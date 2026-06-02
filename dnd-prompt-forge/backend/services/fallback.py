"""
DND Prompt Forge - Fallback 服务
复用现有 build_fallback_prompt() 逻辑，提供确定性生成
"""

from typing import Dict

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


def build_fallback_prompt(data: dict) -> Dict[str, str]:
    """
    构建确定性 fallback 提示词，当 LLM 不可用时使用。

    Args:
        data: 包含生成参数的字典

    Returns:
        包含 main_prompt, short_prompt, negative_prompt, style_notes, usage_tip 的字典
    """
    output_type = data.get("output_type", "portrait")
    race = data.get("race", "").strip()
    class_role = data.get("class_role", "").strip()
    desc = data.get("description", "").strip()
    style = data.get("style", "painterly")
    mood = data.get("mood", "brooding")
    target_model = data.get("target_model", "midjourney")

    # 构建主体描述
    subject_parts = []
    if data.get("gender"):
        subject_parts.append(data["gender"])
    if data.get("age"):
        subject_parts.append(data["age"])
    if race:
        subject_parts.append(race)
    if class_role:
        subject_parts.append(class_role)

    subject = " ".join(subject_parts).strip()
    if not subject:
        subject = "a fantasy character" if output_type != "scene" else "a fantasy location"
    elif output_type != "scene":
        subject = f"a {subject}"

    # 构建描述性修饰
    descr = []
    if desc:
        descr.append(desc)
    if data.get("alignment"):
        descr.append(f"{data['alignment']} alignment")
    if data.get("armor"):
        descr.append(f"wearing {data['armor']}")
    if data.get("weapon"):
        descr.append(f"wielding {data['weapon']}")
    if data.get("magic"):
        descr.append(f"{data['magic']} magic effects")

    # 获取风格和情绪描述
    style_desc = STYLE_DESCRIPTIONS.get(style, STYLE_DESCRIPTIONS["painterly"])
    mood_desc = MOOD_DESCRIPTIONS.get(mood, MOOD_DESCRIPTIONS["brooding"])

    # 构建主提示词
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
    if data.get("palette"):
        main_parts.append(f"{data['palette']} color palette")
    main_parts.append(ANGLES.get(output_type, ""))
    main_parts.append("intricate detail, professional fantasy art, ArtStation quality")

    main = ", ".join(filter(None, main_parts))

    # 模型特定后缀
    if target_model == "midjourney":
        main += f" --ar {AR.get(output_type, '1:1')} --style raw --v 6.1"
    elif target_model == "sd":
        main = "(masterpiece, best quality, highly detailed:1.2) " + main

    # 短提示词
    short_parts = [subject.replace("a ", "") if output_type != "scene" else subject]
    short_parts.append(output_type if output_type != "token" else "top-down token")
    if desc:
        short_parts.append(desc.split(",")[0])
    short_parts.append(style)
    short = ", ".join(filter(None, short_parts))

    # 负面提示词
    neg_parts = [NEGATIVE_BASE, NEGATIVE_BY_TYPE.get(output_type, "")]
    if style == "realism":
        neg_parts.append("painting")
        neg_parts.append("illustration")
    negative = ", ".join(filter(None, neg_parts))

    # 风格提示
    notes_map = {
        "portrait": "Portraits read best with a clear single light source. Keep the background simple so the face carries the image.",
        "fullbody": "Full-body shots need a readable silhouette. Describe the pose as a verb and keep one hero prop dominant.",
        "token": "Tokens must stay centered and high-contrast against the edge. Request a plain or transparent background.",
        "npc": "NPCs land when one memorable trait leads. Name the role so the model dresses them in-world.",
        "monster": "Monsters benefit from a scale cue. Put a small familiar object or low horizon line in frame.",
        "scene": "Scenes want depth: name foreground, midground, and background elements, plus time of day.",
    }
    style_notes = notes_map.get(output_type, "")

    # 使用提示
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