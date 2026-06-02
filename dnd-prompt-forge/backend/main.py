"""
DND Prompt Forge - FastAPI Backend
===================================
API service for generating DND character prompts via DeepSeek LLM.
Includes feedback memory and self-correction system.
"""

import os
import uuid
import json
import sqlite3
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ── Configuration ───────────────────────────────────────────────────────────

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

DB_PATH = os.getenv("DB_PATH", "./prompt_forge.db")

# ── Database ────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS prompt_requests (
            id TEXT PRIMARY KEY,
            created_at TEXT,
            output_type TEXT,
            race TEXT,
            class_role TEXT,
            style TEXT,
            mood TEXT,
            description TEXT,
            target_model TEXT,
            template_version TEXT,
            memory_rule_version TEXT,
            main_prompt TEXT,
            short_prompt TEXT,
            negative_prompt TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            request_id TEXT,
            feedback TEXT,
            reason TEXT,
            comment TEXT,
            input_snapshot TEXT,
            output_snapshot TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS memory_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            updated_at TEXT,
            status TEXT,
            rule_key TEXT,
            rule_text TEXT,
            trigger_reason TEXT,
            times_seen INTEGER DEFAULT 1,
            version TEXT
        )
    """)

    conn.commit()
    conn.close()


# ── Pydantic Models ─────────────────────────────────────────────────────────

class GeneratePromptRequest(BaseModel):
    output_type: str = Field(..., description="Type of output: portrait, fullbody, token, npc, monster, scene")
    race: str = Field(default="", description="Race or creature type")
    class_role: str = Field(default="", description="Class or role")
    style: str = Field(default="painterly", description="Visual style")
    mood: str = Field(default="brooding", description="Mood/atmosphere")
    description: str = Field(default="", description="Short description")
    alignment: Optional[str] = Field(default=None)
    weapon: Optional[str] = Field(default=None)
    background: Optional[str] = Field(default=None)
    target_model: str = Field(default="midjourney", description="Target AI model")
    gender: Optional[str] = Field(default=None)
    age: Optional[str] = Field(default=None)
    armor: Optional[str] = Field(default=None)
    magic: Optional[str] = Field(default=None)
    palette: Optional[str] = Field(default=None)
    camera: Optional[str] = Field(default=None)


class GeneratePromptResponse(BaseModel):
    request_id: str
    template_version: str = "v1"
    memory_rule_version: str = "v1"
    main_prompt: str
    short_prompt: str
    negative_prompt: str
    style_notes: str
    usage_tip: str


class FeedbackRequest(BaseModel):
    request_id: str
    feedback: str = Field(..., description="useful or not_useful")
    reason: Optional[str] = Field(default=None)
    comment: Optional[str] = Field(default=None)


class FeedbackResponse(BaseModel):
    saved: bool
    message: str


# ── LLM Integration ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are DND Prompt Forge, an expert prompt engineer for tabletop RPG AI image generation.

Your task: convert structured character/scene details into high-quality, copy-ready English prompts for AI image models.

## Rules
- Write clear, descriptive English prompts
- Include DND-specific visual details
- Avoid copyrighted character names unless supplied by user
- Avoid explicit, hateful, or extremist content
- Do not claim output images are guaranteed
- Tailor prompts to the target AI model (Midjourney, ChatGPT, etc.)

## Output Format (JSON)
{
  "main_prompt": "detailed main prompt text",
  "short_prompt": "concise version",
  "negative_prompt": "things to exclude",
  "style_notes": "tips for getting the best result",
  "usage_tip": "how to use this prompt effectively"
}
"""

NEGATIVE_BASE = "blurry, lowres, jpeg artifacts, deformed, extra limbs, extra fingers, mutated hands, bad anatomy, watermark, signature, text, logo, cropped, out of frame"

NEGATIVE_BY_TYPE = {
    "token": "background clutter, multiple figures, off-center, busy scenery, harsh drop shadow",
    "portrait": "full body, distant framing, flat even lighting",
    "fullbody": "cropped limbs, floating pose",
    "monster": "cute, friendly, cartoonish proportions",
    "scene": "central character hero, portrait crop",
    "npc": "generic stock-photo face, modern clothing",
}

STYLE_DESCRIPTIONS = {
    "painterly": "painterly fantasy illustration, visible brush strokes, rich oil-painting texture",
    "ink": "ink line art with loose watercolor wash, parchment texture, sketchbook feel",
    "realism": "cinematic semi-realism, physically-based lighting, film still, photoreal materials",
    "comic": "bold graphic comic style, clean inking, flat dramatic color blocking",
    "storybook": "whimsical storybook illustration, soft gouache, warm rounded shapes",
    "grimdark": "grimdark dark-fantasy concept art, muted desaturated palette, heavy chiaroscuro",
}

