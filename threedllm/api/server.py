"""Server entry point for ThreeDLLM API."""

import uvicorn


def main():
    """Main entry point for the server."""
    uvicorn.run(
        "threedllm.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
