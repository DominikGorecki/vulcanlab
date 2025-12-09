/**
 * TypeScript types for RAG configuration management.
 * Matches backend Pydantic schemas.
 */

export interface RagConfig {
  id: number;
  preset_name: string;
  is_default: boolean;
  description: string | null;
  config: RagConfigParams;
  created_at: string;
  updated_at: string;
}

export interface RagConfigParams {
  retrieval: RetrievalParams;
  consolidation: ConsolidationParams;
  augmentation: AugmentationParams;
}

export interface RetrievalParams {
  dense_limit: number;
  lexical_limit: number;
  rrf_k: number;
  top_k_rrf: number;
  top_n_final: number;
  entity_boost: number;
  min_word_count: number;
  min_char_count: number;
  min_content_length: number;
  enrich_lines_above: number;
  enrich_lines_below: number;
  mmr_lambda: number;
  reranker_batch_size: number;
  reranker_max_length: number;
}

export interface ConsolidationParams {
  coverage_threshold: number;
  line_gap: number;
  min_content_length: number;
  enrich_from_md: boolean;
}

export interface AugmentationParams {
  top_n_contexts: number;
}

// Request types
export interface RagConfigCreateRequest {
  preset_name: string;
  description?: string;
  is_default: boolean;
  config: RagConfigParams;
}

export interface RagConfigUpdateRequest {
  description?: string;
  config?: RagConfigParams;
}

// Validation constraints (matches backend)
export const PARAM_CONSTRAINTS = {
  retrieval: {
    dense_limit: { min: 0, max: 100, default: 19, description: "Max results per dense vector query (0 to disable)" },
    lexical_limit: { min: 0, max: 50, default: 5, description: "Max results per lexical (BM25) query (0 to disable)" },
    rrf_k: { min: 1, max: 100, default: 50, description: "RRF constant for rank fusion" },
    top_k_rrf: { min: 1, max: 200, default: 75, description: "Top candidates after RRF fusion" },
    top_n_final: { min: 1, max: 50, default: 17, description: "Final number of results after MMR" },
    entity_boost: { min: 0.0, max: 0.5, default: 0.05, step: 0.01, description: "Score boost per entity match" },
    min_word_count: { min: 0, max: 1000, default: 150, description: "Minimum words in chunk (0 to disable)" },
    min_char_count: { min: 0, max: 5000, default: 250, description: "Minimum characters in chunk (0 to disable)" },
    min_content_length: { min: 0, max: 5000, default: 750, description: "Min content length before enrichment" },
    enrich_lines_above: { min: 0, max: 50, default: 0, description: "Lines to add above chunk when enriching" },
    enrich_lines_below: { min: 0, max: 50, default: 13, description: "Lines to add below chunk when enriching" },
    mmr_lambda: { min: 0.0, max: 1.0, default: 0.7, step: 0.01, description: "MMR balance: relevance (1.0) vs diversity (0.0)" },
    reranker_batch_size: { min: 1, max: 32, default: 8, description: "Batch size for BGE reranker inference" },
    reranker_max_length: { min: 128, max: 1024, default: 512, description: "Max token length for reranker" },
  },
  consolidation: {
    coverage_threshold: { min: 0.0, max: 1.0, default: 0.5, step: 0.01, description: "% of parent coverage to replace with parent" },
    line_gap: { min: 0, max: 50, default: 7, description: "Max lines between chunks to merge them" },
    min_content_length: { min: 0, max: 5000, default: 350, description: "Min characters for final output inclusion" },
    enrich_from_md: { default: true, description: "Read content from markdown during consolidation" },
  },
  augmentation: {
    top_n_contexts: { min: 1, max: 20, default: 5, description: "Number of top contexts to include in prompt" },
  },
} as const;

// Helper to get default config
export function getDefaultConfig(): RagConfigParams {
  return {
    retrieval: {
      dense_limit: PARAM_CONSTRAINTS.retrieval.dense_limit.default,
      lexical_limit: PARAM_CONSTRAINTS.retrieval.lexical_limit.default,
      rrf_k: PARAM_CONSTRAINTS.retrieval.rrf_k.default,
      top_k_rrf: PARAM_CONSTRAINTS.retrieval.top_k_rrf.default,
      top_n_final: PARAM_CONSTRAINTS.retrieval.top_n_final.default,
      entity_boost: PARAM_CONSTRAINTS.retrieval.entity_boost.default,
      min_word_count: PARAM_CONSTRAINTS.retrieval.min_word_count.default,
      min_char_count: PARAM_CONSTRAINTS.retrieval.min_char_count.default,
      min_content_length: PARAM_CONSTRAINTS.retrieval.min_content_length.default,
      enrich_lines_above: PARAM_CONSTRAINTS.retrieval.enrich_lines_above.default,
      enrich_lines_below: PARAM_CONSTRAINTS.retrieval.enrich_lines_below.default,
      mmr_lambda: PARAM_CONSTRAINTS.retrieval.mmr_lambda.default,
      reranker_batch_size: PARAM_CONSTRAINTS.retrieval.reranker_batch_size.default,
      reranker_max_length: PARAM_CONSTRAINTS.retrieval.reranker_max_length.default,
    },
    consolidation: {
      coverage_threshold: PARAM_CONSTRAINTS.consolidation.coverage_threshold.default,
      line_gap: PARAM_CONSTRAINTS.consolidation.line_gap.default,
      min_content_length: PARAM_CONSTRAINTS.consolidation.min_content_length.default,
      enrich_from_md: PARAM_CONSTRAINTS.consolidation.enrich_from_md.default,
    },
    augmentation: {
      top_n_contexts: PARAM_CONSTRAINTS.augmentation.top_n_contexts.default,
    },
  };
}
