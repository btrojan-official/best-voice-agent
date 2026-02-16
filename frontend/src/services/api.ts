import type { Call, SystemStats, Settings, InformationToGather } from "../types";
import { API_ENDPOINTS, getAuthHeader } from "../config";
import { authService } from "./auth";

export const apiService = {
  async getCalls(): Promise<Call[]> {
    const token = authService.getToken();
    if (!token) throw new Error("Not authenticated");
    
    const response = await fetch(API_ENDPOINTS.ADMIN_CALLS, {
      method: "GET",
      headers: getAuthHeader(token)
    });
    
    if (!response.ok) throw new Error("Failed to fetch calls");
    return response.json();
  },
  
  async getCallDetails(callId: string): Promise<Call> {
    const token = authService.getToken();
    if (!token) throw new Error("Not authenticated");
    
    const response = await fetch(API_ENDPOINTS.ADMIN_CALL_DETAILS(callId), {
      method: "GET",
      headers: getAuthHeader(token)
    });
    
    if (!response.ok) throw new Error("Failed to fetch call details");
    return response.json();
  },
  
  async getStats(): Promise<SystemStats> {
    const token = authService.getToken();
    if (!token) throw new Error("Not authenticated");
    
    const response = await fetch(API_ENDPOINTS.ADMIN_STATS, {
      method: "GET",
      headers: getAuthHeader(token)
    });
    
    if (!response.ok) throw new Error("Failed to fetch stats");
    return response.json();
  },
  
  async getSettings(): Promise<Settings> {
    const token = authService.getToken();
    if (!token) throw new Error("Not authenticated");
    
    const response = await fetch(API_ENDPOINTS.ADMIN_SETTINGS, {
      method: "GET",
      headers: getAuthHeader(token)
    });
    
    if (!response.ok) throw new Error("Failed to fetch settings");
    return response.json();
  },
  
  async updateSettings(updates: Partial<Settings>): Promise<Settings> {
    const token = authService.getToken();
    if (!token) throw new Error("Not authenticated");
    
    const response = await fetch(API_ENDPOINTS.ADMIN_SETTINGS, {
      method: "PATCH",
      headers: getAuthHeader(token),
      body: JSON.stringify(updates)
    });
    
    if (!response.ok) throw new Error("Failed to update settings");
    return response.json();
  },
  
  async addInformation(title: string, description: string): Promise<InformationToGather> {
    const token = authService.getToken();
    if (!token) throw new Error("Not authenticated");
    
    const response = await fetch(API_ENDPOINTS.ADMIN_SETTINGS_INFO, {
      method: "POST",
      headers: getAuthHeader(token),
      body: JSON.stringify({ title, description })
    });
    
    if (!response.ok) throw new Error("Failed to add information");
    return response.json();
  },
  
  async removeInformation(infoId: string): Promise<void> {
    const token = authService.getToken();
    if (!token) throw new Error("Not authenticated");
    
    const response = await fetch(API_ENDPOINTS.ADMIN_SETTINGS_INFO_DELETE(infoId), {
      method: "DELETE",
      headers: getAuthHeader(token)
    });
    
    if (!response.ok) throw new Error("Failed to remove information");
  },
  
  async startCall(): Promise<{ call_id: string; status: string; websocket_url: string }> {
    const response = await fetch(API_ENDPOINTS.CALL_START, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
    
    if (!response.ok) throw new Error("Failed to start call");
    return response.json();
  }
};