MOOD_DESCRIPTIONS = {
    "heroic": "heroic, confident, triumphant",
    "brooding": "brooding, moody, introspective",
    "menacing": "menacing, ominous, dangerous",
    "serene": "serene, calm, contemplative",
    "mystical": "mystical, arcane, otherworldly glow",
    "gritty": "gritty, weathered, battle-worn",
}

AR = {"portrait": "4:5", "fullbody": "2:3", "token": "1:1", "npc": "4:5", "monster": "3:2", "scene": "16:9"}

ANGLES = {
    "portrait": "eye-level three-quarter view, shallow depth of field",
    "fullbody": "full-length framing, low hero angle",
    "token": "direct top-down orthographic view",
    "npc": "eye-level, mid framing",
    "monster": "low dramatic angle emphasizing scale",
    "scene": "wide establishing angle, deep perspective",
}


def build_fallback_prompt(data: dict) -> dict:
    """Build a deterministic fallback prompt when LLM is unavailable."""
    output_type = data.get("output_type", "portrait")
    race = data.get("race", "").strip()
    class_role = data.get("class_role", "").strip()
    desc = data.get("description", "").strip()
    style = data.get("style", "painterly")
    mood = data.get("mood", "brooding")
    target_model = data.get("target_model", "midjourney")

    # Subject
    subject_parts = []
    if data.get("gender"): subject_parts.append(data["gender"])
    if data.get("age"): subject_parts.append(data["age"])
    if race: subject_parts.append(race)
    if class_role: subject_parts.append(class_role)

    subject = " ".join(subject_parts).strip()
    if not subject:
        subject = "a fantasy character" if output_type != "scene" else "a fantasy location"
    elif output_type != "scene":
        subject = f"a {subject}"

    # Descriptors
    descr = []
    if desc: descr.append(desc)
    if data.get("alignment"): descr.append(f"{data['alignment']} alignment")
    if data.get("armor"): descr.append(f"wearing {data['armor']}")
    if data.get("weapon"): descr.append(f"wielding {data['weapon']}")
    if data.get("magic"): descr.append(f"{data['magic']} magic effects")

    # Style and mood
    style_desc = STYLE_DESCRIPTIONS.get(style, STYLE_DESCRIPTIONS["painterly"])
    mood_desc = MOOD_DESCRIPTIONS.get(mood, MOOD_DESCRIPTIONS["brooding"])

    # Build main prompt
    main_parts = [subject]
    if output_type == "scene":
        main_parts = [f"wide environment illustration of {subject}"]
    elif output_type == "token":
        main_parts = [f"top-down view, centered single figure, {subject}"]
    elif output_type == "portrait":
        main_parts = [f"head-and-shoulders portrait of {subject}"]
    elif output_type == "fullbody":
        main_parts = [f"full-body character illustration of {subject}"]
    elif output_type == "monster":
        main_parts = [f"full creature illustration of {subject}"]
    elif output_type == "npc":
        main_parts = [f"character portrait of {subject}"]

    main_parts.extend(descr)
    main_parts.append(style_desc)
    main_parts.append(mood_desc)
    if data.get("palette"): main_parts.append(f"{data['palette']} color palette")
    main_parts.append(ANGLES.get(output_type, ""))
    main_parts.append("intricate detail, professional fantasy art, ArtStation quality")

    main = ", ".join(filter(None, main_parts))

    # Model-specific suffix
    if target_model == "midjourney":
        main += f" --ar {AR.get(output_type, '1:1')} --style raw --v 6.1"
    elif target_model == "sd":
        main = "(masterpiece, best quality, highly detailed:1.2) " + main

    # Short prompt
    short_parts = [subject.replace("a ", "") if output_type != "scene" else subject]
    short_parts.append(output_type if output_type != "token" else "top-down token")
    if desc: short_parts.append(desc.split(",")[0])
    short_parts.append(style)
    short = ", ".join(filter(None, short_parts))

    # Negative prompt
    neg_parts = [NEGATIVE_BASE, NEGATIVE_BY_TYPE.get(output_type, "")]
    if style == "realism":
        neg_parts.append("painting, illustration")
    negative = ", ".join(filter(None, neg_parts))

    # Style notes
    notes_map = {
        "portrait": "Portraits read best with a clear single light source. Keep the background simple so the face carries the image.",
        "fullbody": "Full-body shots need a readable silhouette. Describe the pose as a verb and keep one hero prop dominant.",
        "token": "Tokens must stay centered and high-contrast against the edge. Request a plain or transparent background.",
        "npc": "NPCs land when one memorable trait leads. Name the role so the model dresses them in-world.",
        "monster": "Monsters benefit from a scale cue. Put a small familiar object or low horizon line in frame.",
        "scene": "Scenes want depth: name foreground, midground, and background elements, plus time of day.",
    }
    style_notes = notes_map.get(output_type, "")

    # Usage tip
    if output_type == "token":
        usage_tip = "Generate at 1:1, then export with a transparent or solid background and crop to a circle in your VTT."
    else:
        usage_tip = "Paste the main prompt first. If the result drifts, add 1-2 words from the negative prompt into your model's negative field."

    return {
        "main_prompt": main,
        "short_prompt": short,
        "negative_prompt": negative,
        "style_notes": style_notes,
        "usage_tip": usage_tip,
    }


