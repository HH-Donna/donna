from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import ALLOWED_ORIGINS
from app.routers import emails_router, health_router, oauth_router
from app.routers.gmail_watch import router as gmail_watch_router
from app.routers.pubsub import router as pubsub_router
from app.routers.twilio import router as twilio_router
from app.routers.verification_calls import router as verification_calls_router

app = FastAPI(
    title="Donna Backend API", 
    version="1.0.0",
    description="Organized API for Gmail invoice email processing"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(emails_router)
app.include_router(oauth_router)
app.include_router(gmail_watch_router)
app.include_router(pubsub_router)
app.include_router(twilio_router, tags=["twilio"])
app.include_router(verification_calls_router, tags=["verification-calls"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)