from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict

# --- Request/Response Models ---

class SummarizationTriggerResponse(BaseModel):
    status: str
    message: str

class SummarizationStatusResponse(BaseModel):
    status: str
    total_nodes: int
    completed_nodes: int
    error: Optional[str] = None

class SummaryNodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    chunk_id: int
    work_id: int
    gist: str
    key_points: List[dict]
    definitions: List[dict]
    key_terms: List[dict]
    examples: List[dict]
    start_line: int
    end_line: int
    salience_score: float
    heading_breadcrumbs: Optional[str] = None
    level: Optional[str] = None
    parent_id: Optional[int] = None

class SummaryNodesResponse(BaseModel):
    nodes: List[SummaryNodeResponse]

class DeriveRequest(BaseModel):
    type: Literal['abstract', 'outline', 'key_concepts', 'chapter_summaries']

class DeriveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    work_id: int
    type: str
    content: dict
    line_references: List[dict]

class WorkSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    work_id: int
    type: str
    content: dict
    line_references: List[dict]

class SummarizedWorkResponse(BaseModel):
    work_id: int
    title: str
    node_count: int
    summaries: List[str]

class SummarizedWorksResponse(BaseModel):
    works: List[SummarizedWorkResponse]

class SuccessResponse(BaseModel):
    message: str

# --- Settings Models ---

class SummarizeSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    h1_always_summarize: bool
    h2_top_percent: int
    h3_salience_threshold: float
    h4_salience_threshold: float
    definition_density_weight: float
    list_density_weight: float
    keyphrase_novelty_weight: float
    location_prior_weight: float
    heading_depth_weight: float

class SummarizeSettingsUpdateRequest(BaseModel):
    h1_always_summarize: Optional[bool] = None
    h2_top_percent: Optional[int] = None
    h3_salience_threshold: Optional[float] = None
    h4_salience_threshold: Optional[float] = None
    definition_density_weight: Optional[float] = None
    list_density_weight: Optional[float] = None
    keyphrase_novelty_weight: Optional[float] = None
    location_prior_weight: Optional[float] = None
    heading_depth_weight: Optional[float] = None
