# DND Prompt Forge

A free SEO landing application that helps Dungeons & Dragons players and Dungeon Masters turn character ideas into copy-ready AI image prompts.

## Project Structure

```
dnd-prompt-forge/
├── frontend/           # Static HTML/CSS/JS frontend
│   ├── index.html      # Main landing page with SEO
│   ├── css/
│   │   └── style.css   # Complete design system
│   ├── js/             # React components (JSX)
│   │   ├── app.jsx
│   │   ├── generator.jsx
│   │   ├── header.jsx
│   │   ├── footer.jsx
│   │   ├── content-sections.jsx
│   │   ├── prose-pages.jsx
│   │   ├── primitives.jsx
│   │   ├── prompt-engine.jsx
│   │   └── tweaks-panel.jsx
│   ├── sitemap.xml
│   └── robots.txt
├── backend/            # Python FastAPI backend
│   ├── main.py         # API with DeepSeek integration
│   ├── requirements.txt
│   └── README.md
└── docs/               # Scope change documents
```

## Features

- **SEO Optimized**: JSON-LD structured data, meta tags, sitemap, robots.txt
- **Responsive Design**: Mobile-first with dark mode support
- **Prompt Generation**: Deterministic engine with DeepSeek LLM fallback
- **Feedback System**: User feedback with memory rules for self-correction
- **Multiple Output Types**: Portrait, full body, token, NPC, monster, scene
- **Model Targeting**: Midjourney, ChatGPT, Gemini, Leonardo, Stable Diffusion
- **Copy-to-Clipboard**: One-click copy for all prompt outputs
- **No Login Required**: Free to use without account

## Quick Start

### Frontend

The frontend is a static HTML/CSS/JS application that can be served from any web server:

```bash
cd frontend
python3 -m http.server 8080
```

### Backend

```bash
cd backend
pip install -r requirements.txt
export DEEPSEEK_API_KEY="your-api-key"
uvicorn main:app --reload --port 8000
```

## API Endpoints

- `POST /api/generate-prompt` - Generate DND prompts
- `POST /api/feedback` - Submit feedback
- `GET /api/health` - Health check
- `GET /api/memory-rules` - Get active memory rules

## SEO Features

- JSON-LD structured data (SoftwareApplication, FAQPage)
- Canonical URLs on every page
- Unique title and meta descriptions
- Open Graph and Twitter card metadata
- Semantic H1/H2 structure
- Crawlable anchor links
- Mobile-friendly layout
- Sitemap and robots.txt

## License

MIT
