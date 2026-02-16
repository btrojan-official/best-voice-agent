const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_BASE_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

export const API_ENDPOINTS = {
  CALL_START: `${API_BASE_URL}/api/call/start`,
  CALL_DETAILS: (id: string) => `${API_BASE_URL}/api/call/${id}`,
  WS_CALL: (id: string) => `${WS_BASE_URL}/api/ws/call/${id}`,
  
  ADMIN_LOGIN: `${API_BASE_URL}/api/admin/login`,
  ADMIN_CALLS: `${API_BASE_URL}/api/admin/calls`,
  ADMIN_CALL_DETAILS: (id: string) => `${API_BASE_URL}/api/admin/calls/${id}`,
  ADMIN_STATS: `${API_BASE_URL}/api/admin/stats`,
  ADMIN_SETTINGS: `${API_BASE_URL}/api/admin/settings`,
  ADMIN_SETTINGS_INFO: `${API_BASE_URL}/api/admin/settings/information`,
  ADMIN_SETTINGS_INFO_DELETE: (id: string) => `${API_BASE_URL}/api/admin/settings/information/${id}`,
};

export function getAuthHeader(token: string): HeadersInit {
  return {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  };
}
