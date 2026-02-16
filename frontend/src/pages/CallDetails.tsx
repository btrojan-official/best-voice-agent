import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { apiService } from "../services/api";
import type { Call } from "../types";
import "./CallDetails.css";

export default function CallDetails() {
  const { callId } = useParams<{ callId: string }>();
  const [call, setCall] = useState<Call | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (callId) {
      loadCall();
    }
  }, [callId]);

  const loadCall = async () => {
    if (!callId) return;
    
    try {
      const data = await apiService.getCallDetails(callId);
      setCall(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load call");
      console.error("Error loading call:", err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString();
  };

  if (loading) {
    return <div className="admin-page">Loading call details...</div>;
  }

  if (error || !call) {
    return (
      <div className="admin-page">
        <div className="error-message">{error || "Call not found"}</div>
        <Link to="/admin/calls" className="btn">Back to Calls</Link>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="page-header">
        <div>
          <Link to="/admin/calls" className="back-link">← Back to Calls</Link>
          <h1>{call.title}</h1>
        </div>
      </div>

      <div className="call-details-grid">
        <div className="stats-section">
          <h2>Statistics</h2>
          
          <div className="stats-card">
            <h3>Usage</h3>
            <div className="stat-row">
              <span>Input Tokens:</span>
              <span>{call.usage_stats.input_tokens}</span>
            </div>
            <div className="stat-row">
              <span>Output Tokens:</span>
              <span>{call.usage_stats.output_tokens}</span>
            </div>
            <div className="stat-row">
              <span>Input Characters:</span>
              <span>{call.usage_stats.input_characters}</span>
            </div>
            <div className="stat-row">
              <span>Output Characters:</span>
              <span>{call.usage_stats.output_characters}</span>
            </div>
            <div className="stat-row">
              <span>Transcription:</span>
              <span>{call.usage_stats.transcription_seconds.toFixed(2)}s</span>
            </div>
            <div className="stat-row">
              <span>TTS Characters:</span>
              <span>{call.usage_stats.tts_characters}</span>
            </div>
            <div className="stat-row">
              <span>LLM Calls:</span>
              <span>{call.usage_stats.llm_calls}</span>
            </div>
          </div>

          <div className="stats-card">
            <h3>Estimated Costs</h3>
            <div className="stat-row">
              <span>LLM Input:</span>
              <span>${call.cost_stats.llm_input_cost.toFixed(4)}</span>
            </div>
            <div className="stat-row">
              <span>LLM Output:</span>
              <span>${call.cost_stats.llm_output_cost.toFixed(4)}</span>
            </div>
            <div className="stat-row">
              <span>Transcription:</span>
              <span>${call.cost_stats.transcription_cost.toFixed(4)}</span>
            </div>
            <div className="stat-row">
              <span>TTS:</span>
              <span>${call.cost_stats.tts_cost.toFixed(4)}</span>
            </div>
            <div className="stat-row total">
              <span>Total:</span>
              <span>${call.cost_stats.total_cost.toFixed(4)}</span>
            </div>
          </div>

          <div className="stats-card">
            <h3>Timing</h3>
            <div className="stat-row">
              <span>Started:</span>
              <span>{formatDate(call.start_time)}</span>
            </div>
            {call.end_time && (
              <div className="stat-row">
                <span>Ended:</span>
                <span>{formatDate(call.end_time)}</span>
              </div>
            )}
            <div className="stat-row">
              <span>Status:</span>
              <span className={`status-badge status-${call.status}`}>
                {call.status}
              </span>
            </div>
          </div>
        </div>

        <div className="content-section">
          {call.summary && (
            <div className="summary-section">
              <h2>Summary</h2>
              <div className="summary-content">
                {call.summary}
              </div>
            </div>
          )}

          {call.tool_calls.length > 0 && (
            <div className="tools-section">
              <h2>Tool Calls</h2>
              <div className="tools-list">
                {call.tool_calls.map((tool, idx) => (
                  <div key={idx} className="tool-call">
                    <div className="tool-header">
                      <span className="tool-name">{tool.tool_name}</span>
                      <span className="tool-time">{formatTime(tool.timestamp)}</span>
                    </div>
                    <div className="tool-args">
                      <pre>{JSON.stringify(tool.arguments, null, 2)}</pre>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="transcript-section">
            <h2>Transcript</h2>
            <div className="messages-list">
              {call.messages.map((msg, idx) => (
                <div key={idx} className={`transcript-message ${msg.role}`}>
                  <div className="message-header">
                    <span className="role-label">
                      {msg.role === "user" ? "Customer" : "Agent"}
                    </span>
                    <span className="message-time">{formatTime(msg.timestamp)}</span>
                  </div>
                  <div className="message-text">{msg.content}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
