"""Standalone AI module startup entrypoint."""

import uvicorn

from config import settings


if __name__ == "__main__":
    uvicorn.run(
        "ai_module.app:app",
        host=settings.HOST,
        port=8090,
        reload=settings.DEBUG,
    )

