export type Call = {
  id: string;
  business_id?: string;
  caller_id: string | null;
  retell_call_id: string;
  direction?: string;
  started_at: string | null;
  ended_at?: string | null;
  duration_seconds: number | null;
  summary: string | null;
  transcript: string | null;
  intent: string | null;
  urgency: string | null;
  outcome: string | null;
  recording_url?: string | null;
  appointment_booked: boolean;
};

export type Appointment = {
  id: string;
  business_id?: string;
  caller_id: string;
  call_id: string | null;
  cal_event_id?: string | null;
  service: string;
  start_time: string;
  end_time?: string;
  status: string;
};

export type KnowledgeEntry = {
  id: string;
  category: string;
  question: string;
  answer: string;
  active: boolean;
};

export type PageId =
  | "overview"
  | "calls"
  | "appointments"
  | "knowledge"
  | "voice-agent"
  | "customers"
  | "analytics"
  | "settings"
  | "help";

export type LoadState = "idle" | "loading" | "success" | "error";
