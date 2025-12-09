"""
VulcanLab API - FastAPI REST interface for the VulcanLab system.

This package provides a REST API for interacting with the VulcanLab
Retrieval-Augmented Generation system.

Usage:
    # Run the development server
    venv\\Scripts\\uvicorn vulcanlab_api.main:app --reload

    # Or using Python module
    venv\\Scripts\\python -m vulcanlab_api

Endpoints:
    /init       - Initialization and setup operations
    /settings   - Configuration and settings management
    /conv       - Document conversion operations
    /sanitization - Content sanitization operations
    /chunk      - Document chunking operations
    /vec        - Vectorization operations
    /rag        - Retrieval, Augmentation and Generation operations

Interactive Docs:
    Swagger UI: http://localhost:8000/docs
    ReDoc:      http://localhost:8000/redoc
    OpenAPI:    http://localhost:8000/openapi.json
"""

__version__ = "0.1.0"


