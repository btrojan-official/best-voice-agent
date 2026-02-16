export const CallStatus = {
  PENDING: "pending",
  COMPLETED: "completed",
  ERROR: "error"
} as const;

export type CallStatus = typeof CallStatus[keyof typeof CallStatus];

export interface Message {
  role: string;
  content: string;
  timestamp: string;
  audio_duration?: number;
}

export interface UsageStats {
  input_tokens: number;
  output_tokens: number;
  input_characters: number;
  output_characters: number;
  transcription_seconds: number;
  tts_characters: number;
  llm_calls: number;
}

export interface CostStats {
  llm_input_cost: number;
  llm_output_cost: number;
  transcription_cost: number;
  tts_cost: number;
  total_cost: number;
}

export interface ToolCall {
  timestamp: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  result?: Record<string, unknown>;
}

export interface Call {
  id: string;
  title: string;
  status: CallStatus;
  start_time: string;
  end_time?: string;
  messages: Message[];
  tool_calls: ToolCall[];
  summary?: string;
  usage_stats: UsageStats;
  cost_stats: CostStats;
  error_message?: string;
}

export interface InformationToGather {
  id: string;
  title: string;
  description: string;
  created_at: string;
}

export interface Settings {
  model_name: string;
  temperature: number;
  information_to_gather: InformationToGather[];
}

export interface SystemStats {
  total_calls: number;
  completed_calls: number;
  pending_calls: number;
  error_calls: number;
  total_usage: UsageStats;
  total_costs: CostStats;
  last_updated: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  token?: string;
  message?: string;
}

export interface WebSocketMessage {
  type: "transcription" | "response" | "response_chunk" | "audio" | "acknowledgment" | "error";
  text?: string;
  data?: string;
  message?: string;
}
