export type Call = {id:string; caller_id:string|null; retell_call_id:string; started_at:string|null; duration_seconds:number|null; summary:string|null; transcript:string|null; intent:string|null; urgency:string|null; outcome:string|null; appointment_booked:boolean};
export type Appointment = {id:string; caller_id:string; call_id:string|null; service:string; start_time:string; status:string};
export type KnowledgeEntry = {id:string; category:string; question:string; answer:string; active:boolean};
