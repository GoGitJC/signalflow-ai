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
  sentiment?: "positive" | "neutral" | "negative" | string | null;
  recording_url?: string | null;
  appointment_booked: boolean;
};

export type Caller = {
  id: string;
  business_id: string;
  name: string | null;
  phone: string;
  email: string | null;
  notes: string | null;
  tags: string[];
  status: string;
  created_at: string;
  updated_at?: string | null;
  call_count: number;
  appointment_count: number;
  last_interaction_at: string | null;
  recent_call_ids?: string[];
  recent_appointment_ids?: string[];
};

export type VoiceAgent = {
  id: string;
  business_id: string;
  retell_agent_id: string;
  retell_agent_name: string | null;
  name: string;
  greeting: string;
  system_prompt: string;
  voice: string | null;
  temperature: number | null;
  transfer_number: string | null;
  transfer_rules: string | null;
  active: boolean;
  updated_at?: string | null;
};

export type AnalyticsSummary = {
  range: string;
  from_at: string;
  to_at: string;
  calls_today: number;
  calls_total: number;
  bookings: number;
  conversion_rate: number;
  average_duration_seconds: number;
  missed_calls: number;
  transfers: number;
  ai_resolution_rate: number;
  booking_funnel: { calls: number; interested: number; booked: number; completed: number; cancelled: number };
  lead_sources: Record<string, number>;
  series: Array<{ label: string; date: string; calls: number; bookings: number; leads: number }>;
};

export type AuditEvent = {
  id: string;
  source: string;
  business_id: string | null;
  provider?: string | null;
  user_id?: string | null;
  action: string;
  status: string;
  detail?: string | null;
  created_at: string;
};

export type KnowledgeVersion = KnowledgeEntry & {
  entry_id: string;
  business_id: string;
  version: number;
  created_at: string;
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
