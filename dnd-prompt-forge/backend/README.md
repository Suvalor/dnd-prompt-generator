# DND Prompt Forge - Backend

FastAPI backend with DeepSeek LLM integration for the DND Character Prompt Generator.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export DEEPSEEK_API_KEY="your-api-key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"  # optional
export DEEPSEEK_MODEL="deepseek-chat"  # optional
```

3. Run the server:
```bash
uvicorn main:app --reload --port 8000
```

## API Endpoints

- `POST /api/generate-prompt` - Generate DND prompts
- `POST /api/feedback` - Submit feedback
- `GET /api/health` - Health check
