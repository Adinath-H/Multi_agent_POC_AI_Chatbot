import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
GENERATED_DIR = DATA_DIR / "generated"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
DB_PATH = DATA_DIR / "app.db"

# Groq configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.6-27b")

# Optional real-time web research
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
APP_SECRET = os.getenv("APP_SECRET", "change-me")

for folder in (DATA_DIR, UPLOAD_DIR, GENERATED_DIR, KNOWLEDGE_DIR):
    folder.mkdir(parents=True, exist_ok=True)
