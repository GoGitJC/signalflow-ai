import type { Appointment, Call, KnowledgeEntry } from '../types';
const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
export const businessId = import.meta.env.VITE_BUSINESS_ID ?? localStorage.getItem('signalflow_business_id') ?? '';
async function request<T>(path:string, options?:RequestInit):Promise<T>{const response=await fetch(`${API}${path}`,{headers:{'Content-Type':'application/json',...(options?.headers||{})},...options});if(!response.ok)throw new Error((await response.json().catch(()=>({detail:response.statusText}))).detail);return response.json();}
export const api = {
 calls:()=>request<Call[]>(`/api/businesses/${businessId}/calls`),
 appointments:()=>request<Appointment[]>(`/api/businesses/${businessId}/appointments`),
 knowledge:()=>request<KnowledgeEntry[]>(`/api/businesses/${businessId}/knowledge-base`),
 addKnowledge:(payload:Omit<KnowledgeEntry,'id'>)=>request<KnowledgeEntry>(`/api/businesses/${businessId}/knowledge-base`,{method:'POST',body:JSON.stringify(payload)}),
 updateKnowledge:(id:string,payload:Partial<KnowledgeEntry>)=>request<KnowledgeEntry>(`/api/knowledge-base/${id}`,{method:'PATCH',body:JSON.stringify(payload)}),
 deleteKnowledge:(id:string)=>fetch(`${API}/api/knowledge-base/${id}`,{method:'DELETE'})
};
