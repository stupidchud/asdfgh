"""
api/main.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.oauth import router as oauth_router
from routers.protection.antinuke import router as antinuke_router

app = FastAPI(title="asdfgh", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(oauth_router)
app.include_router(antinuke_router)