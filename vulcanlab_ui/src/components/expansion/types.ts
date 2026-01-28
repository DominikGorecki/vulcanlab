/**
 * Expansion-related Type Definitions
 */

export interface SectionSummary {
  id: number;
  order: number;
  heading: string;
  summary: string;
  status: string;
  error_message: string | null;
}

export interface SectionDetail extends SectionSummary {
  expansion_id: number;
  expansion_prompt: string;
  expanded_queries: { queries: string[] } | null;
  hyde_answer: string | null;
  intent: string | null;
  entities: { entities: string[] } | null;
  clean_retrieval_context: { chunks: any[] } | null;
  augmented_prompt: string | null;
  response_text: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExpansionDetail {
  id: number;
  result_id: number;
  query_id: number;
  mode: "automatic" | "manual";
  status: string;
  combined_report: string | null;
  expansion_metadata: Record<string, any> | null;
  sections: SectionSummary[];
  created_at: string;
  updated_at: string;
}

export interface ExpansionListItem {
  id: number;
  result_id: number;
  query_id: number;
  mode: string;
  status: string;
  section_count: number;
  completed_count: number;
  failed_count: number;
  created_at: string;
}
