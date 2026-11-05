"""Configuration settings for FRAUDNET AI platform.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Base directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw" / "elliptic"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ANALYTICS_DIR = PROCESSED_DATA_DIR / "analytics"
RUNTIME_DIR = DATA_DIR / "runtime"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
DOCS_DIR = PROJECT_ROOT / "docs"

# Ensure runtime and report output directories exist
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# File paths
TRANSACTIONS_PARQUET_PATH = PROCESSED_DATA_DIR / "transactions.parquet"
EDGES_PARQUET_PATH = PROCESSED_DATA_DIR / "edges.parquet"
GRAPH_ARTIFACT_PATH = PROCESSED_DATA_DIR / "transaction_graph.pkl"
DATASET_SUMMARY_PATH = PROCESSED_DATA_DIR / "dataset_summary.json"

TRANSACTION_METRICS_PATH = ANALYTICS_DIR / "transaction_metrics.parquet"
TEMPORAL_SUMMARY_PATH = ANALYTICS_DIR / "temporal_summary.json"
NETWORK_PATTERNS_PATH = ANALYTICS_DIR / "network_patterns.json"
COMMUNITY_SUMMARY_PATH = ANALYTICS_DIR / "community_summary.json"

CHAMPION_MODEL_PATH = MODELS_DIR / "fraudnet_model_v1.joblib"
MODEL_SUMMARY_PATH = MODELS_DIR / "model_evaluation_summary.json"

DATABASE_PATH = RUNTIME_DIR / "fraudnet.db"

# Groq / LLM Configuration
# Default model specified for FRAUDNET AI cognitive forensic synthesis
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


def get_groq_api_key() -> str:
    """Safely retrieve GROQ_API_KEY from environment or Streamlit secrets without exposing it."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                key = str(st.secrets["GROQ_API_KEY"]).strip()
        except Exception:
            pass
    return key


def get_groq_model() -> str:
    """Retrieve GROQ_MODEL from environment or Streamlit secrets, defaulting to 'openai/gpt-oss-120b'."""
    model = os.getenv("GROQ_MODEL", "").strip()
    if not model:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GROQ_MODEL" in st.secrets:
                model = str(st.secrets["GROQ_MODEL"]).strip()
        except Exception:
            pass
    return model if model else DEFAULT_GROQ_MODEL


GROQ_API_KEY = get_groq_api_key()
GROQ_MODEL = get_groq_model()
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.1"))
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "2000"))
GROQ_CONNECTIVITY_TOKEN_BUDGET = int(os.getenv("GROQ_CONNECTIVITY_TOKEN_BUDGET", "250"))
GROQ_REASONING_EFFORT = os.getenv("GROQ_REASONING_EFFORT", "low")
GROQ_TIMEOUT_SECONDS = float(os.getenv("GROQ_TIMEOUT_SECONDS", "30.0"))

# Detection Risk Thresholds
DEFAULT_DECISION_THRESHOLD = 0.50
RISK_LEVEL_CRITICAL = 0.85
RISK_LEVEL_HIGH = 0.50
RISK_LEVEL_MODERATE = 0.25

# UI / Visualization Settings
MAX_GRAPH_RENDER_NODES = 120
MAX_GRAPH_RENDER_EDGES = 250
DEFAULT_EGO_RADIUS = 2

