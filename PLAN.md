# 目的

Build a 1-2 day MVP experiment for a free SEO landing application: DND Character Prompt Generator.

The experiment should validate whether a lightweight prompt-generation tool can target long-tail Google SEO traffic and later support Google AdSense monetization.

# 假设

- Users search for DND character, token, NPC, monster, and scene prompt help because direct AI image tools require better English prompts.
- A prompt-only product can avoid image-generation cost while still solving the first user pain.
- Long-tail pages such as Tiefling Warlock Prompt Generator and DND Token Prompt Generator can avoid head-term competition.
- OpenAI-compatible LLM APIs are sufficient for generating structured, copy-ready English prompts.
- Lightweight negative-feedback memory can improve future prompt generations without model fine-tuning.

# 步骤

1. Review product requirements in `docs/scope-change/20260601-dnd-prompt-generator-prd.md`.
2. Review development plan in `docs/scope-change/20260601-dnd-prompt-generator-dev-doc.md`.
3. Review SEO plan in `docs/scope-change/20260601-dnd-prompt-generator-seo-plan.md`.
4. Implement landing application only after the PRD is confirmed.
5. Build Python backend with OpenAI-compatible LLM API integration.
6. Add SQLite or JSONL feedback memory.
7. Add required pages: About Us, Privacy Policy, Terms, Contact.
8. Add technical SEO: title, description, canonical, OG/Twitter, FAQ JSON-LD, robots, sitemap.
9. Test generation, feedback capture, and correction-rule injection.
10. Write final findings in `RESULT.md`.

# 预期产出

- A working landing app MVP.
- A prompt generator usable without login.
- A simple Python backend.
- Feedback memory for negative user responses.
- SEO-ready public pages.
- Documented launch checklist and experiment result.

# 风险与回退

- Risk: DND prompt-only tool may be weaker than image-generation competitors.
  - Fallback: Position as copy-ready prompts for any AI image platform.
- Risk: OpenAI-compatible LLM JSON output may be unstable across providers.
  - Fallback: Add output validation and deterministic template fallback.
- Risk: SEO competition may be higher than expected.
  - Fallback: Expand into narrower race/class/token/scene long-tail pages.
- Risk: AdSense approval may require more content.
  - Fallback: Add guides, examples, FAQ, and policy pages before applying.
