from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import router as api_router

app = FastAPI(title="Vector Search and Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "https://jobs-chatbot.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")