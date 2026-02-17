# Best Voice Agent - Backend

Real-time streaming AI customer support agent with FastAPI and LlamaIndex.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

3. Edit `.env` with your API keys:
   - OPENROUTER_API_KEY: Get from https://openrouter.ai/ (required for OpenRouter models)
   - GROQ_API_KEY: Get from https://groq.com/ (required for Groq models)
   - DEFAULT_MODEL: Model to use (default: openai/gpt-oss-120b)
     - Groq models: moonshotai/kimi-k2-instruct-0905, llama-3.3-70b-versatile, llama-3.1-70b-versatile
     - OpenRouter models: anthropic/claude-3.5-sonnet, google/gemini-pro-1.5, etc.
   - ELEVENLABS_API_KEY: Get from https://elevenlabs.io/
   - TRANSCRIPTION_MODEL: Whisper model for transcription (default: whisper-large-v3)
   - ADMIN_USERNAME and ADMIN_PASSWORD: For admin panel access


## Run

### Development
```bash
python main.py
```

### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── auth.py                 # Authentication service
├── agent/                  # AI agent implementation
│   ├── agent.py           # CustomerSupportAgent class
│   ├── tools.py           # Agent tools
│   └── prompts.py         # System prompts
├── models/                 # Data models and database
│   ├── schemas.py         # Pydantic models
│   └── database.py        # JSON-based database
├── routers/               # API routes
│   ├── chat.py           # WebSocket chat endpoints
│   └── admin.py          # Admin panel endpoints
└── utils/                 # Utility functions
    ├── query_llm.py      # LLM utilities
    ├── transcription.py  # Speech-to-text
    └── tts.py            # Text-to-speech
```

## API Endpoints

### Chat
- `POST /api/call/start` - Start new call
- `WS /api/ws/call/{call_id}` - WebSocket for real-time conversation
- `GET /api/call/{call_id}` - Get call details

### Admin
- `POST /api/admin/login` - Admin login
- `GET /api/admin/calls` - Get all calls
- `GET /api/admin/calls/{call_id}` - Get call details
- `GET /api/admin/stats` - Get system statistics
- `GET /api/admin/settings` - Get settings
- `PATCH /api/admin/settings` - Update settings
- `POST /api/admin/settings/information` - Add information to gather
- `DELETE /api/admin/settings/information/{info_id}` - Remove information

## WebSocket Message Format

### Client → Server
```json
{
  "type": "audio",
  "data": "<base64_encoded_audio>"
}
```

### Server → Client
```json
{
  "type": "transcription",
  "text": "User's transcribed speech"
}
```

```json
{
  "type": "response",
  "text": "Agent's response"
}
```

```json
{
  "type": "audio",
  "data": "<base64_encoded_audio>"
}
```

## Logging

Logs are stored in `logs/app.log` and also printed to console.

## Data Storage

Data is stored in JSON files in the `data/` directory:
- `calls.json` - Call records
- `settings.json` - System settings
- `stats.json` - Usage statistics
