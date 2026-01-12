"""
PostgreSQL-based checkpointer for LangGraph workflow state management.
Stores state in the research_sessions.state_data JSONB column.
"""

from typing import Any, Dict, List, Optional, Tuple, Callable, Iterator
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from langgraph.checkpoint.base import (
    BaseCheckpointSaver, 
    Checkpoint, 
    CheckpointMetadata, 
    CheckpointTuple,
    SerializerProtocol
)

from vulcanlab.data.models.research_session import ResearchSession
from vulcanlab.research.state import ResearchState

def serialize_state(state: ResearchState) -> Dict[str, Any]:
    """Serialize ResearchState to a JSON-serializable dictionary."""
    return dict(state)

def deserialize_state(state_dict: Dict[str, Any]) -> ResearchState:
    """Deserialize a dictionary to a ResearchState object."""
    return state_dict  # type: ignore

class PostgresSaver(BaseCheckpointSaver):
    """
    Checkpointer for LangGraph that persists state to PostgreSQL.
    Stores state in the research_sessions table.
    """

    def __init__(self, db_session_factory: Callable[[], Session]):
        """
        Initialize the checkpointer with a database session factory.

        Args:
            db_session_factory: A callable that returns a new SQLAlchemy Session.
        """
        super().__init__()
        self.db_session_factory = db_session_factory

    def get_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """
        Get a checkpoint tuple from the database.
        
        Args:
            config: LangGraph configuration containing thread_id.
            
        Returns:
            CheckpointTuple if found, else None.
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return None
            
        with self.db_session_factory() as session:
            query = select(ResearchSession).where(ResearchSession.thread_id == thread_id)
            research_session = session.execute(query).scalar_one_or_none()
            
            if research_session and research_session.state_data:
                # If state_data contains a full checkpoint, return it
                checkpoint_data = research_session.state_data.get("checkpoint")
                metadata_data = research_session.state_data.get("metadata", {})
                
                if checkpoint_data:
                    return CheckpointTuple(
                        config=config,
                        checkpoint=checkpoint_data,
                        metadata=metadata_data,
                        parent_config=None
                    )
            return None

    def put(self, config: dict, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: dict) -> dict:
        """
        Save a checkpoint to the database.
        
        Args:
            config: LangGraph configuration containing thread_id.
            checkpoint: The checkpoint data to save.
            metadata: Metadata associated with the checkpoint.
            new_versions: Version information.
            
        Returns:
            Dictionary containing version information (can be empty).
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return {}
            
        with self.db_session_factory() as session:
            query = select(ResearchSession).where(ResearchSession.thread_id == thread_id)
            research_session = session.execute(query).scalar_one_or_none()
            
            if research_session:
                # We store the checkpoint and metadata in state_data, merging with existing data
                current_state = research_session.state_data or {}
                new_state = dict(current_state)
                new_state.update({
                    "checkpoint": checkpoint,
                    "metadata": metadata
                })
                research_session.state_data = new_state
                research_session.updated_at = func.now()
                session.commit()
        return {}

    def put_writes(self, config: dict, writes: List[Tuple[str, Any]], task_id: str) -> None:
        """
        Store intermediate writes (optional for basic functionality).
        """
        pass

    def list(self, config: Optional[dict], *, filter: Optional[dict] = None, before: Optional[dict] = None, limit: Optional[int] = None) -> Iterator[CheckpointTuple]:
        """
        List checkpoints matching criteria.
        """
        # Minimal implementation for listing
        return iter([])

    def get_next_version(self, current_version: Optional[str], item: Any) -> str:
        """Required by LangGraph checkpointer interface."""
        return str(int(current_version or "0") + 1)
