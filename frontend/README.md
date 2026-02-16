# Best Voice Agent - Frontend

Modern React + TypeScript web interface for the AI-powered voice customer support agent.

## Overview

The frontend provides a clean, responsive interface for:
- **Customer Chat**: Real-time voice conversations with the AI agent
- **Admin Dashboard**: Monitoring calls, viewing statistics, and configuring settings

Built with React 18, TypeScript, Vite, and React Router for fast development and optimal performance.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment (optional):
```bash
cp .env.example .env
```

Edit `.env` to customize API endpoints:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Run

### Development
```bash
npm run dev
```
Runs on http://localhost:5173

### Production Build
```bash
npm run build
npm run preview
```

### Linting
```bash
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── main.tsx           # Application entry point
│   ├── App.tsx            # Main app component with routing
│   ├── config.ts          # API endpoint configuration
│   ├── types.ts           # TypeScript type definitions
│   ├── pages/             # Page components
│   │   ├── Chat.tsx       # Customer voice chat interface
│   │   ├── AdminLogin.tsx # Admin authentication
│   │   ├── AdminLayout.tsx# Admin panel layout
│   │   ├── AdminCalls.tsx # Call history and details
│   │   ├── AdminStats.tsx # Usage statistics
│   │   └── AdminSettings.tsx # System configuration
│   ├── services/          # API service modules
│   │   ├── api.ts         # HTTP API client
│   │   └── auth.ts        # Authentication service
│   └── assets/            # Static assets
├── public/                # Public static files
├── nginx.conf             # Nginx configuration for production
├── vite.config.ts         # Vite build configuration
└── Dockerfile             # Container configuration
```

## Key Features

### Customer Chat Interface
- **Push-to-Talk Recording**: Hold button to record, release to send
- **Real-Time Transcription**: See your speech transcribed instantly
- **Voice Responses**: Hear AI agent responses with text display
- **Smart Audio Interruption**: Agent stops talking when you start speaking
- **Auto-Cleanup**: Conversations end after 10 minutes of inactivity
- **Natural Acknowledgments**: Agent uses "Hmm...", "Let me think..." sounds
- **Message History**: View full conversation transcript

### Admin Dashboard
- **Call Monitoring**: View all customer calls with details
- **Real-Time Stats**: Track usage, costs, and system metrics
- **Settings Management**: Configure AI model, temperature, and information gathering
- **Secure Authentication**: Token-based admin access
- **Call Details**: Deep dive into individual conversations with transcripts

## Pages

### `/chat`
Customer-facing voice chat interface
- Start/end calls
- Push-to-talk recording
- Live message display
- Audio playback controls

### `/admin`
Protected admin routes (requires login):
- `/admin/calls` - Call history and details
- `/admin/stats` - System-wide statistics
- `/admin/settings` - Configuration management

## WebSocket Integration

The frontend connects to the backend via WebSocket for real-time communication:

### Sending Audio
```typescript
websocket.send(JSON.stringify({
  type: "audio",
  data: base64AudioData
}));
```

### Receiving Messages
```typescript
// Transcription
{ type: "transcription", text: "..." }

// Acknowledgment sound
{ type: "acknowledgment", text: "Hmm...", data: base64Audio }

// AI response text
{ type: "response", text: "..." }

// Response audio
{ type: "audio", data: base64Audio }

// Errors
{ type: "error", message: "..." }
```

## Technologies

- **React 18**: Modern component-based UI
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **React Router**: Client-side routing
- **MediaRecorder API**: Browser audio recording
- **WebSocket API**: Real-time bidirectional communication
- **Nginx**: Production web server and reverse proxy

## API Integration

The frontend communicates with the backend REST API for:
- Starting calls: `POST /api/call/start`
- Admin login: `POST /api/admin/login`
- Fetching calls: `GET /api/admin/calls`
- Statistics: `GET /api/admin/stats`
- Settings: `GET/PATCH /api/admin/settings`

See `src/services/api.ts` for complete API client implementation.

## Styling

Component-specific CSS files provide styling:
- `Chat.css` - Customer chat interface
- `AdminLayout.css` - Admin panel layout
- `AdminCalls.css` - Call history styling
- `AdminStats.css` - Statistics dashboard
- `AdminSettings.css` - Settings page
- `index.css` - Global styles

## Production Deployment

### With Docker
```bash
docker build -t voice-agent-frontend .
docker run -p 80:80 voice-agent-frontend
```

### With Nginx
1. Build the application:
```bash
npm run build
```

2. Serve the `dist/` directory with Nginx using the provided `nginx.conf`

The Nginx configuration includes:
- Static file serving
- API proxying to backend
- WebSocket proxying with extended timeouts
- Health check endpoint

## Browser Requirements

- Modern browser with WebSocket support
- Microphone access permission
- MediaRecorder API support (Chrome, Firefox, Safari, Edge)

## Development Tips

- Hot Module Replacement (HMR) is enabled in dev mode
- TypeScript strict mode is enabled for type safety
- ESLint is configured for code quality
- Use browser DevTools to inspect WebSocket messages
- Check console for activity tracking logs
