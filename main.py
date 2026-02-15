#!/usr/bin/env python3
import uvicorn

from src.config import get_settings, setup_logging


def main():
    settings = get_settings()
    setup_logging(settings.log_level)

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
