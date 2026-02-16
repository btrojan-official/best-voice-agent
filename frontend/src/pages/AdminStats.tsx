import { useState, useEffect } from "react";
import { apiService } from "../services/api";
import type { SystemStats } from "../types";
import "./AdminStats.css";

export default function AdminStats() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      const data = await apiService.getStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load stats");
      console.error("Error loading stats:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="admin-page">Loading statistics...</div>;
  }

  if (error || !stats) {
    return (
      <div className="admin-page">
        <div className="error-message">{error || "No stats available"}</div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <div className="page-header">
        <h1>Statistics</h1>
        <div className="last-updated">
          Last updated: {new Date(stats.last_updated).toLocaleString()}
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Calls</h3>
          <div className="stat-item">
            <span className="stat-label">Total Calls</span>
            <span className="stat-value">{stats.total_calls}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Completed</span>
            <span className="stat-value success">{stats.completed_calls}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Pending</span>
            <span className="stat-value warning">{stats.pending_calls}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Errors</span>
            <span className="stat-value error">{stats.error_calls}</span>
          </div>
        </div>

        <div className="stat-card">
          <h3>Usage - Tokens</h3>
          <div className="stat-item">
            <span className="stat-label">Input Tokens</span>
            <span className="stat-value">{stats.total_usage.input_tokens.toLocaleString()}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Output Tokens</span>
            <span className="stat-value">{stats.total_usage.output_tokens.toLocaleString()}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Total Tokens</span>
            <span className="stat-value">
              {(stats.total_usage.input_tokens + stats.total_usage.output_tokens).toLocaleString()}
            </span>
          </div>
        </div>

        <div className="stat-card">
          <h3>Usage - Characters</h3>
          <div className="stat-item">
            <span className="stat-label">Input Characters</span>
            <span className="stat-value">{stats.total_usage.input_characters.toLocaleString()}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Output Characters</span>
            <span className="stat-value">{stats.total_usage.output_characters.toLocaleString()}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">TTS Characters</span>
            <span className="stat-value">{stats.total_usage.tts_characters.toLocaleString()}</span>
          </div>
        </div>

        <div className="stat-card">
          <h3>Usage - Audio & LLM</h3>
          <div className="stat-item">
            <span className="stat-label">Transcription Time</span>
            <span className="stat-value">
              {stats.total_usage.transcription_seconds.toFixed(2)}s
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">LLM API Calls</span>
            <span className="stat-value">{stats.total_usage.llm_calls}</span>
          </div>
        </div>

        <div className="stat-card cost-card">
          <h3>Costs - LLM</h3>
          <div className="stat-item">
            <span className="stat-label">Input Cost</span>
            <span className="stat-value">${stats.total_costs.llm_input_cost.toFixed(4)}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Output Cost</span>
            <span className="stat-value">${stats.total_costs.llm_output_cost.toFixed(4)}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Total LLM</span>
            <span className="stat-value">
              ${(stats.total_costs.llm_input_cost + stats.total_costs.llm_output_cost).toFixed(4)}
            </span>
          </div>
        </div>

        <div className="stat-card cost-card">
          <h3>Costs - Audio</h3>
          <div className="stat-item">
            <span className="stat-label">Transcription</span>
            <span className="stat-value">${stats.total_costs.transcription_cost.toFixed(4)}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Text-to-Speech</span>
            <span className="stat-value">${stats.total_costs.tts_cost.toFixed(4)}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Total Audio</span>
            <span className="stat-value">
              ${(stats.total_costs.transcription_cost + stats.total_costs.tts_cost).toFixed(4)}
            </span>
          </div>
        </div>

        <div className="stat-card total-cost-card">
          <h3>Total Estimated Cost</h3>
          <div className="total-cost">
            ${stats.total_costs.total_cost.toFixed(4)}
          </div>
          <div className="cost-breakdown">
            <div className="breakdown-item">
              <span>LLM</span>
              <span>
                {((stats.total_costs.llm_input_cost + stats.total_costs.llm_output_cost) / stats.total_costs.total_cost * 100).toFixed(1)}%
              </span>
            </div>
            <div className="breakdown-item">
              <span>Audio</span>
              <span>
                {((stats.total_costs.transcription_cost + stats.total_costs.tts_cost) / stats.total_costs.total_cost * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {Object.keys(stats.model_latencies || {}).length > 0 && (
          <div className="stat-card latency-card" style={{ gridColumn: '1 / -1' }}>
            <h3>Model Performance (Latency per 100 Tokens)</h3>
            <div className="latency-grid">
              {Object.values(stats.model_latencies).map((modelStats) => (
                <div key={modelStats.model_name} className="latency-item">
                  <div className="model-name">{modelStats.model_name}</div>
                  <div className="latency-stats">
                    <div className="latency-stat">
                      <span className="latency-label">Avg Latency</span>
                      <span className="latency-value">
                        {modelStats.avg_latency_per_100_tokens.toFixed(1)}ms / 100 tokens
                      </span>
                    </div>
                    <div className="latency-stat">
                      <span className="latency-label">Total Calls</span>
                      <span className="latency-value">{modelStats.total_calls}</span>
                    </div>
                    <div className="latency-stat">
                      <span className="latency-label">Total Tokens</span>
                      <span className="latency-value">{modelStats.total_tokens.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
