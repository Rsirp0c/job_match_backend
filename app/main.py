from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import router as api_router
import logging
import os
import uvicorn

logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI(title="Vector Search and Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://jobs-chatbot.vercel.app","http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "Backend is running"}

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)