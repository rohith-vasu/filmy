from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading

from app.model_state import load_model, model_watcher_thread
from app.routes.auth import auth_router
from app.routes.users import user_router
from app.routes.user_feedback import user_feedback_router
from app.routes.recommendation import recommendation_router
from app.routes.movies import movie_router
from app.dependencies.auth import get_current_user
from app.core.settings import settings


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting FastAPI and loading ALS model...")
    load_model()

    # Background daily refresh thread
    thread = threading.Thread(target=model_watcher_thread, daemon=True)
    thread.start()

    print("⚡ Background model watcher running.")
    
    yield
    
    # Shutdown (if needed in the future)
    print("👋 Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    root_path="/filmy-api/v1",
    title="Filmy API",
    description="Visit http://0.0.0.0:8000/docs for API documentation",
    version="0.0.1",
    lifespan=lifespan
)

# CORS Configuration
ALLOWED_ORIGINS = [
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(user_router, dependencies=[Depends(get_current_user)])
app.include_router(movie_router)
app.include_router(recommendation_router)
app.include_router(user_feedback_router, dependencies=[Depends(get_current_user)])