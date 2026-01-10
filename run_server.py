#!/usr/bin/env python3
"""Run the ThreeDLLM API server."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "threedllm.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
