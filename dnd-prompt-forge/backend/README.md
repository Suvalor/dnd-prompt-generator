# DND Prompt Forge - Backend

FastAPI backend with OpenAI-compatible LLM integration for the DND Character Prompt Generator.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://your-openai-compatible-provider.example/v1"
export LLM_MODEL="your-model-name"
```

3. Run the server:
```bash
uvicorn main:app --reload --port 8000
```

## API Endpoints

- `POST /api/generate-prompt` - Generate DND prompts
- `POST /api/feedback` - Submit feedback
- `GET /api/health` - Health check
