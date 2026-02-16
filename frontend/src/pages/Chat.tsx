import { useState, useRef, useEffect } from "react";
import { API_ENDPOINTS } from "../config";
import { apiService } from "../services/api";
import type { WebSocketMessage } from "../types";
import "./Chat.css";

export default function Chat() {
  const [isCallActive, setIsCallActive] = useState(false);
  const [, setCallId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Array<{ role: string; text: string; timestamp: string }>>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const inactivityTimerRef = useRef<number | null>(null);
  const lastActivityTimeRef = useRef<number>(Date.now());

  const startCall = async () => {
    try {
      setError(null);
      const result = await apiService.startCall();
      setCallId(result.call_id);
      lastActivityTimeRef.current = Date.now();
      startInactivityTimer();
      
      const ws = new WebSocket(API_ENDPOINTS.WS_CALL(result.call_id));
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log("WebSocket connected");
        setIsCallActive(true);
      };
      
      ws.onmessage = (event) => {
        const data: WebSocketMessage = JSON.parse(event.data);
        lastActivityTimeRef.current = Date.now();
        
        if (data.type === "transcription" && data.text) {
          setMessages(prev => [...prev, {
            role: "user",
            text: data.text as string,
            timestamp: new Date().toISOString()
          }]);
        } else if (data.type === "acknowledgment" && data.data) {
          // Play acknowledgment audio (interrupt any current audio)
          stopCurrentAudio();
          playAudioResponse(data.data);
        } else if (data.type === "response" && data.text) {
          setMessages(prev => [...prev, {
            role: "assistant",
            text: data.text as string,
            timestamp: new Date().toISOString()
          }]);
        } else if (data.type === "audio" && data.data) {
          // Interrupt any currently playing audio
          stopCurrentAudio();
          playAudioResponse(data.data);
        } else if (data.type === "error" && data.message) {
          setError(data.message);
        }
      };
      
      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setError("Connection error occurred");
      };
      
      ws.onclose = () => {
        console.log("WebSocket closed");
        setIsCallActive(false);
        stopInactivityTimer();
      };
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start call");
      console.error("Error starting call:", err);
    }
  };

  const endCall = () => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: "end_call" }));
      wsRef.current.close();
    }
    
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
    }
    
    stopCurrentAudio();
    stopInactivityTimer();
    clearMessages();
    
    setIsCallActive(false);
    setIsRecording(false);
  };

  const stopCurrentAudio = () => {
    // Stop and cleanup any currently playing audio
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      currentAudioRef.current = null;
    }
  };

  const startInactivityTimer = () => {
    stopInactivityTimer();
    
    const checkInactivity = () => {
      const timeSinceActivity = Date.now() - lastActivityTimeRef.current;
      const INACTIVITY_TIMEOUT = 10 * 60 * 1000; // 10 minutes
      
      const minutesSinceActivity = Math.floor(timeSinceActivity / 60000);
      console.log(`Activity check: ${minutesSinceActivity} minutes since last activity`);
      
      if (timeSinceActivity >= INACTIVITY_TIMEOUT) {
        console.log("Ending call due to inactivity (10 minutes)");
        endCall();
      }
    };
    
    // Check every 30 seconds
    inactivityTimerRef.current = setInterval(checkInactivity, 30000);
  };

  const stopInactivityTimer = () => {
    if (inactivityTimerRef.current) {
      clearInterval(inactivityTimerRef.current);
      inactivityTimerRef.current = null;
    }
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const startRecording = async () => {
    try {
      // Stop any currently playing audio when user starts speaking
      stopCurrentAudio();
      lastActivityTimeRef.current = Date.now();
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        await sendAudioToServer(audioBlob);
        audioChunksRef.current = [];
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      
    } catch (err) {
      setError("Failed to access microphone");
      console.error("Error starting recording:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (mediaRecorderRef.current.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      }
    }
  };

  const sendAudioToServer = async (audioBlob: Blob) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }
    
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64data = reader.result as string;
      const base64Audio = base64data.split(",")[1];
      
      wsRef.current?.send(JSON.stringify({
        type: "audio",
        data: base64Audio
      }));
    };
    reader.readAsDataURL(audioBlob);
  };

  const playAudioResponse = (base64Audio: string) => {
    try {
      const audioData = atob(base64Audio);
      const arrayBuffer = new ArrayBuffer(audioData.length);
      const view = new Uint8Array(arrayBuffer);
      
      for (let i = 0; i < audioData.length; i++) {
        view[i] = audioData.charCodeAt(i);
      }
      
      const blob = new Blob([arrayBuffer], { type: "audio/mpeg" });
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      
      // Store reference to current audio
      currentAudioRef.current = audio;
      
      audio.onended = () => {
        // Clear reference when audio finishes
        if (currentAudioRef.current === audio) {
          currentAudioRef.current = null;
        }
      };
      
      audio.play().catch(err => {
        console.error("Error playing audio:", err);
      });
      
    } catch (err) {
      console.error("Error processing audio response:", err);
    }
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
      stopCurrentAudio();
      stopInactivityTimer();
    };
  }, []);

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Customer Support</h1>
      </div>

      <div className="chat-content">
        {!isCallActive ? (
          <div className="call-start">
            <button className="btn btn-primary" onClick={startCall}>
              Call Customer Support
            </button>
            {error && <div className="error-message">{error}</div>}
          </div>
        ) : (
          <div className="call-active">
            <div className="call-status">
              <span className="status-indicator active"></span>
              <span>Call Active</span>
            </div>

            <div className="messages-container">
              {messages.map((msg, idx) => (
                <div key={idx} className={`message ${msg.role}`}>
                  <div className="message-header">
                    <span className="role">{msg.role === "user" ? "You" : "Agent"}</span>
                    <span className="timestamp">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="message-content">{msg.text}</div>
                </div>
              ))}
            </div>

            <div className="controls">
              <button
                className={`btn ${isRecording ? "btn-danger" : "btn-secondary"}`}
                onMouseDown={startRecording}
                onMouseUp={stopRecording}
                onTouchStart={startRecording}
                onTouchEnd={stopRecording}
              >
                {isRecording ? "Recording..." : "Hold to Speak"}
              </button>
              
              <button className="btn btn-danger" onClick={endCall}>
                End Call
              </button>
            </div>

            {error && <div className="error-message">{error}</div>}
          </div>
        )}
      </div>
    </div>
  );
}
