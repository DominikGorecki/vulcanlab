export interface SubQuestion {
  id: string;
  question: string;
  rationale: string;
  estimated_tokens: number;
  relevant_items: number[];
}

export interface ResearchPlan {
  research_goal: string;
  key_themes: string[];
  sub_questions: SubQuestion[];
  synthesis_approach: string;
}

export interface MatchResult {
  result_id: number;
  question_text: string;
  similarity_score: number;
  quality_assessment?: string;
  content_preview?: string;
}

export interface MatchResultsResponse {
  matched_results: MatchResult[];
  recommended_strategy: string;
}

export interface ResearchSession {
  id: number;
  collection_id: number;
  thread_id: string;
  session_type: "manual" | "automated";
  status: string;
  research_plan?: ResearchPlan;
  current_phase?: string;
  state_data?: any;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface ResearchReport {
  id: number;
  session_id: number;
  report_content: string;
  executive_summary?: string;
  quality_evaluation?: any;
  report_metadata?: {
    word_count?: number;
    citation_count?: number;
    [key: string]: any;
  };
}

export interface SessionProgress {
  status: string;
  current_phase: string;
  sections_completed: number;
  total_sections: number;
  error?: string;
}
