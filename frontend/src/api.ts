export type Params = Record<string, string | number | boolean | null | undefined>
export interface RawNode { id: string; type: string; sub_type: string; label: string; name?: string; timestamp?: string | null; [key: string]: unknown }
export interface Entity extends RawNode { communications: number }
export interface Message { id: string; timestamp: string; date: string; hour: number; sender: string; receiver: string; content: string; evidence_ids: string[] }
export interface Page<T> { items: T[]; total: number; page: number; page_size: number }
export interface Quality { nodes: number; edges: number; missing_timestamp_count: number; missing_timestamp_ids: string[]; timestamp_outliers: {id:string; timestamp:string; reason:string}[]; inferred_edges: number; recorded_edges:number; communications_without_evidence:string[]; source_sha256:string; [key:string]:unknown }
export interface Overview { entities:number; communications:number; projection_edges:number; evidence_targets:number; total_entities:number; total_nodes:number; total_edges:number; total_communications:number; quality:Quality; period:{start:string;end:string} }
export interface Heat { days:string[]; cells:{date:string;hour:number;count:number;baseline:number}[]; daily:{date:string;count:number}[]; total:number }
export interface GraphNode extends RawNode { community:number; communications:number; sent:number; received:number; self_loops:number; weighted_degree:number; centrality:number }
export interface GraphEdge { key:string; source:string; target:string; weight:number; message_ids:string[]; type:string; is_inferred:boolean; bridge?:boolean }
export interface Community { id:number; members:string[]; size:number; representatives:string[]; communications:number; internal_communications:number; sent_external:number; received_external:number; topics:string[] }
export interface GraphData { nodes:GraphNode[]; edges:GraphEdge[]; communities:Community[]; mode:string; truncated:boolean; eligible_nodes?:number; components:number; definition:string }
export interface EvidenceCheck { code:string;text:string;related_ids?:string[] }
export interface Evidence { node:RawNode; participants:string[]; symmetric:boolean; edges:GraphEdge[]; messages:Message[]; targets:RawNode[]; status:string; checks?:EvidenceCheck[]; message_checks?:Record<string,EvidenceCheck[]>; nearby_exchange?:Message[]; source:{archive:string;member:string;node_id:string;sha256:string} }
export interface EventRow { id:string; sub_type:string; timestamp:string|null; time_source:string; time_status:string; participants:string[]; evidence_ids:string[]; status:string; node:RawNode }
export interface Timeline { source_sha256:string; items:EventRow[]; total:number; undated:number; excluded_outliers:number; types:string[] }
export interface Anomaly { date:string; hour:number; count:number; baseline:number; mad:number; score:number; flagged:boolean; message_ids:string[]; new_contacts:string[]; features:{name:string;value:number;contribution:number}[]; explanation:string }
export interface Anomalies { items:Anomaly[]; method:string; limitation:string }
export interface FeatureEvidence { label:string; alias_ids:string[]; candidate_ids:string[]; hour?:number; alias_count?:number; candidate_count?:number; contribution?:number; examples?:{id:string;excerpt:string}[] }
export interface AliasDiagnostics { scenarios:{key:string;kind:string;included_messages:number;excluded_message_ids:string[];ranking:{candidate:string;score:number}[]}[];method:string;limitation:string }
export interface AliasCandidate { candidate:string; score:number; features:Record<string,number>; contributions:Record<string,number>; support_ids:string[]; context_ids:string[]; conflicts:string[]; refuting_ids:string[]; sample_size:{alias:number;candidate:number}; shared_neighbors:string[]; feature_evidence:Record<string,FeatureEvidence[]> }
export interface Aliases { alias:string; alias_type:'Person'|'Vessel'; comparison:string; source_sha256:string; aliases:string[]; weights:Record<string,number>; items:AliasCandidate[]; status:string; method:string; scope:string; diagnostics?:AliasDiagnostics }
export interface RoleLinks { entity_id:string; comparison:string; source_sha256:string; items:{relationship_id:string; person:string; vessel:string; role:string|null; is_inferred:boolean; evidence_ids:string[]; all_evidence_ids:string[]; relationship:RawNode; edges:GraphEdge[]}[]; scope:string; limitation:string }
export interface PeriodProfiles { alias:string; source_sha256:string; split_date:string|null; split_mode:string; contact_jaccard:number|null; hour_cosine:number|null; segments:{start:string;end:string;count:number;sent:number;received:number;self_loops:number;hour_counts:number[];message_ids:string[];contacts:{entity_id:string;count:number;sent:number;received:number;message_ids:string[]}[]}[] }
export interface Topic { id:number; keywords:string[]; count:number; message_ids:string[]; representatives:Message[] }
export interface TopicData { topics:Topic[]; groups:{id:number;members:string[];counts:number[];message_ids:string[][]}[]; daily:{date:string;counts:number[]}[]; total:number;unassigned:number; model:{version:string;source_sha256:string;topic_count:number;seed:number;fit_scope:string;reconstruction_error:number}; method:string;limitation:string }

export async function get<T>(path:string, params:Params = {}, signal?:AbortSignal):Promise<T> {
  const query = new URLSearchParams()
  for (const [k,v] of Object.entries(params)) if (v !== undefined && v !== null && v !== '') query.set(k,String(v))
  const res = await fetch(`/api/${path}${query.size ? `?${query}` : ''}`, {signal})
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.error?.message || `请求失败 (${res.status})`)
  }
  return res.json() as Promise<T>
}
