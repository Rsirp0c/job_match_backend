from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import router as api_router

app = FastAPI(title="Vector Search and Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://jobs-chatbot.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=[
        "Content-Length", 
        "Content-Range", 
        "Content-Type",
        "Accept-Ranges",
        "Content-Disposition",
    ],
    max_age=600,  # Cache CORS preflight for 10 minutes
)

@app.get("/")
async def read_root():
    return {"message": "Backend is running"}

app.include_router(api_router, prefix="/api/v1")