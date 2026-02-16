import type { LoginRequest, LoginResponse } from "../types";
import { API_ENDPOINTS } from "../config";

export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(API_ENDPOINTS.ADMIN_LOGIN, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials)
    });
    
    return response.json();
  },
  
  getToken(): string | null {
    return localStorage.getItem("auth_token");
  },
  
  setToken(token: string): void {
    localStorage.setItem("auth_token", token);
  },
  
  clearToken(): void {
    localStorage.removeItem("auth_token");
  },
  
  isAuthenticated(): boolean {
    return !!this.getToken();
  }
};
