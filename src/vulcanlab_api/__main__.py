"""
Entry point for running the API as a module.

Usage:
    venv\\Scripts\\python -m vulcanlab_api
    venv\\Scripts\\python -m vulcanlab_api --host 0.0.0.0 --port 8080
"""

import argparse

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run the VulcanLab API server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    uvicorn.run(
        "vulcanlab_api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()


