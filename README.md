# Best Voice Agent 🎙️

> Enterprise-grade AI voice assistant for real-time customer support with observability and analytics.

---

## ✨ Highlights

- **⚡ Blazing Fast** — Groq-powered inference (70B models, sub-second responses) with real-time streaming
- **🧠 Smart Memory** — Long-short term memory via conversation summarization keeps context without blowing up token usage
- **🎛️ Fully Customizable** — Admin dashboard to tweak models, temperature, prompts, and data collection fields — no code changes needed
- **📊 Full Observability** — Per-call cost tracking, transcripts, AI-generated summaries, and performance metrics
- **🌍 Multi-Language** — Automatically adapts to the user's language via LLM
- **🐳 One-Command Deploy** — Full stack up with `docker-compose up`

---

## 🚀 Quick Start (Docker)

**Prerequisites:** Docker & Docker Compose, plus API keys for [OpenRouter](https://openrouter.ai/), [ElevenLabs](https://elevenlabs.io/), and [Groq](https://groq.com/).

```bash
git clone https://github.com/yourusername/best-voice-agent.git
cd best-voice-agent

cp .env.example .env
# Fill in your API keys:
# OPENROUTER_API_KEY=...
# ELEVENLABS_API_KEY=...
# GROQ_API_KEY=...

docker-compose up -d
```

| Service | URL |
|---|---|
| Customer Chat | http://localhost/chat |
| Admin Panel | http://localhost/admin |
| API Docs | http://localhost:8000/docs |

Default admin credentials: `admin` / `admin123` — **change in production.**

```bash
docker-compose down        # stop
docker-compose down -v     # stop + delete data
```

---

## 📁 Project Structure

```
best-voice-agent/
├── backend/                  # FastAPI async backend
│   ├── agent/                # Core AI agent (agent.py, prompts.py, tools.py)
│   ├── models/               # Pydantic schemas + JSON DB
│   ├── routers/              # REST + WebSocket endpoints (admin.py, chat.py)
│   ├── utils/                # TTS, transcription, audio caching
│   ├── data/                 # Persisted calls, settings, stats (Docker volume)
│   └── main.py / auth.py     # Entry point + JWT auth
│
├── frontend/                 # React 18 + TypeScript + Vite
│   └── src/
│       ├── pages/            # Chat, AdminCalls, AdminStats, AdminSettings
│       └── services/         # API + auth clients
│
├── docker-compose.yml
└── .env.example
```

---

## ⚙️ Key Configuration

```bash
# .env
OPENROUTER_API_KEY=...
ELEVENLABS_API_KEY=...
GROQ_API_KEY=...

DEFAULT_MODEL=openai/gpt-oss-120b   # or llama-3.3-70b-versatile, claude-4.5-sonnet, etc.
TRANSCRIPTION_MODEL=whisper-large-v3
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

Model selection, temperature, pricing, and data collection fields can all be changed live from the admin dashboard.

---

## 🏗️ Tech Stack

**Backend:** FastAPI · LlamaIndex · Groq · OpenRouter · ElevenLabs · WebSocket  
**Frontend:** React 18 · TypeScript · Vite · MediaRecorder API  
**Infra:** Docker Compose · Nginx

---

## 📚 API Docs

Available at `http://localhost:8000/docs` (Swagger) when the backend is running.
