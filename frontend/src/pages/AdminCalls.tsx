import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { apiService } from "../services/api";
import type { Call } from "../types";
import { CallStatus } from "../types";
import "./AdminCalls.css";

export default function AdminCalls() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCalls();
    const interval = setInterval(loadCalls, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadCalls = async () => {
    try {
      const data = await apiService.getCalls();
      setCalls(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load calls");
      console.error("Error loading calls:", err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getStatusClass = (status: CallStatus) => {
    return `status-badge status-${status.toLowerCase()}`;
  };

  if (loading) {
    return <div className="admin-page">Loading calls...</div>;
  }

  return (
    <div className="admin-page">
      <div className="page-header">
        <h1>Calls</h1>
        <div className="stats-summary">
          <span>Total: {calls.length}</span>
          <span>Pending: {calls.filter(c => c.status === CallStatus.PENDING).length}</span>
          <span>Completed: {calls.filter(c => c.status === CallStatus.COMPLETED).length}</span>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="calls-list">
        {calls.length === 0 ? (
          <div className="empty-state">No calls yet</div>
        ) : (
          calls.map((call) => (
            <Link to={`/admin/calls/${call.id}`} key={call.id} className="call-card">
              <div className="call-header">
                <div className="call-title-row">
                  {call.status === CallStatus.PENDING && (
                    <span className="status-indicator pending"></span>
                  )}
                  <h3>{call.title}</h3>
                </div>
                <span className={getStatusClass(call.status)}>
                  {call.status}
                </span>
              </div>
              
              <div className="call-meta">
                <span>Started: {formatDate(call.start_time)}</span>
                {call.end_time && (
                  <span>Ended: {formatDate(call.end_time)}</span>
                )}
              </div>
              
              <div className="call-stats-preview">
                <span>{call.messages.length} messages</span>
                <span>${call.cost_stats.total_cost.toFixed(4)}</span>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
