"""
Shared dependencies for FastAPI dependency injection.

Usage:
    from vulcanlab_api.dependencies import get_db_session, CommonQueryParams

    @router.get("/items")
    async def get_items(
        commons: Annotated[CommonQueryParams, Depends()],
        db: Annotated[Session, Depends(get_db_session)]
    ):
        ...
"""

from typing import Annotated

from fastapi import Depends, Query


class CommonQueryParams:
    """Common query parameters used across multiple endpoints."""

    def __init__(
        self,
        skip: Annotated[
            int,
            Query(
                ge=0,
                description="Number of items to skip for pagination",
                example=0,
            ),
        ] = 0,
        limit: Annotated[
            int,
            Query(
                ge=1,
                le=100,
                description="Maximum number of items to return",
                example=20,
            ),
        ] = 20,
    ):
        self.skip = skip
        self.limit = limit


# Type alias for dependency injection
CommonParams = Annotated[CommonQueryParams, Depends()]


from vulcanlab.data.database import get_db_session


