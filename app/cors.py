import os

from fastapi.middleware.cors import CORSMiddleware


def configure_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("APP_ORIGIN").split(",") if os.getenv("APP_ORIGIN") else ["http://127.0.0.1:8001", "http://localhost:8001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
