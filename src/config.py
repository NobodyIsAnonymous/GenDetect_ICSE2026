"""Centralized path constants for the GenDetect project."""
from pathlib import Path

# Project root is one level up from this file (src/../)
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_RULES_DIR = PROJECT_ROOT / "data" / "rules"
DATA_BENCHMARK_DIR = PROJECT_ROOT / "data" / "benchmark"
MODELS_DIR = PROJECT_ROOT / "models"
DOCS_DIR = PROJECT_ROOT / "docs"

# Rules data files
NOLOOP_ENCODED_TRACE = DATA_RULES_DIR / "noloop_encoded_trace.csv"
ENCODED_TRACE = DATA_RULES_DIR / "encoded_trace.csv"
FINAL_CLASSIFIED_FUNCTIONS = DATA_RULES_DIR / "final_classified_functions.csv"

# Benchmark data files
BENCHMARK_DATA = DATA_BENCHMARK_DIR / "benchmark-data.csv"
CLASSIFIED_TX_FILTERED = DATA_BENCHMARK_DIR / "classified_tx_filtered.csv"
BENCHMARK_RESULTS = DATA_BENCHMARK_DIR / "benchmark-results.csv"
ML_BENCHMARK_RESULTS = DATA_BENCHMARK_DIR / "ml-benchmark-results.csv"

# Model files
TFIDF_VECTORIZER = MODELS_DIR / "tfidf_vectorizer.pkl"
XGBOOST_MODEL_JSON = MODELS_DIR / "xgboost_model.json"
XGBOOST_MODEL_PKL = MODELS_DIR / "xgboost_model.pkl"

# Docs
CLUSTERING_PNG = DOCS_DIR / "hierarchical_clustering_high_res.png"

# Log file
ERROR_LOG = PROJECT_ROOT / "error.log"