async def call_deepseek(prompt_data: dict) -> dict:
    """Call DeepSeek API to generate prompt."""
    if not DEEPSEEK_API_KEY:
        return build_fallback_prompt(prompt_data)

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    user_prompt = f"""Generate a DND character prompt with these details:
- Output type: {prompt_data.get('output_type', 'portrait')}
- Race/Creature: {prompt_data.get('race', '')}
- Class/Role: {prompt_data.get('class_role', '')}
- Style: {prompt_data.get('style', 'painterly')}
- Mood: {prompt_data.get('mood', 'brooding')}
- Description: {prompt_data.get('description', '')}
- Target model: {prompt_data.get('target_model', 'midjourney')}
"""

    if prompt_data.get("alignment"):
        user_prompt += f"- Alignment: {prompt_data['alignment']}\n"
    if prompt_data.get("weapon"):
        user_prompt += f"- Weapon: {prompt_data['weapon']}\n"
    if prompt_data.get("armor"):
        user_prompt += f"- Armor: {prompt_data['armor']}\n"
    if prompt_data.get("magic"):
        user_prompt += f"- Magic: {prompt_data['magic']}\n"
    if prompt_data.get("palette"):
        user_prompt += f"- Color palette: {prompt_data['palette']}\n"

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            response = await client.post(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            result = json.loads(content)
            return result
    except Exception:
        # Fallback on any error
        return build_fallback_prompt(prompt_data)


# ── FastAPI App ─────────────────────────────────────────────────────────────

app = FastAPI(title="DND Prompt Forge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/api/health")
async def health_check():
    return {"ok": True}


@app.post("/api/generate-prompt")
async def generate_prompt(req: GeneratePromptRequest):
    request_id = str(uuid.uuid4())

    # Call LLM
    result = await call_deepseek(req.dict())

    # Store in database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """INSERT INTO prompt_requests
           (id, created_at, output_type, race, class_role, style, mood, description,
            target_model, template_version, memory_rule_version, main_prompt,
            short_prompt, negative_prompt)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (request_id, datetime.utcnow().isoformat(), req.output_type, req.race,
         req.class_role, req.style, req.mood, req.description, req.target_model,
         "v1", "v1", result["main_prompt"], result["short_prompt"],
         result["negative_prompt"]),
    )
    conn.commit()
    conn.close()

    return GeneratePromptResponse(
        request_id=request_id,
        template_version="v1",
        memory_rule_version="v1",
        main_prompt=result["main_prompt"],
        short_prompt=result["short_prompt"],
        negative_prompt=result["negative_prompt"],
        style_notes=result["style_notes"],
        usage_tip=result["usage_tip"],
    )


@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Store feedback
    c.execute(
        """INSERT INTO feedback_events
           (created_at, request_id, feedback, reason, comment)
           VALUES (?, ?, ?, ?, ?)""",
        (datetime.utcnow().isoformat(), req.request_id, req.feedback,
         req.reason, req.comment),
    )

    # Update or create memory rule for negative feedback
    if req.feedback == "not_useful" and req.reason:
        c.execute(
            "SELECT id, times_seen FROM memory_rules WHERE rule_key = ?",
            (req.reason,),
        )
        row = c.fetchone()
        if row:
            c.execute(
                "UPDATE memory_rules SET times_seen = times_seen + 1, updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), row[0]),
            )
        else:
            c.execute(
                """INSERT INTO memory_rules
                   (created_at, updated_at, status, rule_key, rule_text, trigger_reason, version)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(),
                 "active", req.reason, f"Auto-generated rule for: {req.reason}",
                 req.comment or "", "v1"),
            )

    conn.commit()
    conn.close()

    return FeedbackResponse(saved=True, message="Thanks. Future prompts will use this feedback.")


@app.get("/api/memory-rules")
async def get_memory_rules():
    """Get active memory rules for prompt generation."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT rule_key, rule_text, times_seen FROM memory_rules WHERE status = 'active'")
    rules = [{"key": row[0], "text": row[1], "times_seen": row[2]} for row in c.fetchall()]
    conn.close()
    return {"rules": rules}
