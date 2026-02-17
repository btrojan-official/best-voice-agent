# Best Voice Agent

Real-time streaming AI customer support agent with voice conversation capabilities.

## Overview

This application provides an intelligent customer support system that uses voice interaction powered by AI. The system includes:

- **Real-time voice conversations** via WebSocket
- **AI-powered agent** using LlamaIndex and OpenRouter
- **Speech-to-text** transcription
- **Text-to-speech** responses
- **Admin dashboard** for monitoring and configuration
- **Usage tracking** and cost estimation

## Architecture

### Backend (FastAPI + Python)
- FastAPI server with WebSocket support
- LlamaIndex for AI agent orchestration
- OpenRouter API for LLM access
- ElevenLabs for TTS
- Groq Whisper for transcription
- JSON-based data storage
- Comprehensive logging and error handling

### Frontend (React + TypeScript)
- React with TypeScript
- React Router for navigation
- WebSocket for real-time communication
- MediaRecorder API for audio capture
- Admin panel with authentication

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Test API connections (optional but recommended)
python test_apis.py

# Start with Docker Compose
docker-compose up -d

# Access the application
# Frontend: http://localhost
# Backend: http://localhost:8000
```

See [DOCKER.md](DOCKER.md) for detailed Docker instructions.

### Option 2: Manual Setup

#### Prerequisites
- Python 3.9+
- Node.js 18+
- API Keys:
  - OpenRouter (for LLM)
  - ElevenLabs (for TTS)
  - Groq (for transcription)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run server
python main.py
```

Server will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (optional, defaults work for local dev)
cp .env.example .env

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Usage

### Customer Chat
1. Navigate to `http://localhost:5173/chat`
2. Click "Call Customer Support"
3. Hold the "Hold to Speak" button and talk
4. Release to send your message
5. Agent will respond with voice and text

### Admin Panel
1. Navigate to `http://localhost:5173/admin`
2. Login with credentials from backend `.env` (default: admin/admin123)
3. Access:
   - **Calls**: View all calls and their details
   - **Stats**: System-wide usage and cost statistics
   - **Settings**: Configure model and information gathering

## Features

### Real-time Voice Communication
- Low-latency streaming architecture
- Push-to-talk recording
- Automatic transcription
- Natural voice responses

### AI Agent
- Powered by Claude 3.5 Sonnet (via OpenRouter)
- Customizable system prompts
- Configurable information gathering
- Tool calling capabilities
- Conversation summarization

### Precomputed Audio & Smart Interruptions
- **Instant Greeting**: First message is precomputed for zero-latency start
- **Natural Acknowledgments**: Smart use of "Hmm...", "Let me think...", etc. while processing
- **Context-Aware**: Acknowledgments are passed to the AI model for contextual responses
- **Smart Interruptions**: Agent pauses when user starts speaking or new audio arrives
- **Auto-Cleanup**: Conversations automatically end and clear after 3 minutes of inactivity

### Admin Dashboard
- Real-time call monitoring
- Detailed usage statistics
- Cost tracking and estimation
- Model configuration
- Information gathering customization

### Logging & Observability
- Comprehensive logging to file and console
- Error tracking and handling
- Usage metrics collection
- Cost estimation per call

## Configuration

### Backend Environment Variables
```env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_VOICE_ID=your_voice_id
GROQ_API_KEY=your_key_here
TRANSCRIPTION_MODEL=whisper-large-v3
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
PORT=8000
```

### Testing API Connections

Before running the application, test your API keys:

```bash
python test_apis.py
```

This will verify that:
- OpenRouter API is accessible and working
- ElevenLabs TTS API is functional
- Groq Whisper API is responding correctly

### Frontend Environment Variables
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## API Documentation

When the backend is running, visit:
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Project Structure

```
best-voice-agent/
├── backend/
│   ├── agent/              # AI agent implementation
│   ├── models/             # Data models and database
│   ├── routers/            # API endpoints
│   ├── utils/              # Utility functions
│   ├── main.py             # Application entry point
│   ├── auth.py             # Authentication
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/          # React pages
│   │   ├── services/       # API services
│   │   └── types.ts        # TypeScript types
│   └── package.json
└── README.md
```

## Cost Estimation

The system tracks and estimates costs for:
- LLM input/output tokens (via OpenRouter)
- Speech transcription (Groq Whisper)
- Text-to-speech (ElevenLabs)

Costs are displayed per call and in aggregate statistics.

## Development

### Backend
- Add new agent tools in `backend/agent/tools.py`
- Modify prompts in `backend/agent/prompts.py`
- Add API endpoints in `backend/routers/`

### Frontend
- Add pages in `frontend/src/pages/`
- Update types in `frontend/src/types.ts`
- Modify API services in `frontend/src/services/`

## Production Deployment

### Docker (Recommended)

See [DOCKER.md](DOCKER.md) for complete Docker deployment instructions.

```bash
docker-compose up -d --build
```

### Manual Deployment

#### Backend
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Frontend
```bash
npm run build
# Serve the dist/ folder with your preferred static file server
```

## Troubleshooting

### WebSocket Connection Issues
- Ensure backend is running on port 8000
- Check CORS settings in `backend/main.py`
- Verify WebSocket URL in frontend config

### Audio Recording Issues
- Grant microphone permissions in browser
- Use HTTPS in production (required for MediaRecorder)

### API Key Errors
- Verify all API keys are correctly set in `.env`
- Check API key permissions and quotas

## License

MIT

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing style
- TypeScript types are properly defined
- Error handling is comprehensive
- Logging is appropriate
