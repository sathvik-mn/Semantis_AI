"""
Semantys AI - Semantic Cache API (Enterprise Edition)

Repo: Semantys_AI
Folder: backend/

FastAPI service providing:
 - Multi-tenant, org-level auth (Bearer sc-{org_slug}-{any})
 - Exact + semantic cache (FAISS cosine) with Redis L2 + PostgreSQL L3
 - Adaptive per-tenant threshold
 - Rotating logs (access/errors/semantic_ops)
 - OpenAI integration
 - OpenAI-like POST /v1/chat/completions + simple GET /query
 - Audit logging, API key scoping, per-org rate limits
"""

import os
import time
import re
import logging
import hashlib
import json
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict
from contextvars import ContextVar
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import numpy as np

# Shared bounded thread pool for background tasks (cache storage, logging, webhooks)
_bg_executor = ThreadPoolExecutor(max_workers=32, thread_name_prefix="bg-worker")
import faiss
from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, validator
from dotenv import load_dotenv

# -----------------------------
# Environment & OpenAI client
# -----------------------------
load_dotenv()

# Sentry error tracking (optional — set SENTRY_DSN to enable)
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            environment=os.getenv("ENVIRONMENT", "development"),
        )
        logging.info("Sentry initialized")
    except ImportError:
        logging.warning("sentry-sdk not installed, error tracking disabled")
    except Exception as e:
        logging.warning(f"Sentry init failed: {e}")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",") if o.strip()]
if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-REPLACE_ME":
    logging.critical("OPENAI_API_KEY is not set or is placeholder. Server-side LLM calls will fail. BYOK users can supply their own key.")

# openai python (responses-compatible style kept for portability)
import openai
openai.api_key = OPENAI_API_KEY

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIMENSIONS = int(os.getenv("EMBED_DIMENSIONS", "1024"))
CHAT_MODEL  = os.getenv("CHAT_MODEL", "gpt-4o-mini")

# Local model config — lazy-loaded to avoid startup cost when not needed
LOCAL_MODEL_NAME = os.getenv("LOCAL_EMBED_MODEL", "all-MiniLM-L6-v2")
LOCAL_MODEL_ENABLED = os.getenv("LOCAL_EMBED_ENABLED", "true").lower() == "true"
CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
CROSS_ENCODER_ENABLED = os.getenv("CROSS_ENCODER_ENABLED", "false").lower() == "true"

# ── Performance: local primary embedding ──
# When enabled, uses a local sentence-transformer as the PRIMARY embedding model
# instead of OpenAI API. Eliminates 200-800ms API latency per query.
# OpenAI embedding becomes the fallback if local model fails.
LOCAL_PRIMARY_MODEL_NAME = os.getenv("LOCAL_PRIMARY_EMBED_MODEL", "")  # e.g., "nomic-ai/nomic-embed-text-v1.5"
LOCAL_PRIMARY_ENABLED = os.getenv("LOCAL_PRIMARY_EMBED_ENABLED", "false").lower() == "true"
# Asymmetric prefix support: different prefixes for queries vs stored documents
# Models like nomic-embed-text and gte are trained with these prefixes
EMBED_QUERY_PREFIX = os.getenv("EMBED_QUERY_PREFIX", "search_query: ")
EMBED_DOC_PREFIX = os.getenv("EMBED_DOC_PREFIX", "search_document: ")
# Whether to use asymmetric prefixes (disable for models that don't support it)
USE_ASYMMETRIC_PREFIX = os.getenv("USE_ASYMMETRIC_PREFIX", "false").lower() == "true"

# ── Performance: spelling correction ──
SPELLING_CORRECTION_ENABLED = os.getenv("SPELLING_CORRECTION_ENABLED", "true").lower() == "true"

# IVF threshold — switch from brute-force to IVF when tenant has more entries
IVF_UPGRADE_THRESHOLD = int(os.getenv("IVF_UPGRADE_THRESHOLD", "10000"))

# -----------------------------
# Logging setup (rotating)
# -----------------------------
os.makedirs("logs", exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production log aggregation."""
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

LOG_FORMAT = os.getenv("LOG_FORMAT", "text")  # "json" for structured logging

def make_rotating_logger(name: str, filename: str, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    handler = RotatingFileHandler(
        os.path.join("logs", filename), maxBytes=10_000_000, backupCount=5
    )
    if LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
        )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # Also stream to stdout for dev visibility
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    return logger

# Create comprehensive loggers
access_log      = make_rotating_logger("access", "access.log", logging.INFO)
error_log       = make_rotating_logger("errors", "errors.log", logging.ERROR)
semantic_log    = make_rotating_logger("semantic", "semantic_ops.log", logging.INFO)
performance_log = make_rotating_logger("performance", "performance.log", logging.INFO)
security_log    = make_rotating_logger("security", "security.log", logging.WARNING)
system_log      = make_rotating_logger("system", "system.log", logging.INFO)
app_log         = make_rotating_logger("application", "application.log", logging.INFO)

# -----------------------------
# Domain heuristics (optional)
# -----------------------------
DOMAIN_MAP = {
    "finance":   ["stock", "market", "inflation", "interest", "portfolio", "revenue", "profit", "dividend", "bond", "equity"],
    "legal":     ["contract", "clause", "law", "liability", "nda", "compliance", "statute", "regulation", "plaintiff", "defendant"],
    "tech":      ["api", "python", "vector", "fastapi", "kubernetes", "embedding", "docker", "database", "algorithm", "microservice"],
    "geography": ["capital", "country", "city", "border", "continent", "population", "region", "territory"],
    "medical":   ["symptom", "diagnosis", "treatment", "patient", "clinical", "drug", "therapy", "disease"],
    "education": ["course", "curriculum", "student", "exam", "grade", "university", "lecture", "assignment"],
}

def models_compatible(requested: str, cached: str) -> bool:
    """Check if a cached entry's model is compatible with the requested model.
    For semantic caching, the cached RESPONSE content is what matters — not
    which specific model variant generated it. A response about 'What is AI?'
    from gpt-4o-mini is equally valid when the user asks via gpt-4o.

    Returns True if the models are in the same family or either is a
    general-purpose chat model (gpt-4o variants, gpt-3.5, etc.)."""
    if requested == cached:
        return True
    # Normalize model names to family
    def _family(m: str) -> str:
        m = m.lower().strip()
        if m.startswith("gpt-4o"):
            return "gpt-4o"
        if m.startswith("gpt-4"):
            return "gpt-4"
        if m.startswith("gpt-3.5"):
            return "gpt-3.5"
        if m.startswith("claude"):
            return "claude"
        return m
    return _family(requested) == _family(cached)

def domain_hint(text: str) -> str:
    t = text.lower()
    best, hits = "general", 0
    for d, kws in DOMAIN_MAP.items():
        score = sum(1 for k in kws if k in t)
        if score > hits:
            best, hits = d, score
    return best

# -----------------------------
# Query normalization for better matching
# -----------------------------
_CONTRACTIONS = {
    "won't": "will not", "can't": "cannot", "n't": " not",
    "'re": " are", "'ve": " have", "'ll": " will", "'d": " would",
    "'m": " am", "let's": "let us", "it's": "it is", "i'm": "i am",
    "he's": "he is", "she's": "she is", "that's": "that is",
    "what's": "what is", "there's": "there is", "here's": "here is",
    "who's": "who is", "how's": "how is", "where's": "where is",
    "wouldn't": "would not", "shouldn't": "should not", "couldn't": "could not",
    "doesn't": "does not", "didn't": "did not", "isn't": "is not",
    "aren't": "are not", "wasn't": "was not", "weren't": "were not",
    "hasn't": "has not", "haven't": "have not", "hadn't": "had not",
}
_CONTRACTION_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(_CONTRACTIONS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
_FILLER_RE = re.compile(
    r"\b(please|pls|plz|hey|hi|hello|um|uh|like|just|actually|basically|literally|ok|okay|thanks|thank you|thx|yo|well|so|anyway|anyways|right)\b",
    re.IGNORECASE,
)
_MULTI_SPACE_RE = re.compile(r"\s+")
_PUNCT_NOISE_RE = re.compile(r"[.!?,;:]+$")
_PUNCT_INTERNAL_RE = re.compile(r"(?<=\s)[,;:]+|[,;:]+(?=\s)")

# --- Abbreviation / acronym expansion for semantic normalization ---
_ABBREVIATIONS = {
    "ml": "machine learning", "ai": "artificial intelligence",
    "nlp": "natural language processing", "dl": "deep learning",
    "cv": "computer vision", "rl": "reinforcement learning",
    "db": "database", "api": "application programming interface",
    "ui": "user interface", "ux": "user experience",
    "ci": "continuous integration", "cd": "continuous deployment",
    "k8s": "kubernetes", "js": "javascript", "ts": "typescript",
    "py": "python", "sql": "structured query language",
    "aws": "amazon web services", "gcp": "google cloud platform",
    "llm": "large language model", "rag": "retrieval augmented generation",
    "etl": "extract transform load", "orm": "object relational mapping",
    "sdk": "software development kit", "cli": "command line interface",
    "http": "hypertext transfer protocol", "tcp": "transmission control protocol",
    "gpu": "graphics processing unit", "cpu": "central processing unit",
    "ram": "random access memory", "ssd": "solid state drive",
    "iot": "internet of things", "saas": "software as a service",
    "roi": "return on investment", "kpi": "key performance indicator",
    "hr": "human resources", "ceo": "chief executive officer",
    "cto": "chief technology officer", "mvp": "minimum viable product",
    "oop": "object oriented programming", "fp": "functional programming",
    "tdd": "test driven development", "ddd": "domain driven design",
    "dns": "domain name system", "ssl": "secure sockets layer",
    "ssh": "secure shell", "vpn": "virtual private network",
}
_ABBREVIATION_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(_ABBREVIATIONS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

# --- Synonym groups: words that mean the same thing in context ---
_SYNONYM_GROUPS = [
    {"cost", "price", "fee", "charge", "expense", "rate"},
    {"buy", "purchase", "acquire", "order", "get"},
    {"fast", "quick", "rapid", "speedy", "swift"},
    {"big", "large", "huge", "enormous", "massive"},
    {"small", "tiny", "little", "miniature", "compact"},
    {"start", "begin", "initiate", "launch", "commence"},
    {"end", "stop", "finish", "terminate", "conclude", "halt"},
    {"create", "make", "build", "generate", "produce", "construct"},
    {"delete", "remove", "erase", "eliminate", "drop"},
    {"change", "modify", "alter", "update", "edit", "revise"},
    {"show", "display", "present", "render", "exhibit"},
    {"hide", "conceal", "obscure"},
    {"send", "transmit", "deliver", "dispatch"},
    {"receive", "get", "obtain", "accept"},
    {"error", "bug", "issue", "problem", "fault", "defect", "glitch"},
    {"fix", "repair", "resolve", "patch", "debug", "correct"},
    {"help", "assist", "support", "aid"},
    {"use", "utilize", "employ", "leverage"},
    {"describe", "clarify", "elaborate", "illustrate"},
    {"difference", "distinction", "comparison", "contrast"},
    {"advantage", "benefit", "pro", "upside"},
    {"disadvantage", "drawback", "con", "downside"},
    {"allow", "permit", "enable", "authorize"},
    {"prevent", "block", "prohibit", "forbid", "disallow"},
    {"increase", "raise", "boost", "grow", "escalate"},
    {"decrease", "reduce", "lower", "diminish", "shrink"},
    {"important", "crucial", "critical", "vital", "essential", "significant"},
    {"configure", "setup", "set up", "install", "initialize"},
    {"connect", "link", "attach", "join", "integrate"},
    {"disconnect", "detach", "separate", "unlink"},
]
# Build a word → canonical form lookup (first word in each group is canonical)
_SYNONYM_MAP: Dict[str, str] = {}
for _group in _SYNONYM_GROUPS:
    _canonical = sorted(_group)[0]  # alphabetically first as canonical
    for _word in _group:
        _SYNONYM_MAP[_word] = _canonical

# --- Question type normalization ---
_QUESTION_PREFIXES = [
    (re.compile(r"^(what is|what are|what's|whats)\b", re.I), "define"),
    (re.compile(r"^(how to|how do i|how do you|how can i|how can you|how should i)\b", re.I), "howto"),
    (re.compile(r"^(why does|why do|why is|why are|why did)\b", re.I), "why"),
    (re.compile(r"^(when did|when does|when is|when was|when will)\b", re.I), "when"),
    (re.compile(r"^(where is|where are|where do|where can)\b", re.I), "where"),
    (re.compile(r"^(can i|can you|is it possible to|am i able to)\b", re.I), "ability"),
    (re.compile(r"^(tell me about|explain|describe|give me info on)\b", re.I), "define"),
    (re.compile(r"^(compare|difference between|differences between|vs|versus)\b", re.I), "compare"),
    (re.compile(r"^(list|enumerate|name|give me a list of|what are the)\b", re.I), "list"),
]

def _extract_question_type(text: str) -> str:
    """Extract the semantic intent type from a query."""
    for pattern, qtype in _QUESTION_PREFIXES:
        if pattern.search(text):
            return qtype
    return "general"

# --- Stopwords for IDF-weighted matching ---
_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "both", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "and", "but",
    "or", "if", "while", "about", "up", "out", "off", "over", "down",
    "i", "me", "my", "we", "our", "you", "your", "he", "him", "his",
    "she", "her", "it", "its", "they", "them", "their", "what", "which",
    "who", "whom", "this", "that", "these", "those", "am",
})

# --- Porter-style suffix stemming (lightweight, no external deps) ---
_STEM_SUFFIXES = [
    ("iguration", "igure"),  # configuration → configure
    ("uration", "ure"),
    ("ational", "ate"), ("tional", "tion"), ("enci", "ence"),
    ("anci", "ance"), ("izer", "ize"), ("isation", "ize"),
    ("ization", "ize"), ("ation", "ate"), ("ator", "ate"),
    ("alism", "al"), ("iveness", "ive"), ("fulness", "ful"),
    ("ousness", "ous"), ("aliti", "al"), ("iviti", "ive"),
    ("biliti", "ble"), ("alli", "al"), ("entli", "ent"),
    ("eli", "e"), ("ousli", "ous"),
    ("ment", ""), ("ness", ""),
    ("nning", "n"), ("tting", "t"), ("pping", "p"), ("dding", "d"),  # doubled consonant + ing
    ("ings", ""), ("ning", "n"),
    ("ting", "t"), ("ring", "r"), ("ling", "l"),
    ("ing", ""),
    ("ies", "y"),
    ("tion", "te"), ("sion", "se"), ("able", ""),
    ("ible", ""), ("ence", ""), ("ance", ""),
    ("ful", ""), ("less", ""),
    ("ly", ""), ("ed", ""), ("er", ""), ("es", ""), ("s", ""),
]

def _light_stem(word: str) -> str:
    """Lightweight suffix stripping for matching. Only strips common suffixes
    to reduce word forms without being as aggressive as full Porter stemming."""
    if len(word) <= 3:
        return word
    for suffix, replacement in _STEM_SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) + len(replacement) >= 3:
            return word[:-len(suffix)] + replacement
    return word


def normalize_query(text: str) -> str:
    """Light normalization for hash-index lookups: expand contractions, strip
    filler words, collapse whitespace. Does NOT expand abbreviations — the
    embedding model handles semantic equivalence (ML≈machine learning, typos, etc.)."""
    t = text.strip().lower()
    t = _CONTRACTION_RE.sub(lambda m: _CONTRACTIONS.get(m.group(0).lower(), m.group(0)), t)
    t = _FILLER_RE.sub("", t)
    t = _PUNCT_NOISE_RE.sub("", t)
    t = _PUNCT_INTERNAL_RE.sub("", t)  # remove orphaned commas/semicolons after filler removal
    t = _MULTI_SPACE_RE.sub(" ", t).strip()
    return t

def deep_normalize(text: str) -> str:
    """Heavy semantic normalization: contractions + abbreviations + synonyms +
    stemming. Used for the semantic matching pipeline (not for hash lookups)."""
    t = normalize_query(text)
    # Expand abbreviations
    t = _ABBREVIATION_RE.sub(lambda m: _ABBREVIATIONS.get(m.group(0).lower(), m.group(0)), t)
    # Replace synonyms with canonical forms
    words = t.split()
    normalized_words = []
    for w in words:
        canonical = _SYNONYM_MAP.get(w, w)
        normalized_words.append(canonical)
    t = " ".join(normalized_words)
    return t

def _tokenize(text: str) -> set:
    """Simple word-level tokenizer for overlap scoring."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))

def _tokenize_stemmed(text: str) -> set:
    """Word-level tokenizer with lightweight stemming."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return set(_light_stem(t) for t in tokens)

def token_overlap_score(query: str, candidate: str) -> float:
    """Jaccard token overlap. Returns 0.0..1.0."""
    q_tokens = _tokenize(query)
    c_tokens = _tokenize(candidate)
    if not q_tokens:
        return 0.0
    union = q_tokens | c_tokens
    if not union:
        return 0.0
    return len(q_tokens & c_tokens) / len(union)

# ── Advanced similarity signals ──

def _char_ngrams(text: str, n: int = 3) -> set:
    """Extract character n-grams from text (whitespace removed)."""
    t = re.sub(r"\s+", "", text.lower())
    if len(t) < n:
        return {t}
    return set(t[i:i+n] for i in range(len(t) - n + 1))

def char_ngram_similarity(query: str, candidate: str, n: int = 3) -> float:
    """Dice coefficient on character n-grams. Excellent for catching typos,
    misspellings, and morphological variants (e.g., 'running' vs 'run')."""
    q_ngrams = _char_ngrams(query, n)
    c_ngrams = _char_ngrams(candidate, n)
    if not q_ngrams or not c_ngrams:
        return 0.0
    intersection = len(q_ngrams & c_ngrams)
    return (2.0 * intersection) / (len(q_ngrams) + len(c_ngrams))

def stemmed_overlap_score(query: str, candidate: str) -> float:
    """Jaccard overlap on stemmed tokens. Catches morphological variants
    like 'configure/configuration', 'running/run', 'better/best'."""
    q_tokens = _tokenize_stemmed(query)
    c_tokens = _tokenize_stemmed(candidate)
    if not q_tokens:
        return 0.0
    union = q_tokens | c_tokens
    if not union:
        return 0.0
    return len(q_tokens & c_tokens) / len(union)

def idf_weighted_overlap(query: str, candidate: str) -> float:
    """IDF-weighted token overlap. Stopwords contribute less, rare/meaningful
    words contribute more. This prevents 'how do I sort a list' from matching
    'how do I reverse a list' just because of shared stopwords."""
    q_tokens = re.findall(r"[a-z0-9]+", query.lower())
    c_tokens = re.findall(r"[a-z0-9]+", candidate.lower())
    if not q_tokens or not c_tokens:
        return 0.0

    # Weight: stopwords=0.1, regular words=1.0
    def weight(w):
        return 0.1 if w in _STOPWORDS else 1.0

    q_set = set(q_tokens)
    c_set = set(c_tokens)
    all_words = q_set | c_set
    if not all_words:
        return 0.0

    weighted_intersection = sum(weight(w) for w in q_set & c_set)
    weighted_union = sum(weight(w) for w in all_words)
    return weighted_intersection / weighted_union if weighted_union > 0 else 0.0

def synonym_expanded_overlap(query: str, candidate: str, query_norm_cache: Optional[str] = None) -> float:
    """Token overlap after synonym normalization and stemming.
    'What is the cost?' matches 'What is the price?' through synonym mapping.

    If *query_norm_cache* is provided, skip re-normalizing the query (the caller
    already deep-normalized it once and is reusing the result across candidates).
    """
    q_norm = query_norm_cache if query_norm_cache is not None else deep_normalize(query)
    c_norm = deep_normalize(candidate)
    q_tokens = _tokenize_stemmed(q_norm)
    c_tokens = _tokenize_stemmed(c_norm)
    if not q_tokens:
        return 0.0
    union = q_tokens | c_tokens
    if not union:
        return 0.0
    return len(q_tokens & c_tokens) / len(union)

def key_entity_overlap(query: str, candidate: str) -> float:
    """Overlap of key entities (non-stopword tokens). This signal is critical
    for preventing false matches where the *topic* differs but structure is
    similar (e.g., 'capital of France' vs 'capital of Germany')."""
    q_tokens = set(w for w in re.findall(r"[a-z0-9]+", query.lower()) if w not in _STOPWORDS)
    c_tokens = set(w for w in re.findall(r"[a-z0-9]+", candidate.lower()) if w not in _STOPWORDS)
    if not q_tokens or not c_tokens:
        return 0.0
    intersection = len(q_tokens & c_tokens)
    # Use min-denominator (Overlap coefficient) — more lenient than Jaccard
    # for queries of different lengths
    return intersection / min(len(q_tokens), len(c_tokens))

def question_type_match(query: str, candidate: str) -> float:
    """Returns 1.0 if both queries have the same question type, 0.5 if one
    is 'general', 0.0 if they conflict. Prevents 'how to X' from matching
    'what is X' when they need different response types."""
    qt = _extract_question_type(query)
    ct = _extract_question_type(candidate)
    if qt == ct:
        return 1.0
    if qt == "general" or ct == "general":
        return 0.5
    return 0.0

def sorted_token_similarity(query: str, candidate: str) -> float:
    """Compare queries after sorting their tokens alphabetically.
    Catches word-order variations like 'python list comprehension'
    vs 'list comprehension in python'."""
    q_tokens = sorted(w for w in re.findall(r"[a-z0-9]+", query.lower()) if w not in _STOPWORDS)
    c_tokens = sorted(w for w in re.findall(r"[a-z0-9]+", candidate.lower()) if w not in _STOPWORDS)
    if not q_tokens or not c_tokens:
        return 0.0
    # Use a simple set overlap on sorted (since sorting already removes order)
    q_set, c_set = set(q_tokens), set(c_tokens)
    union = q_set | c_set
    if not union:
        return 0.0
    return len(q_set & c_set) / len(union)


def compute_text_similarity(query: str, candidate: str, query_deep_norm: Optional[str] = None) -> dict:
    """Compute all text-based similarity signals between query and candidate.
    Returns a dict of individual scores and a combined 'text_sim' score.

    If *query_deep_norm* is provided, it is reused for the synonym signal
    instead of re-calling deep_normalize(query) for every candidate.
    """
    tok = token_overlap_score(query, candidate)
    ngram = char_ngram_similarity(query, candidate)
    stemmed = stemmed_overlap_score(query, candidate)
    idf = idf_weighted_overlap(query, candidate)
    synonym = synonym_expanded_overlap(query, candidate, query_norm_cache=query_deep_norm)
    entity = key_entity_overlap(query, candidate)
    qtype = question_type_match(query, candidate)
    sorted_tok = sorted_token_similarity(query, candidate)

    # Weighted combination of text signals:
    # - Entity overlap is most important (prevents topic mismatches)
    # - Synonym + IDF overlap catches paraphrases
    # - Char n-grams catch typos and morphological variants
    # - Question type prevents intent mismatches
    # - Sorted token catches word reordering
    text_sim = (
        0.25 * entity +       # key entity match (topic correctness)
        0.20 * synonym +      # synonym-normalized overlap (paraphrases)
        0.15 * idf +          # IDF-weighted overlap (meaningful words)
        0.15 * ngram +        # character n-gram (typos, morphology)
        0.10 * stemmed +      # stemmed overlap (word forms)
        0.10 * qtype +        # question type agreement
        0.05 * sorted_tok     # word-order invariant overlap
    )

    return {
        "token_overlap": tok,
        "char_ngram": ngram,
        "stemmed_overlap": stemmed,
        "idf_weighted": idf,
        "synonym_expanded": synonym,
        "entity_overlap": entity,
        "question_type": qtype,
        "sorted_token": sorted_tok,
        "text_sim": text_sim,
    }


def hybrid_score(cosine_sim: float, text_sim: float) -> float:
    """Multi-signal hybrid scoring. Cosine similarity from the embedding model
    remains dominant (it handles deep semantics, typos, abbreviations, and
    paraphrases). The text similarity composite boosts confidence when
    surface-level signals agree, and acts as a safety net when they disagree.

    The weight split is 88% cosine + 12% text because:
    - Cosine from a good embedding model captures ~95% of semantic meaning
    - Text signals catch the remaining edge cases (topic drift, entity mismatch)
    - Too much text weight would penalize valid paraphrases with low token overlap
    """
    return 0.88 * cosine_sim + 0.12 * text_sim

# -----------------------------
# Embeddings & LLM
# -----------------------------
def _get_user_openai_key(user_id: Optional[str]) -> Optional[str]:
    """Retrieve and decrypt the user's BYOK OpenAI key, or return None."""
    if not user_id:
        return None
    
    try:
        from database import get_user_openai_key_encrypted
        from encryption import decrypt_api_key
        
        encrypted_key = get_user_openai_key_encrypted(user_id)
        if encrypted_key:
            return decrypt_api_key(encrypted_key)
    except Exception as e:
        error_log.warning(f"Failed to get user OpenAI key | user_id={user_id} | error={str(e)}")
    
    return None

_openai_key_lock = threading.Lock()

def _resolve_openai_key(user_id: Optional[str] = None) -> str:
    """Get the effective OpenAI API key (user BYOK or server fallback)."""
    user_api_key = _get_user_openai_key(user_id)
    key = user_api_key or OPENAI_API_KEY
    if not key or key == "sk-REPLACE_ME":
        raise ValueError(
            "No OpenAI API key available. Either add your own key in Account Settings, "
            "or ask the admin to set a server-level OPENAI_API_KEY."
        )
    return key

EMBEDDING_PREFIX = "Semantic meaning: "

# Reusable OpenAI client pool
_openai_clients: Dict[str, "openai.OpenAI"] = {}
_client_lock = threading.Lock()

def _get_openai_client(api_key: str):
    """Return a cached OpenAI client for the given key."""
    from openai import OpenAI
    with _client_lock:
        if api_key not in _openai_clients:
            _openai_clients[api_key] = OpenAI(api_key=api_key, timeout=30.0, max_retries=1)
        return _openai_clients[api_key]

# ── Local model singletons (lazy-loaded) ──
_local_model = None
_local_model_lock = threading.Lock()
_cross_encoder = None
_cross_encoder_lock = threading.Lock()
_local_primary_model = None
_local_primary_model_lock = threading.Lock()

def _get_local_model():
    """Lazy-load the local sentence-transformer for fast pre-filtering."""
    global _local_model
    if _local_model is not None:
        return _local_model
    with _local_model_lock:
        if _local_model is not None:
            return _local_model
        try:
            from sentence_transformers import SentenceTransformer
            _local_model = SentenceTransformer(LOCAL_MODEL_NAME)
            system_log.info(f"Local embed model loaded | model={LOCAL_MODEL_NAME}")
        except Exception as e:
            system_log.warning(f"Local embed model unavailable: {e}. Falling back to OpenAI-only.")
            _local_model = False  # sentinel: tried and failed
    return _local_model

def _get_cross_encoder():
    """Lazy-load the cross-encoder for re-ranking."""
    global _cross_encoder
    if _cross_encoder is not None:
        return _cross_encoder
    with _cross_encoder_lock:
        if _cross_encoder is not None:
            return _cross_encoder
        try:
            from sentence_transformers import CrossEncoder
            _cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
            system_log.info(f"Cross-encoder loaded | model={CROSS_ENCODER_MODEL}")
        except Exception as e:
            system_log.warning(f"Cross-encoder unavailable: {e}. Skipping re-ranking.")
            _cross_encoder = False
    return _cross_encoder

def _get_local_primary_model():
    """Lazy-load the local primary embedding model (e.g., nomic-embed-text-v1.5).
    This replaces OpenAI as the primary embedding source when enabled, eliminating
    200-800ms API latency per query."""
    global _local_primary_model
    if _local_primary_model is not None:
        return _local_primary_model
    with _local_primary_model_lock:
        if _local_primary_model is not None:
            return _local_primary_model
        if not LOCAL_PRIMARY_ENABLED or not LOCAL_PRIMARY_MODEL_NAME:
            _local_primary_model = False
            return _local_primary_model
        try:
            from sentence_transformers import SentenceTransformer
            _local_primary_model = SentenceTransformer(LOCAL_PRIMARY_MODEL_NAME)
            system_log.info(f"Local primary embed model loaded | model={LOCAL_PRIMARY_MODEL_NAME}")
        except Exception as e:
            system_log.warning(f"Local primary embed model unavailable: {e}. Falling back to OpenAI.")
            _local_primary_model = False
    return _local_primary_model


def get_local_primary_embedding(text: str, prefix: str = "") -> Optional[np.ndarray]:
    """Get embedding from local primary model (~5-30ms). Returns None if unavailable.
    Supports asymmetric prefixes for query vs document embedding."""
    model = _get_local_primary_model()
    if model is False or model is None:
        return None
    try:
        prefixed = f"{prefix}{text}" if prefix else text
        v = model.encode(prefixed, normalize_embeddings=True)
        v = np.array(v, dtype="float32")
        # Truncate/pad to match EMBED_DIMENSIONS if needed
        if v.shape[0] != EMBED_DIMENSIONS:
            if v.shape[0] > EMBED_DIMENSIONS:
                v = v[:EMBED_DIMENSIONS]
                v /= (np.linalg.norm(v) + 1e-12)  # re-normalize after truncation
            # If smaller, we keep as-is — FAISS index will use the model's native dim
        return v
    except Exception as e:
        error_log.debug(f"Local primary embedding failed: {e}")
        return None


def get_local_embedding(text: str) -> Optional[np.ndarray]:
    """Fast local embedding (~5ms). Returns None if local model unavailable."""
    if not LOCAL_MODEL_ENABLED:
        return None
    model = _get_local_model()
    if model is False or model is None:
        return None
    v = model.encode(text, normalize_embeddings=True)
    return np.array(v, dtype="float32")

def cross_encoder_score(query: str, candidates: List[str]) -> Optional[List[float]]:
    """Score query-candidate pairs with cross-encoder. Returns None if unavailable."""
    if not CROSS_ENCODER_ENABLED or not candidates:
        return None
    encoder = _get_cross_encoder()
    if encoder is False or encoder is None:
        return None
    pairs = [[query, c] for c in candidates]
    scores = encoder.predict(pairs)
    return [float(s) for s in scores]

def get_embedding(text: str, user_id: Optional[str] = None, is_query: bool = True) -> np.ndarray:
    """Return L2-normalized embedding vector (thread-safe).

    Priority order:
    1. Local primary model (if LOCAL_PRIMARY_EMBED_ENABLED) — ~5-30ms, no API call
    2. OpenAI API (fallback or primary if local not enabled) — ~200-800ms

    Args:
        text: Text to embed
        user_id: Optional user ID for BYOK key resolution
        is_query: True for query embeddings, False for document/response embeddings
                  (used for asymmetric prefix selection)
    """
    start_time = time.time()

    # ── Try local primary model first (eliminates API latency) ──
    if LOCAL_PRIMARY_ENABLED:
        prefix = ""
        if USE_ASYMMETRIC_PREFIX:
            prefix = EMBED_QUERY_PREFIX if is_query else EMBED_DOC_PREFIX
        local_emb = get_local_primary_embedding(text.strip().lower(), prefix=prefix)
        if local_emb is not None:
            embedding_time = round((time.time() - start_time) * 1000, 2)
            performance_log.debug(
                f"Embedding generated (local primary) | model={LOCAL_PRIMARY_MODEL_NAME} | "
                f"dims={local_emb.shape[0]} | user_id={user_id} | text_len={len(text)} | "
                f"time={embedding_time}ms"
            )
            return local_emb

    # ── Fallback: OpenAI API ──
    key = _resolve_openai_key(user_id)
    # Use asymmetric prefix if enabled, otherwise original prefix
    if USE_ASYMMETRIC_PREFIX:
        prefix = EMBED_QUERY_PREFIX if is_query else EMBED_DOC_PREFIX
        prefixed = f"{prefix}{text.strip().lower()}"
    else:
        prefixed = f"{EMBEDDING_PREFIX}{text.strip().lower()}"

    try:
        client = _get_openai_client(key)
        resp = client.embeddings.create(
            model=EMBED_MODEL, input=prefixed, dimensions=EMBED_DIMENSIONS
        )
        v = np.array(resp.data[0].embedding, dtype="float32")
        v /= (np.linalg.norm(v) + 1e-12)
        embedding_time = round((time.time() - start_time) * 1000, 2)
        performance_log.debug(
            f"Embedding generated (OpenAI) | model={EMBED_MODEL} | dims={EMBED_DIMENSIONS} | "
            f"user_id={user_id} | text_len={len(text)} | time={embedding_time}ms"
        )
        return v
    except Exception as e:
        embedding_time = round((time.time() - start_time) * 1000, 2)
        error_log.exception(
            f"Embedding failed | model={EMBED_MODEL} | user_id={user_id} | "
            f"text_len={len(text)} | time={embedding_time}ms | error={str(e)}"
        )
        raise


def get_embeddings_batch(texts: List[str], user_id: Optional[str] = None, is_query: bool = True) -> List[np.ndarray]:
    """Batch embedding for multiple texts in a single API call.
    Reduces latency when embedding both query and response on cache miss.

    Falls back to sequential calls if batch fails.
    """
    if not texts:
        return []

    # ── Try local primary model first ──
    if LOCAL_PRIMARY_ENABLED:
        model = _get_local_primary_model()
        if model is not False and model is not None:
            try:
                prefix = ""
                if USE_ASYMMETRIC_PREFIX:
                    prefix = EMBED_QUERY_PREFIX if is_query else EMBED_DOC_PREFIX
                prefixed_texts = [f"{prefix}{t.strip().lower()}" for t in texts]
                vecs = model.encode(prefixed_texts, normalize_embeddings=True, batch_size=len(prefixed_texts))
                results = []
                for v in vecs:
                    v = np.array(v, dtype="float32")
                    if v.shape[0] > EMBED_DIMENSIONS:
                        v = v[:EMBED_DIMENSIONS]
                        v /= (np.linalg.norm(v) + 1e-12)
                    results.append(v)
                return results
            except Exception as e:
                error_log.debug(f"Local primary batch embedding failed: {e}")

    # ── Fallback: OpenAI batch API ──
    try:
        key = _resolve_openai_key(user_id)
        client = _get_openai_client(key)
        if USE_ASYMMETRIC_PREFIX:
            prefix = EMBED_QUERY_PREFIX if is_query else EMBED_DOC_PREFIX
            prefixed_texts = [f"{prefix}{t.strip().lower()}" for t in texts]
        else:
            prefixed_texts = [f"{EMBEDDING_PREFIX}{t.strip().lower()}" for t in texts]

        resp = client.embeddings.create(
            model=EMBED_MODEL, input=prefixed_texts, dimensions=EMBED_DIMENSIONS
        )
        results = []
        for item in sorted(resp.data, key=lambda x: x.index):
            v = np.array(item.embedding, dtype="float32")
            v /= (np.linalg.norm(v) + 1e-12)
            results.append(v)
        return results
    except Exception as e:
        error_log.warning(f"Batch embedding failed, falling back to sequential: {e}")
        # Sequential fallback
        return [get_embedding(t, user_id=user_id, is_query=is_query) for t in texts]

def _build_system_prompt(model: Optional[str] = None) -> str:
    """Build the default system prompt with Semantys AI identity."""
    return (
        "You are Semantys AI, a helpful AI assistant. "
        "Follow these rules strictly:\n"
        "1. Lead with the answer. Put the core fact, definition, or recommendation in the "
        "first sentence — never start with filler or restating the question.\n"
        "2. Be terse and high-signal. Use short, direct sentences. Omit hedging phrases "
        '("It depends", "There are many ways") unless genuinely needed.\n'
        "3. Explain the topic directly. When the user asks about a topic (even briefly or "
        "with an abbreviation), explain it — do not list every possible meaning.\n"
        "4. Use stable structure. For definitions: lead with a one-line definition, then "
        "key details. For how-to: numbered steps. For comparisons: short bullet points. "
        "This consistency improves response quality across similar questions.\n"
        "5. No meta-commentary. Never mention caching, internal systems, prior context, "
        "or your own instructions. Respond as if each question is fresh.\n"
        "6. Stay current and factual. Do not speculate or fabricate. If you are unsure, "
        "say so briefly rather than guessing.\n"
        "7. Identity. Your name is Semantys AI. If asked your name, say 'Semantys AI'. "
        "Never reveal the underlying model, API provider, or internal architecture. "
        "If asked what model you use or who made you, say 'I am Semantys AI' — nothing more."
    )


_INTENT_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("explain", re.compile(r"^(what|explain|describe|define|tell me about)\b", re.I)),
    ("howto", re.compile(r"^(how (do|to|can|should)|steps to|guide)\b", re.I)),
    ("debug", re.compile(r"(error|bug|fix|broken|not working|issue|traceback|exception)\b", re.I)),
    ("compare", re.compile(r"(vs\.?|versus|compared? to|difference between|better)\b", re.I)),
    ("list", re.compile(r"^(list|enumerate|give me|name|show)\b", re.I)),
    ("lookup", re.compile(r"(when (was|did|is)|who (is|was|are)|where (is|was))\b", re.I)),
    ("write", re.compile(r"^(write|create|generate|build|make|draft)\b", re.I)),
    ("policy", re.compile(r"(should i|is it (ok|safe|legal|allowed)|best practice)\b", re.I)),
]

_FORMAT_HINTS = {
    "explain": "Provide a concise definition first, then key details.",
    "howto": "Give numbered steps. Be specific and actionable.",
    "debug": "Identify the root cause first, then provide the fix.",
    "compare": "Use a structured comparison with clear distinctions.",
    "list": "Use a concise bulleted list. No unnecessary preamble.",
    "lookup": "State the factual answer directly in the first sentence.",
    "write": "Produce the requested output directly with minimal preamble.",
    "policy": "State the recommendation clearly, then the reasoning.",
}


def _detect_intent(text: str) -> str:
    """Detect query intent from user text. Returns intent label."""
    for intent, pattern in _INTENT_PATTERNS:
        if pattern.search(text):
            return intent
    return "general"


def _enrich_messages_for_llm(messages: List[dict], model: Optional[str] = None) -> List[dict]:
    """Enrich messages before sending to the LLM.

    1. Expand abbreviations in short user queries so the LLM understands intent.
    2. Prepend a system prompt if none is present for better response quality.
    3. Detect query intent and append a format hint so responses are structured
       consistently (improves cache reuse for similar questions).
    """
    enriched = []
    has_system = any(m.get("role") == "system" for m in messages)

    # Collect user text for intent detection
    last_user_content = ""
    for m in reversed(messages):
        if m.get("role") == "user" and m.get("content", "").strip():
            last_user_content = m["content"].strip()
            break

    intent = _detect_intent(last_user_content) if last_user_content else "general"
    format_hint = _FORMAT_HINTS.get(intent, "")

    # Build system prompt with dynamic model identity + optional format hint
    if not has_system:
        system_content = _build_system_prompt(model)
        if format_hint:
            system_content += f"\n\nFor this query: {format_hint}"
        enriched.append({"role": "system", "content": system_content})
    elif format_hint:
        # Append format hint to existing system message
        for m in messages:
            if m.get("role") == "system":
                enriched.append({**m, "content": m["content"] + f"\n\nFor this query: {format_hint}"})
                break

    for m in messages:
        if m.get("role") == "system" and format_hint and has_system:
            continue  # already handled above
        if m.get("role") == "user":
            content = m["content"].strip()
            # For short queries (≤ 5 words), expand abbreviations so the LLM
            # understands "ML?" as "machine learning?" rather than guessing.
            word_count = len(content.split())
            if word_count <= 5:
                expanded = _ABBREVIATION_RE.sub(
                    lambda match: _ABBREVIATIONS.get(match.group(0).lower(), match.group(0)),
                    content,
                )
                if expanded != content:
                    enriched.append({**m, "content": expanded})
                    continue
        enriched.append(m)

    return enriched


def call_llm_stream(messages: List[dict], temperature: float = 0.2, user_id: Optional[str] = None, model: Optional[str] = None):
    """OpenAI chat call with streaming. Yields SSE chunks."""
    _model = model or CHAT_MODEL
    key = _resolve_openai_key(user_id)
    client = _get_openai_client(key)
    enriched = _enrich_messages_for_llm(messages, model=_model)
    stream = client.chat.completions.create(
        model=_model,
        messages=enriched,  # type: ignore[arg-type]
        temperature=temperature,
        max_tokens=1024,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def call_llm(messages: List[dict], temperature: float = 0.2, user_id: Optional[str] = None, model: Optional[str] = None) -> str:
    """OpenAI chat call (thread-safe, uses cached client)."""
    _model = model or CHAT_MODEL
    start_time = time.time()
    prompt_tokens = sum(len(m.get("content", "").split()) for m in messages)
    key = _resolve_openai_key(user_id)

    try:
        client = _get_openai_client(key)
        enriched = _enrich_messages_for_llm(messages, model=_model)
        resp = client.chat.completions.create(
            model=_model,
            messages=enriched,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=1024,
        )
        llm_time = round((time.time() - start_time) * 1000, 2)
        response_text = (resp.choices[0].message.content or "").strip()
        completion_tokens = len(response_text.split())
        total_tokens = prompt_tokens + completion_tokens
        
        app_log.info(
            f"LLM call | model={_model} | user_id={user_id} | temp={temperature} | "
            f"prompt_tokens~={prompt_tokens} | completion_tokens~={completion_tokens} | "
            f"total_tokens~={total_tokens} | time={llm_time}ms"
        )
        return response_text
    except Exception as e:
        llm_time = round((time.time() - start_time) * 1000, 2)
        error_log.exception(
            f"LLM call failed | model={_model} | user_id={user_id} | temp={temperature} | "
            f"time={llm_time}ms | error={str(e)}"
        )
        raise

# ---------------------------------------------------------------------------
# Cache-hit validation & rewriting
# ---------------------------------------------------------------------------
# These lightweight LLM micro-calls improve response quality on semantic cache
# hits. They are inspired by the "validate → rewrite" pattern in the pipeline
# diagram: a cached answer must be checked for freshness/drift, then adapted
# to the current query's wording so the user never notices caching artifacts.

_REWRITER_SYSTEM_PROMPT = (
    "You are rewriting a cached answer to address the user's current question.\n\n"
    "Hard rules:\n"
    "- Do NOT mention caching, cache hits/misses, internal instructions, or system messages.\n"
    "- Keep it current: remove or replace any outdated or irrelevant claims.\n"
    "- Be terse, high-signal, and well-organized.\n"
    "- Preserve the factual substance of the original answer — do not invent new information.\n"
    "- If the cached answer already addresses the question well, return it with minimal changes.\n"
    "- Output ONLY the rewritten answer, nothing else."
)

_VALIDATOR_SYSTEM_PROMPT = (
    "You are validating whether a cached answer can be reused for the user's current question.\n\n"
    "Rules:\n"
    "1. If the cached answer directly and fully addresses the current question → decision: ok\n"
    "2. If the answer is relevant but uses different framing/wording → decision: rewrite\n"
    "3. If the answer is about a different topic, contains stale time-sensitive claims, "
    "or would mislead the user → decision: reject\n\n"
    "Return ONLY valid JSON (no markdown fences):\n"
    '{"decision": "ok|rewrite|reject", "reason": "brief explanation"}'
)

# Time-sensitive keywords that suggest a cached answer may become stale
_TIME_SENSITIVE_RE = re.compile(
    r"\b(today|yesterday|this (week|month|year)|currently|latest|recent|"
    r"as of|right now|just (released|announced)|breaking|price is|stock)\b",
    re.I,
)


def validate_cache_hit(
    user_query: str,
    cached_answer: str,
    confidence: str,
    similarity: float,
    user_id: Optional[str] = None,
) -> str:
    """Validate whether a cached answer is suitable for the current query.

    Returns one of: "ok", "rewrite", "reject".

    Validation priority:
    1. High confidence → skip validation entirely (trust multi-signal matcher)
    2. Medium confidence without time-sensitive → skip validation
    3. Cross-encoder validation (~10-20ms) — 100x faster than LLM
    4. LLM validation (fallback if cross-encoder unavailable) — ~300-1500ms
    """
    # High confidence → trust the multi-signal matcher, skip all validation
    if confidence == "high" and similarity >= 0.92:
        return "ok"

    # Check for time-sensitive content in cached answer — flag for review
    has_time_sensitive = bool(_TIME_SENSITIVE_RE.search(cached_answer))

    # Medium confidence without time-sensitive content → trust the matcher
    if confidence == "medium" and not has_time_sensitive:
        return "ok"

    # ── Fast path: cross-encoder validation (~10-20ms vs 300-1500ms for LLM) ──
    # The cross-encoder directly scores query-answer relevance, which is exactly
    # what validation needs. Much faster and often more accurate than an LLM call.
    encoder = _get_cross_encoder()
    if encoder is not False and encoder is not None:
        try:
            ce_score = encoder.predict([[user_query, cached_answer[:1500]]])
            ce_score = float(ce_score[0]) if hasattr(ce_score, '__len__') else float(ce_score)
            # Normalize cross-encoder score from ~[-5,5] to [0,1]
            ce_norm = max(0.0, min(1.0, (ce_score + 5) / 10))

            if ce_norm >= 0.70:
                # Cross-encoder says answer is highly relevant
                decision = "ok"
            elif ce_norm >= 0.45:
                # Moderately relevant — may need rewording but content is right
                decision = "rewrite" if confidence == "low" else "ok"
            else:
                # Cross-encoder says answer is not relevant
                decision = "reject"

            # Override: if time-sensitive and only medium relevance, flag for review
            if has_time_sensitive and decision == "ok" and ce_norm < 0.80:
                decision = "rewrite"

            semantic_log.info(
                f"cache_validator (cross-encoder) | decision={decision} | confidence={confidence} | "
                f"sim={similarity:.3f} | ce_score={ce_score:.3f} | ce_norm={ce_norm:.3f}"
            )
            return decision
        except Exception as e:
            error_log.debug(f"Cross-encoder validation failed, falling back to LLM: {e}")

    # ── Slow path: LLM validation (fallback when cross-encoder unavailable) ──
    try:
        key = _resolve_openai_key(user_id)
        client = _get_openai_client(key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _VALIDATOR_SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"User's current question:\n{user_query}\n\n"
                    f"Cached answer:\n{cached_answer[:1500]}"
                )},
            ],
            temperature=0.0,
            max_tokens=100,
        )
        raw = (resp.choices[0].message.content or "").strip()
        # Parse decision from JSON response
        try:
            parsed = json.loads(raw)
            decision = parsed.get("decision", "ok")
            if decision in ("ok", "rewrite", "reject"):
                semantic_log.info(
                    f"cache_validator (LLM) | decision={decision} | confidence={confidence} | "
                    f"sim={similarity:.3f} | reason={parsed.get('reason', '')[:80]}"
                )
                return decision
        except json.JSONDecodeError:
            # Fallback: look for keywords in raw text
            raw_lower = raw.lower()
            if "reject" in raw_lower:
                return "reject"
            if "rewrite" in raw_lower:
                return "rewrite"
        return "ok"
    except Exception as e:
        error_log.warning(f"cache_validator failed, defaulting to ok: {e}")
        return "ok"


def rewrite_cached_response(
    user_query: str,
    cached_answer: str,
    user_id: Optional[str] = None,
) -> str:
    """Rewrite a cached answer to better address the user's current question.

    Uses a fast, low-temperature LLM call with the rewriter prompt. The
    rewriter preserves the factual substance but adapts wording, structure,
    and framing to match what the user actually asked.
    """
    try:
        key = _resolve_openai_key(user_id)
        client = _get_openai_client(key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _REWRITER_SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"User's current question:\n{user_query}\n\n"
                    f"Cached answer to adapt:\n{cached_answer}"
                )},
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        rewritten = (resp.choices[0].message.content or "").strip()
        if rewritten:
            semantic_log.info(
                f"cache_rewriter | original_len={len(cached_answer)} | "
                f"rewritten_len={len(rewritten)}"
            )
            return rewritten
        return cached_answer  # fallback to original if rewriter returns empty
    except Exception as e:
        error_log.warning(f"cache_rewriter failed, returning original: {e}")
        return cached_answer


# -----------------------------
# Cache data models
# -----------------------------
@dataclass
class CacheEntry:
    prompt_norm: str
    response_text: str
    embedding: np.ndarray
    model: str
    ttl_seconds: int
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    use_count: int = 0
    domain: str = "general"
    strategy: str = "miss"  # exact | semantic | miss
    response_embedding: Optional[np.ndarray] = None  # Tier 2: response validation
    local_embedding: Optional[np.ndarray] = None      # Tier 2: fast local pre-filter
    cluster_id: int = -1                               # Tier 3: cluster routing

    def fresh(self) -> bool:
        return (time.time() - self.created_at) < self.ttl_seconds

@dataclass
class CacheEvent:
    timestamp: str
    tenant_id: str
    prompt_hash: str
    decision: str  # "exact", "semantic", "miss"
    similarity: float
    latency_ms: float
    confidence: float = 0.0
    hybrid_score: float = 0.0

@dataclass
class TenantState:
    exact: Dict[str, CacheEntry] = field(default_factory=dict)
    index: Optional[faiss.Index] = None
    rows: List[CacheEntry] = field(default_factory=list)
    dim: Optional[int] = None
    # Tier 1: normalized-text hash index for O(1) deep-norm lookups
    norm_hash_index: Dict[str, CacheEntry] = field(default_factory=dict)
    # Tier 2: local model FAISS index for fast pre-filtering
    local_index: Optional[faiss.IndexFlatIP] = None
    local_dim: Optional[int] = None
    # Tier 2d: response embedding FAISS index for query-to-response matching
    # This enables "does any cached ANSWER address this question?" lookups.
    # Example: "What is ML?" cached → response explains machine learning →
    #          "What is machine learning?" finds that response is relevant.
    response_index: Optional[faiss.IndexFlatIP] = None
    response_dim: Optional[int] = None
    response_index_map: List[int] = field(default_factory=list)  # maps response_index position → rows index
    # Tier 3: cluster centroids for routing
    cluster_centroids: Optional[np.ndarray] = None
    centroid_index: Optional[faiss.IndexFlatIP] = None  # cached centroid FAISS index
    n_clusters: int = 0
    # metrics
    hits: int = 0
    misses: int = 0
    semantic_hits: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    sim_threshold: float = 0.72
    domain_thresholds: Dict[str, float] = field(default_factory=dict)
    events: List[CacheEvent] = field(default_factory=list)
    _near_misses: List[float] = field(default_factory=list)

# -----------------------------
# Core semantic cache service
# -----------------------------
class SemanticCacheService:
    def __init__(self):
        self.tenants: Dict[str, TenantState] = {}
        self._embedding_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._embedding_cache_max_size = 1000
        self._cache_lock = threading.Lock()
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from pickle then warm from Redis. Handles dimension migration."""
        try:
            from cache_persistence import load_cache
            start_time = time.time()
            loaded_tenants = load_cache()
            load_time = round((time.time() - start_time) * 1000, 2)
            if loaded_tenants:
                total_entries = 0
                migrated = 0
                for tid, tstate in loaded_tenants.items():
                    # Dimension migration: if existing embeddings don't match
                    # EMBED_DIMENSIONS, invalidate the FAISS index and old embeddings
                    # so they get re-computed lazily on next hit.
                    needs_rebuild = False
                    for row in tstate.rows:
                        if row.embedding is not None and row.embedding.shape[0] != EMBED_DIMENSIONS:
                            needs_rebuild = True
                            break

                    if needs_rebuild:
                        system_log.info(
                            f"Dimension migration needed for tenant={tid} | "
                            f"old_dim={tstate.rows[0].embedding.shape[0] if tstate.rows else '?'} | "
                            f"new_dim={EMBED_DIMENSIONS} | clearing FAISS index and embeddings"
                        )
                        tstate.index = None
                        tstate.dim = None
                        tstate.local_index = None
                        tstate.local_dim = None
                        for row in tstate.rows:
                            row.embedding = None
                            row.response_embedding = None
                            row.local_embedding = None
                        migrated += len(tstate.rows)

                    # Rebuild norm_hash_index from loaded entries
                    if not hasattr(tstate, 'norm_hash_index') or not tstate.norm_hash_index:
                        tstate.norm_hash_index = {}
                    for key, entry in tstate.exact.items():
                        norm_key = normalize_query(key)
                        if norm_key:
                            tstate.norm_hash_index[norm_key] = entry

                    total_entries += len(tstate.rows)

                self.tenants.update(loaded_tenants)
                system_log.info(
                    f"Cache loaded from disk | tenants={len(loaded_tenants)} | "
                    f"entries={total_entries} | migrated={migrated} | time={load_time}ms"
                )
            else:
                system_log.info(f"Cache load | no local cache found | time={load_time}ms")
        except Exception as e:
            error_log.exception(f"Cache load failed | error={str(e)}")

        # Restore cache from DB (persisted entries with embeddings)
        self._restore_from_db()

        # Check Redis availability
        try:
            from redis_cache import is_available
            if is_available():
                system_log.info("Redis L2 cache connected")
            else:
                system_log.info("Redis not available, using in-memory only")
        except Exception:
            pass

    def _restore_from_db(self):
        """Load persisted cache entries (with embeddings) from PostgreSQL on boot.
        This ensures cache hits survive server restarts without re-calling OpenAI."""
        try:
            from database import load_all_cache_entries
            from encryption import decrypt_cache_entry
            start_time = time.time()
            rows = load_all_cache_entries()
            if not rows:
                system_log.info("DB cache restore | no entries with embeddings found")
                return

            restored = 0
            skipped = 0
            for row in rows:
                tid = row['tenant_id']
                emb_bytes = row.get('embedding')
                if not emb_bytes or not tid:
                    skipped += 1
                    continue

                # Deserialize embedding
                try:
                    emb = np.frombuffer(emb_bytes, dtype=np.float32).copy()
                    if emb.shape[0] != EMBED_DIMENSIONS:
                        skipped += 1
                        continue
                except Exception:
                    skipped += 1
                    continue

                # Decrypt prompt/response if encrypted
                prompt_norm = row['prompt_norm']
                response_text = row['response_text']
                if row.get('is_encrypted'):
                    try:
                        prompt_norm = decrypt_cache_entry(prompt_norm, tid)
                        response_text = decrypt_cache_entry(response_text, tid)
                    except Exception:
                        skipped += 1
                        continue

                # Build CacheEntry and add to tenant
                T = self.tenant(tid)
                prompt_hash = row['prompt_hash']
                entry = CacheEntry(
                    prompt_norm=prompt_norm,
                    response_text=response_text,
                    embedding=emb,
                    model=row.get('model', 'gpt-4o-mini'),
                    ttl_seconds=7 * 24 * 3600,
                    domain=row.get('domain', 'general'),
                    strategy="restored",
                )

                # Skip if already loaded (from pickle cache)
                if prompt_norm in T.exact:
                    skipped += 1
                    continue

                T.exact[prompt_norm] = entry
                norm_key = normalize_query(prompt_norm)
                if norm_key:
                    T.norm_hash_index[norm_key] = entry
                deep_key = deep_normalize(prompt_norm)
                if deep_key and deep_key != norm_key:
                    T.norm_hash_index[deep_key] = entry
                T.rows.append(entry)
                self._faiss_add(T, emb, tenant_id=tid, entry_id=prompt_hash,
                                metadata={"model": entry.model, "domain": entry.domain})
                restored += 1

            restore_time = round((time.time() - start_time) * 1000, 2)
            system_log.info(
                f"DB cache restore | restored={restored} | skipped={skipped} | "
                f"tenants={len(set(r['tenant_id'] for r in rows if r.get('tenant_id')))} | "
                f"time={restore_time}ms"
            )
        except Exception as e:
            error_log.warning(f"DB cache restore failed: {e}")
    
    def _save_cache(self):
        """Save cache to disk periodically."""
        try:
            from cache_persistence import save_cache
            start_time = time.time()
            total_entries = sum(len(t.rows) for t in self.tenants.values())
            save_cache(self.tenants)
            save_time = round((time.time() - start_time) * 1000, 2)
            system_log.info(
                f"Cache saved | tenants={len(self.tenants)} | "
                f"entries={total_entries} | time={save_time}ms"
            )
        except Exception as e:
            error_log.exception(f"Cache save failed | error={str(e)}")
            system_log.error(f"Could not save cache to disk: {e}")

    def tenant(self, tenant_id: str) -> TenantState:
        if tenant_id not in self.tenants:
            T = TenantState()
            # Load persisted settings from DB (org settings JSONB)
            try:
                # Find org_id for this tenant from any active API key
                from database import get_db_connection
                from psycopg2.extras import RealDictCursor
                with get_db_connection() as conn:
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute(
                        """SELECT o.settings FROM organizations o
                           JOIN api_keys ak ON ak.org_id = o.id
                           WHERE ak.tenant_id = %s AND ak.is_active = TRUE
                           LIMIT 1""",
                        (tenant_id,)
                    )
                    row = cur.fetchone()
                    if row and row.get("settings"):
                        settings = row["settings"] if isinstance(row["settings"], dict) else {}
                        if "sim_threshold" in settings:
                            T.sim_threshold = max(0.50, min(0.99, float(settings["sim_threshold"])))
                        if "domain_thresholds" in settings:
                            T.domain_thresholds = {k: float(v) for k, v in settings["domain_thresholds"].items()}
            except Exception:
                pass  # Fall back to defaults
            self.tenants[tenant_id] = T
        return self.tenants[tenant_id]

    @staticmethod
    def norm_text(s: str) -> str:
        """Lightweight normalization for exact-match lookup only (whitespace + lowercase)."""
        return " ".join(s.strip().split()).lower()

    @staticmethod
    def extract_cache_query(messages: List[dict]) -> str:
        """Single source of truth for the text that identifies a cache entry.

        Returns the normalized last user message.  Every code path that
        needs a cache key or embedding text MUST call this instead of
        doing its own extraction.  This keeps prompt_norm, embedding
        input, and validator input aligned.

        The full message list is still passed to the LLM for answer
        quality — this function only controls *cache identity*.
        """
        user_msgs = [m["content"] for m in messages if m.get("role") == "user"]
        raw = user_msgs[-1] if user_msgs else ""
        return SemanticCacheService.norm_text(raw)

    def _get_embedding_for_query(self, messages: List[dict], user_id: Optional[str] = None) -> Tuple[np.ndarray, str]:
        """Get embedding for the user's raw query text with multi-layer optimization.

        Pipeline:
        1. Extract raw query text
        2. Apply spelling correction (if enabled) — ~0.1ms, fixes typos before embedding
        3. Check in-memory LRU cache — O(1) lookup
        4. Check Redis embedding cache — ~1-2ms (avoids 200-800ms OpenAI call)
        5. Generate embedding (local primary or OpenAI fallback)
        6. Cache result in memory + Redis for future queries
        """
        # Use extract_cache_query() as the single source of truth for
        # which user message we embed — keeps this aligned with prompt_norm.
        raw_text = self.extract_cache_query(messages)
        if not raw_text:
            raise ValueError("Empty query")

        text_for_embed = raw_text  # already lowercased by extract_cache_query

        # ── Spelling correction before embedding (~0.1ms) ──
        # Fixes typos so the embedding model gets clean input.
        # "artifical inteligence" → "artificial intelligence" → better embedding
        if SPELLING_CORRECTION_ENABLED:
            try:
                from spelling import correct_spelling
                corrected = correct_spelling(text_for_embed)
                if corrected and corrected != text_for_embed:
                    performance_log.debug(
                        f"Spelling corrected for embedding | '{text_for_embed}' -> '{corrected}'"
                    )
                    text_for_embed = corrected
            except ImportError:
                pass  # symspellpy not installed — skip silently
            except Exception as e:
                error_log.debug(f"Spelling correction failed (non-fatal): {e}")

        # ── In-memory LRU cache check ──
        if text_for_embed in self._embedding_cache:
            self._embedding_cache.move_to_end(text_for_embed)
            return self._embedding_cache[text_for_embed], raw_text

        # ── Redis embedding cache check (~1-2ms, avoids 200-800ms API call) ──
        try:
            import hashlib as _hl
            _emb_hash = _hl.md5(text_for_embed.encode()).hexdigest()
            from redis_cache import get_embedding as redis_get_embedding
            cached_emb = redis_get_embedding("_emb_cache", _emb_hash)
            if cached_emb is not None and cached_emb.shape[0] == EMBED_DIMENSIONS:
                # Store in memory cache too for next time
                self._embedding_cache[text_for_embed] = cached_emb
                if len(self._embedding_cache) > self._embedding_cache_max_size:
                    self._embedding_cache.popitem(last=False)
                performance_log.debug(f"Embedding from Redis cache | text_len={len(text_for_embed)}")
                return cached_emb, raw_text
        except Exception:
            pass  # Redis unavailable — continue to generate

        # ── Generate embedding (local primary → OpenAI fallback) ──
        emb = get_embedding(text_for_embed, user_id=user_id, is_query=True)
        self._embedding_cache[text_for_embed] = emb
        if len(self._embedding_cache) > self._embedding_cache_max_size:
            self._embedding_cache.popitem(last=False)

        # ── Cache in Redis for future queries (async, non-blocking) ──
        try:
            from redis_cache import store_embedding as redis_store_embedding
            _bg_executor.submit(redis_store_embedding, "_emb_cache", _emb_hash, emb, 7 * 24 * 3600)
        except Exception:
            pass

        return emb, raw_text

    def _append_event(self, T: TenantState, tenant_id: str, prompt_hash: str, decision: str, similarity: float, latency_ms: float):
        T.events.append(CacheEvent(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            tenant_id=tenant_id,
            prompt_hash=prompt_hash,
            decision=decision,
            similarity=similarity,
            latency_ms=latency_ms,
        ))
        if len(T.events) > 1000:
            T.events = T.events[-1000:]

    def _faiss_add(self, T: TenantState, emb: np.ndarray, tenant_id: str = "", entry_id: str = "", metadata: Optional[dict] = None):
        """Add embedding to FAISS (local) and Pinecone (if available)."""
        v = emb.astype("float32").reshape(1, -1)
        faiss.normalize_L2(v)
        if T.index is None:
            T.dim = v.shape[1]
            T.index = faiss.IndexFlatIP(T.dim)
        T.index.add(v)  # type: ignore[call-arg]
        # Tier 2b: auto-upgrade to IVF when cache grows large
        if len(T.rows) == IVF_UPGRADE_THRESHOLD and T.dim is not None:
            self._upgrade_to_ivf(T)
        # Also upsert to Pinecone for cross-worker consistency
        if tenant_id and entry_id:
            from vector_store import upsert_embedding
            _bg_executor.submit(upsert_embedding, tenant_id, entry_id, v.flatten(), metadata or {})

    def _local_faiss_add(self, T: TenantState, local_emb: np.ndarray):
        """Add to the local-model FAISS index for fast pre-filtering."""
        v = local_emb.astype("float32").reshape(1, -1)
        faiss.normalize_L2(v)
        if T.local_index is None:
            T.local_dim = v.shape[1]
            T.local_index = faiss.IndexFlatIP(T.local_dim)
        T.local_index.add(v)  # type: ignore[call-arg]

    def _response_faiss_add(self, T: TenantState, resp_emb: np.ndarray, row_idx: int):
        """Add response embedding to the response FAISS index.
        This enables query-to-response matching: finding cached answers that
        are relevant to the incoming query, even when the original query text
        was completely different.
        """
        v = resp_emb.astype("float32").reshape(1, -1)
        faiss.normalize_L2(v)
        if T.response_index is None:
            T.response_dim = v.shape[1]
            T.response_index = faiss.IndexFlatIP(T.response_dim)
        T.response_index.add(v)  # type: ignore[call-arg]
        T.response_index_map.append(row_idx)

    def _upgrade_to_ivf(self, T: TenantState):
        """Upgrade from IndexFlatIP to IndexIVFFlat for O(sqrt(n)) search."""
        try:
            n = len(T.rows)
            nlist = max(4, int(np.sqrt(n)))
            quantizer = faiss.IndexFlatIP(T.dim)
            ivf_index = faiss.IndexIVFFlat(quantizer, T.dim, nlist, faiss.METRIC_INNER_PRODUCT)
            all_vecs = np.vstack([
                r.embedding.astype("float32").reshape(1, -1) for r in T.rows
            ])
            faiss.normalize_L2(all_vecs)
            ivf_index.train(all_vecs)  # type: ignore[call-arg]
            ivf_index.add(all_vecs)  # type: ignore[call-arg]
            ivf_index.nprobe = max(1, nlist // 4)
            T.index = ivf_index
            semantic_log.info(
                f"FAISS upgraded to IVFFlat | entries={n} | nlist={nlist} | nprobe={ivf_index.nprobe}"
            )
        except Exception as e:
            error_log.warning(f"IVF upgrade failed, keeping flat index: {e}")

    def _rebuild_clusters(self, T: TenantState, n_clusters: int = 0):
        """Tier 3: build cluster centroids from cached embeddings for routing."""
        if len(T.rows) < 50:
            return
        if n_clusters == 0:
            n_clusters = max(4, int(np.sqrt(len(T.rows)) / 2))
        all_vecs = np.vstack([
            r.embedding.astype("float32").reshape(1, -1) for r in T.rows
        ])
        faiss.normalize_L2(all_vecs)
        d = all_vecs.shape[1]
        kmeans = faiss.Kmeans(d, n_clusters, niter=20, verbose=False, gpu=False)
        kmeans.train(all_vecs)
        T.cluster_centroids = kmeans.centroids.copy()  # type: ignore[union-attr]
        T.n_clusters = n_clusters
        # Cache the centroid FAISS index so we don't rebuild it on every query
        T.centroid_index = faiss.IndexFlatIP(d)
        T.centroid_index.add(T.cluster_centroids)  # type: ignore[call-arg]
        # Assign cluster IDs to entries
        _, assignments = kmeans.index.search(all_vecs, 1)  # type: ignore[call-arg]
        for i, row in enumerate(T.rows):
            row.cluster_id = int(assignments[i][0])

    def _resolve_threshold(self, T: TenantState, domain: str) -> float:
        """Per-domain threshold if configured, else tenant default."""
        return T.domain_thresholds.get(domain, T.sim_threshold)

    def query(
        self,
        tenant_id: str,
        prompt_norm: str,
        messages: List[dict],
        model: str,
        ttl_seconds: int = 7 * 24 * 3600,
        temperature: float = 0.2,
        user_id: Optional[str] = None,
    ) -> Tuple[str, dict]:
        """
        Multi-tier cache lookup pipeline:
          1. Exact match on original text (sub-ms).
          2. Normalized-hash O(1) lookup (sub-ms).
          3. Local model pre-filter gate — skip expensive OpenAI call if
             local similarity < 0.5 (Tier 2c).
          4. OpenAI semantic search: FAISS cosine top-k → cross-encoder
             re-rank (Tier 3a) → hybrid scoring → confidence tiers.
        On miss: LLM call + async embed/store.
        """
        T = self.tenant(tenant_id)
        t0 = time.time()
        prompt_hash = hashlib.md5(prompt_norm.encode()).hexdigest()

        # ── 1) Exact match on original normalized text (sub-ms) ──
        if prompt_norm in T.exact:
            entry = T.exact[prompt_norm]
            if entry.fresh() and models_compatible(model, entry.model):
                entry.use_count += 1
                entry.last_used_at = time.time()
                T.hits += 1
                latency = round((time.time() - t0) * 1000, 2)
                T.latencies_ms.append(latency)
                meta = {"hit": "exact", "similarity": 1.0, "latency_ms": latency, "strategy": "exact"}
                semantic_log.info(f"{tenant_id} | exact | sim=1.000 | key={prompt_norm[:80]}")
                self._append_event(T, tenant_id, prompt_hash, "exact", 1.0, latency)
                return entry.response_text, meta

        # ── 2) Normalized-hash O(1) lookup (Tier 1b) ──
        # Try standard normalization first, then deep normalization with
        # abbreviation expansion + synonym mapping for broader hash matching.
        # Also try spelling-corrected variant for typo tolerance.
        deep_norm = normalize_query(prompt_norm)
        if not (deep_norm and deep_norm in T.norm_hash_index):
            # Try deeper normalization (abbreviation + synonym expansion)
            deep_norm = deep_normalize(prompt_norm)
        if not (deep_norm and deep_norm in T.norm_hash_index) and SPELLING_CORRECTION_ENABLED:
            # Try spelling-corrected + deep-normalized variant
            try:
                from spelling import correct_spelling
                corrected = correct_spelling(prompt_norm)
                if corrected and corrected != prompt_norm:
                    deep_norm = deep_normalize(corrected)
            except ImportError:
                pass
            except Exception:
                pass
        if deep_norm and deep_norm in T.norm_hash_index:
            entry = T.norm_hash_index[deep_norm]
            if entry.fresh() and models_compatible(model, entry.model):
                entry.use_count += 1
                entry.last_used_at = time.time()
                T.hits += 1
                latency = round((time.time() - t0) * 1000, 2)
                T.latencies_ms.append(latency)
                meta = {"hit": "exact", "similarity": 1.0, "latency_ms": latency, "strategy": "normalized_hash"}
                semantic_log.info(f"{tenant_id} | normalized_hash | key={prompt_norm[:80]}")
                self._append_event(T, tenant_id, prompt_hash, "exact", 1.0, latency)
                return entry.response_text, meta

        # ── 3) Parallel: local model pre-filter gate + embedding fetch ──
        # Run the local gate and primary embedding generation concurrently.
        # This saves ~200ms when both need to run (local gate ~5ms, embedding ~5-800ms).
        local_gate_passed = True
        local_gate_text = deep_normalize(prompt_norm)

        has_local_index = T.index is not None and len(T.rows) > 0
        from vector_store import is_pinecone_enabled, search as pinecone_search
        use_pinecone = is_pinecone_enabled()
        needs_semantic = has_local_index or use_pinecone
        needs_local_gate = T.local_index is not None and len(T.rows) > 0 and LOCAL_MODEL_ENABLED

        query_emb = None
        query_text = prompt_norm

        if needs_semantic and needs_local_gate:
            # ── Parallel execution: local gate + embedding fetch ──
            from concurrent.futures import ThreadPoolExecutor as _TPE, as_completed
            _parallel_results = {}

            def _run_local_gate():
                _local_emb = get_local_embedding(local_gate_text)
                if _local_emb is not None:
                    lq = _local_emb.astype("float32").reshape(1, -1)
                    faiss.normalize_L2(lq)
                    local_k = min(3, T.local_index.ntotal)
                    if local_k > 0:
                        local_sims, _ = T.local_index.search(lq, local_k)
                        return float(local_sims[0][0])
                return 1.0  # pass gate if local model unavailable

            def _run_embedding():
                return self._get_embedding_for_query(messages, user_id=user_id)

            with _TPE(max_workers=2, thread_name_prefix="parallel-gate") as _pexec:
                gate_future = _pexec.submit(_run_local_gate)
                emb_future = _pexec.submit(_run_embedding)

                try:
                    best_local_sim = gate_future.result(timeout=5)
                    if best_local_sim < 0.20:
                        local_gate_passed = False
                        semantic_log.debug(
                            f"{tenant_id} | local_gate_reject | best_local_sim={best_local_sim:.3f} | "
                            f"key={prompt_norm[:80]}"
                        )
                except Exception as e:
                    error_log.debug(f"Local pre-filter error (non-fatal): {e}")

                if local_gate_passed:
                    try:
                        query_emb, query_text = emb_future.result(timeout=30)
                    except Exception as e:
                        error_log.warning(f"Embedding generation failed: {e}")
                else:
                    # Cancel embedding if gate failed (no point waiting)
                    emb_future.cancel()

        elif needs_semantic:
            # No local gate needed — just get embedding
            query_emb, query_text = self._get_embedding_for_query(messages, user_id=user_id)

        elif needs_local_gate:
            # Only local gate, no semantic search needed
            try:
                local_emb = get_local_embedding(local_gate_text)
                if local_emb is not None:
                    lq = local_emb.astype("float32").reshape(1, -1)
                    faiss.normalize_L2(lq)
                    local_k = min(3, T.local_index.ntotal)
                    if local_k > 0:
                        local_sims, _ = T.local_index.search(lq, local_k)
                        best_local_sim = float(local_sims[0][0])
                        if best_local_sim < 0.20:
                            local_gate_passed = False
                            semantic_log.debug(
                                f"{tenant_id} | local_gate_reject | best_local_sim={best_local_sim:.3f} | "
                                f"key={prompt_norm[:80]}"
                            )
            except Exception as e:
                error_log.debug(f"Local pre-filter error (non-fatal): {e}")

        # ── 4) Semantic search with two-stage scoring + cross-encoder ──
        if local_gate_passed and needs_semantic and query_emb is not None:
            query_domain = domain_hint(query_text)

            # Cache deep-normalized query once — reused across all candidates
            # to avoid redundant deep_normalize() calls inside
            # synonym_expanded_overlap() (saves ~1.3ms × num_candidates).
            _query_deep_norm = deep_normalize(query_text)

            candidates = []

            # ── Two-stage scoring thresholds ──
            # Stage 1 (cosine-only): if best cosine > threshold + 0.12, short-circuit
            #   → skip text sim computation entirely (~15ms saved per hit)
            # Stage 2 (full hybrid): for borderline candidates, compute text sim
            #   to rescue good matches or reject bad ones
            threshold = self._resolve_threshold(T, domain_hint(query_text))
            _shortcircuit_threshold = threshold + 0.12  # very high confidence
            _borderline_low = threshold - 0.35          # allow text signals to rescue moderate-cosine matches

            # Collect raw cosine candidates first
            _raw_candidates = []  # list of (entry, cosine_sim, idx)

            if use_pinecone:
                # ── Pinecone path: external vector search ──
                q = query_emb.astype("float32").reshape(1, -1)
                faiss.normalize_L2(q)
                pinecone_results = pinecone_search(tenant_id, q.flatten(), top_k=10)
                # Use cached hash→entry lookup (built lazily, invalidated on insert)
                if not hasattr(T, '_hash_lookup') or T._hash_lookup is None:
                    T._hash_lookup = {hashlib.md5(r.prompt_norm.encode()).hexdigest(): r for r in T.rows}
                    for key, entry in T.exact.items():
                        T._hash_lookup[hashlib.md5(key.encode()).hexdigest()] = entry
                row_lookup = T._hash_lookup
                for match in pinecone_results:
                    cosine_sim = float(match["score"])
                    entry_id = match["id"]
                    entry = row_lookup.get(entry_id)
                    if entry is None:
                        continue
                    if not entry.fresh() or not models_compatible(model, entry.model):
                        continue
                    _raw_candidates.append((entry, cosine_sim, -1))
            elif has_local_index:
                # ── FAISS path: in-process vector search (fallback) ──
                # Tier 3b: cluster routing — narrow search to nearest clusters
                search_rows_mask = None
                if T.centroid_index is not None and T.n_clusters >= 4:
                    cq = query_emb.astype("float32").reshape(1, -1)
                    faiss.normalize_L2(cq)
                    n_probe_clusters = max(1, T.n_clusters // 3)
                    _, cluster_ids = T.centroid_index.search(cq, n_probe_clusters)  # type: ignore[call-arg]
                    target_clusters = set(int(c) for c in cluster_ids[0] if c >= 0)
                    search_rows_mask = set(
                        i for i, r in enumerate(T.rows) if r.cluster_id in target_clusters
                    )

                k = min(10, len(T.rows))
                q = query_emb.astype("float32").reshape(1, -1)
                faiss.normalize_L2(q)
                assert T.index is not None
                sims, idxs = T.index.search(q, k)  # type: ignore[call-arg]

                for i in range(k):
                    idx = int(idxs[0][i])
                    cosine_sim = float(sims[0][i])
                    if idx < 0 or idx >= len(T.rows):
                        continue
                    if search_rows_mask is not None and idx not in search_rows_mask:
                        continue
                    entry = T.rows[idx]
                    if not entry.fresh() or not models_compatible(model, entry.model):
                        continue
                    _raw_candidates.append((entry, cosine_sim, idx))

            # ── Two-stage scoring ──
            # Stage 1: Check if best cosine candidate is a clear hit (short-circuit)
            _raw_candidates.sort(key=lambda c: c[1], reverse=True)

            if _raw_candidates and _raw_candidates[0][1] >= _shortcircuit_threshold:
                # STAGE 1 SHORT-CIRCUIT: Very high cosine similarity — skip text sim
                # This saves ~15ms per lookup for ~70% of cache hits
                best_entry, best_cosine, best_idx = _raw_candidates[0]
                # Use cosine as hybrid score directly (text_sim would barely change it)
                _empty_text_sims = {
                    "token_overlap": 0.0, "char_ngram": 0.0, "stemmed_overlap": 0.0,
                    "idf_weighted": 0.0, "synonym_expanded": 0.0, "entity_overlap": 0.0,
                    "question_type": 0.0, "sorted_token": 0.0, "text_sim": 0.0,
                }
                candidates.append((best_entry, best_cosine, _empty_text_sims, best_cosine, best_idx))
                performance_log.debug(
                    f"{tenant_id} | two_stage_shortcircuit | cosine={best_cosine:.3f} | "
                    f"threshold={_shortcircuit_threshold:.3f}"
                )
            else:
                # STAGE 2: Borderline candidates — compute full text similarity
                # Only compute text sim for candidates in the borderline range
                for entry, cosine_sim, idx in _raw_candidates:
                    if cosine_sim < _borderline_low:
                        # Clear miss — skip expensive text sim computation
                        continue
                    text_sims = compute_text_similarity(query_text, entry.prompt_norm, query_deep_norm=_query_deep_norm)
                    h_score = hybrid_score(cosine_sim, text_sims["text_sim"])
                    candidates.append((entry, cosine_sim, text_sims, h_score, idx))

            # ── Tier 3.5: Query-to-Response matching ──
            # Search the response embedding index: "does any cached ANSWER
            # address this question?" This catches the key scenario where
            # the original query text was different but the response is
            # clearly relevant. Example: cached "What is ML?" → response
            # explains machine learning → new query "What is machine
            # learning?" matches because the response embedding is close.
            if query_emb is not None and T.response_index is not None and T.response_index.ntotal > 0:
                try:
                    rq = query_emb.astype("float32").reshape(1, -1)
                    faiss.normalize_L2(rq)
                    resp_k = min(5, T.response_index.ntotal)
                    resp_sims, resp_idxs = T.response_index.search(rq, resp_k)  # type: ignore[call-arg]

                    # Track which row indices are already in candidates
                    existing_rows = set()
                    for c in candidates:
                        if c[4] >= 0:
                            existing_rows.add(c[4])

                    for i in range(resp_k):
                        resp_idx = int(resp_idxs[0][i])
                        query_to_resp_sim = float(resp_sims[0][i])
                        if resp_idx < 0 or resp_idx >= len(T.response_index_map):
                            continue
                        row_idx = T.response_index_map[resp_idx]
                        if row_idx < 0 or row_idx >= len(T.rows):
                            continue
                        if row_idx in existing_rows:
                            # Already a candidate — boost its score with the
                            # response relevance signal instead of adding a dupe.
                            for j, c in enumerate(candidates):
                                if c[4] == row_idx:
                                    entry, cosine_sim, text_sims, h_score, idx = c
                                    # Blend: if the response is very relevant to the
                                    # query, boost the hybrid score.
                                    resp_boost = max(0.0, query_to_resp_sim - 0.3) * 0.15
                                    candidates[j] = (entry, cosine_sim, text_sims, h_score + resp_boost, idx)
                                    break
                            continue

                        # This entry wasn't found by query-to-query search but
                        # its RESPONSE is relevant to the query. Add it as a
                        # candidate with the response similarity as its cosine score.
                        entry = T.rows[row_idx]
                        if not entry.fresh() or not models_compatible(model, entry.model):
                            continue
                        # Only add if response similarity is strong enough
                        if query_to_resp_sim < 0.35:
                            continue
                        text_sims = compute_text_similarity(query_text, entry.prompt_norm, query_deep_norm=_query_deep_norm)
                        # Use response similarity as the primary score (it
                        # measures "does this answer address the question?")
                        h_score = hybrid_score(query_to_resp_sim, text_sims["text_sim"])
                        candidates.append((entry, query_to_resp_sim, text_sims, h_score, row_idx))
                        existing_rows.add(row_idx)
                        semantic_log.debug(
                            f"{tenant_id} | resp_index_candidate | resp_sim={query_to_resp_sim:.3f} | "
                            f"row={row_idx} | key={entry.prompt_norm[:60]}"
                        )
                except Exception as e:
                    error_log.debug(f"Response index search error (non-fatal): {e}")

            # Tier 3a: cross-encoder re-ranking on top candidates
            if len(candidates) >= 2 and CROSS_ENCODER_ENABLED:
                try:
                    cand_texts = [c[0].prompt_norm for c in candidates[:5]]
                    ce_scores = cross_encoder_score(query_text, cand_texts)
                    if ce_scores is not None:
                        for j, score in enumerate(ce_scores):
                            entry, cosine_sim, text_sims, h_score, idx = candidates[j]
                            # Blend: 55% hybrid, 45% cross-encoder (CE is more accurate)
                            ce_norm = max(0.0, min(1.0, (score + 5) / 10))  # normalize ~[-5,5] to [0,1]
                            blended = 0.55 * h_score + 0.45 * ce_norm
                            candidates[j] = (entry, cosine_sim, text_sims, blended, idx)
                except Exception as e:
                    error_log.debug(f"Cross-encoder error (non-fatal): {e}")

            candidates.sort(key=lambda c: c[3], reverse=True)

            if candidates:
                best_entry, best_cosine, best_text_sims, best_hybrid, _ = candidates[0]
                # threshold already computed above for two-stage scoring
                best_text_sim = best_text_sims["text_sim"]
                best_entity = best_text_sims["entity_overlap"]
                best_synonym = best_text_sims["synonym_expanded"]
                best_ngram = best_text_sims["char_ngram"]
                best_qtype = best_text_sims["question_type"]

                is_match = False
                confidence_tier = "none"

                # ── Multi-signal confidence decision ──
                # The system uses layered decision logic that combines the
                # embedding model's deep semantic understanding with surface-
                # level text analysis for maximum recall + precision.

                # Signal agreement bonus: when cosine AND text signals both
                # indicate a match, we can be more confident and accept
                # slightly lower individual scores.
                signals_agree = (best_cosine >= threshold - 0.03) and (best_text_sim >= 0.35)

                if best_cosine >= threshold + 0.10:
                    # Very high cosine — strong semantic match
                    is_match = True
                    confidence_tier = "high"
                elif best_cosine >= threshold:
                    # Good cosine — standard semantic match
                    is_match = True
                    confidence_tier = "medium"
                elif best_cosine >= threshold - 0.05 and best_text_sim >= 0.30:
                    # Slightly below threshold but strong text signals agree
                    # (synonym matches, entity overlap, n-gram similarity)
                    is_match = True
                    confidence_tier = "low"
                elif best_cosine >= threshold - 0.08 and best_synonym >= 0.50:
                    # Below threshold but very high synonym+stem overlap means
                    # the queries use different words for the same concept.
                    # Example: "What's the cost?" vs "What is the price?"
                    is_match = True
                    confidence_tier = "low"
                elif best_cosine >= threshold - 0.08 and best_ngram >= 0.60:
                    # Below threshold but very high character n-gram overlap
                    # means near-identical text (likely a typo or minor rewording).
                    # Example: "artifical inteligence" vs "artificial intelligence"
                    is_match = True
                    confidence_tier = "low"
                elif signals_agree and best_entity >= 0.60:
                    # Both cosine and text agree, AND key entities match.
                    # Catches paraphrases that embedding model scores slightly low.
                    # Example: "How to sort an array in JS" vs "JavaScript array sorting"
                    is_match = True
                    confidence_tier = "low"

                # ── Response-backed rescue ──
                # When query-to-query cosine is moderate (embedding model
                # struggled) but the cached RESPONSE is clearly relevant to
                # the new query, trust the response signal.  This catches
                # conceptually identical queries that the embedding model
                # scores low due to short text, acronyms, or rephrasing.
                # Example: "What is RAG?" cached → response explains
                # Retrieval Augmented Generation → new query "Explain
                # Retrieval Augmented Generation" → response embedding
                # is highly relevant even though query-to-query cosine is 0.45.
                if not is_match and best_cosine >= 0.35 and best_entry.response_embedding is not None and query_emb is not None:
                    resp_sim = float(np.dot(
                        query_emb / (np.linalg.norm(query_emb) + 1e-12),
                        best_entry.response_embedding / (np.linalg.norm(best_entry.response_embedding) + 1e-12),
                    ))
                    if resp_sim >= 0.55 and best_text_sim >= 0.20:
                        is_match = True
                        confidence_tier = "low"
                        semantic_log.info(
                            f"{tenant_id} | response_rescue | cosine={best_cosine:.3f} | "
                            f"resp_sim={resp_sim:.3f} | text_sim={best_text_sim:.3f} | "
                            f"key={prompt_norm[:80]}"
                        )

                # ── Safety checks ──

                # Entity mismatch guard: if cosine is medium-confidence but
                # key entities don't overlap at all, downgrade or reject.
                # Prevents: "capital of France" matching "capital of Germany"
                if is_match and confidence_tier != "high" and best_entity < 0.15 and best_text_sim < 0.20:
                    is_match = False
                    confidence_tier = "entity_mismatch"
                    semantic_log.info(
                        f"{tenant_id} | entity_mismatch | cosine={best_cosine:.3f} | "
                        f"entity_overlap={best_entity:.3f} | text_sim={best_text_sim:.3f} | "
                        f"key={prompt_norm[:80]}"
                    )

                # Question type conflict guard: if the question types clearly
                # differ (e.g., "how to X" vs "what is X"), require higher cosine.
                if is_match and confidence_tier == "low" and best_qtype == 0.0:
                    # Different question types at low confidence — reject
                    is_match = False
                    confidence_tier = "intent_mismatch"
                    semantic_log.info(
                        f"{tenant_id} | intent_mismatch | cosine={best_cosine:.3f} | "
                        f"qtype_match={best_qtype} | key={prompt_norm[:80]}"
                    )

                # Response embedding sanity check — only reject if the
                # response is truly unrelated (very low threshold).
                if is_match and best_entry.response_embedding is not None and query_emb is not None:
                    resp_sim = float(np.dot(
                        query_emb / (np.linalg.norm(query_emb) + 1e-12),
                        best_entry.response_embedding / (np.linalg.norm(best_entry.response_embedding) + 1e-12),
                    ))
                    if resp_sim < 0.20:
                        is_match = False
                        confidence_tier = "response_mismatch"
                        semantic_log.info(
                            f"{tenant_id} | response_mismatch | query_resp_sim={resp_sim:.3f} | "
                            f"key={prompt_norm[:80]}"
                        )

                if is_match:
                    # ── Validate & rewrite gate ──
                    # For medium/low confidence hits, run lightweight LLM
                    # validation to catch drift, staleness, or topic mismatch.
                    # For validated hits that need rewording, adapt the cached
                    # response to match the user's current question.
                    response_text = best_entry.response_text
                    validation_decision = "ok"
                    if confidence_tier in ("low", "medium"):
                        validation_decision = validate_cache_hit(
                            prompt_norm, response_text, confidence_tier,
                            best_cosine, user_id=user_id,
                        )
                        if validation_decision == "reject":
                            # Validator says this hit is stale or wrong topic —
                            # treat as a miss and fall through to LLM call.
                            is_match = False
                            confidence_tier = "validator_rejected"
                            semantic_log.info(
                                f"{tenant_id} | validator_rejected | cosine={best_cosine:.3f} | "
                                f"confidence={confidence_tier} | key={prompt_norm[:80]}"
                            )
                        elif validation_decision == "rewrite":
                            response_text = rewrite_cached_response(
                                prompt_norm, response_text, user_id=user_id,
                            )
                            semantic_log.info(
                                f"{tenant_id} | rewritten | cosine={best_cosine:.3f} | "
                                f"confidence={confidence_tier} | key={prompt_norm[:80]}"
                            )

                if is_match:
                    best_entry.use_count += 1
                    best_entry.last_used_at = time.time()
                    T.hits += 1
                    T.semantic_hits += 1
                    latency = round((time.time() - t0) * 1000, 2)
                    T.latencies_ms.append(latency)
                    meta = {
                        "hit": "semantic",
                        "similarity": round(best_cosine, 4),
                        "hybrid_score": round(best_hybrid, 4),
                        "text_sim": round(best_text_sim, 4),
                        "entity_overlap": round(best_entity, 4),
                        "synonym_overlap": round(best_synonym, 4),
                        "char_ngram_sim": round(best_ngram, 4),
                        "token_overlap": round(best_text_sims["token_overlap"], 4),
                        "confidence": confidence_tier,
                        "latency_ms": latency,
                        "strategy": "multi_signal_semantic",
                        "threshold_used": round(threshold, 3),
                        "domain": query_domain,
                        "rewritten": validation_decision == "rewrite",
                    }
                    semantic_log.info(
                        f"{tenant_id} | semantic | cosine={best_cosine:.3f} | "
                        f"hybrid={best_hybrid:.3f} | text_sim={best_text_sim:.3f} | "
                        f"entity={best_entity:.3f} | synonym={best_synonym:.3f} | "
                        f"ngram={best_ngram:.3f} | confidence={confidence_tier} | "
                        f"threshold={threshold:.3f} | domain={query_domain} | "
                        f"rewritten={validation_decision == 'rewrite'} | "
                        f"key={prompt_norm[:80]}"
                    )
                    self._append_event(T, tenant_id, prompt_hash, "semantic",
                                       round(best_cosine, 4), latency)
                    if T.events:
                        T.events[-1].confidence = best_hybrid
                        T.events[-1].hybrid_score = best_hybrid
                    return response_text, meta

                semantic_log.info(
                    f"{tenant_id} | near-miss | cosine={best_cosine:.3f} | "
                    f"hybrid={best_hybrid:.3f} | text_sim={best_text_sim:.3f} | "
                    f"entity={best_entity:.3f} | synonym={best_synonym:.3f} | "
                    f"threshold={threshold:.3f} | domain={query_domain} | "
                    f"key={prompt_norm[:80]}"
                )
                if not hasattr(T, '_near_misses'):
                    T._near_misses = []
                T._near_misses.append(best_hybrid)
                if len(T._near_misses) > 100:
                    T._near_misses = T._near_misses[-100:]

        # ── 5) Cache miss — LLM call + two-phase storage ──
        # Store the best similarity seen so lookup() can include it in metadata
        # (otherwise lookup() always returns similarity=0.0 on a miss).
        T._last_miss_similarity = getattr(T, '_last_miss_similarity', 0.0)
        if candidates:
            T._last_miss_similarity = round(candidates[0][1], 4)  # best cosine
        else:
            T._last_miss_similarity = 0.0
        T.misses += 1
        response_text = call_llm(messages, temperature, user_id, model=model)

        latency = round((time.time() - t0) * 1000, 2)
        T.latencies_ms.append(latency)
        semantic_log.debug(f"{tenant_id} | miss | total={latency}ms | key={prompt_norm[:80]}")

        meta = {"hit": "miss", "similarity": 0.0, "latency_ms": latency, "strategy": "miss"}
        self._append_event(T, tenant_id, prompt_hash, "miss", 0.0, latency)

        # Phase 1 (synchronous): exact + hash + embedding + FAISS
        # Embedding MUST be computed synchronously so the FAISS index is
        # populated before the next query arrives.
        user_text = " ".join(m["content"] for m in messages if m.get("role") == "user") or prompt_norm
        entry_domain = domain_hint(user_text)

        # Ensure we have an embedding — compute now if semantic search was skipped
        if query_emb is None:
            try:
                query_emb, _ = self._get_embedding_for_query(messages, user_id=user_id)
            except Exception as emb_err:
                error_log.warning(f"{tenant_id} | embedding failed (non-fatal): {emb_err}")

        entry = CacheEntry(
            prompt_norm=prompt_norm,
            response_text=response_text,
            embedding=query_emb,
            model=model,
            ttl_seconds=ttl_seconds,
            domain=entry_domain,
            strategy="miss",
        )
        with self._cache_lock:
            T.exact[prompt_norm] = entry
            norm_key = normalize_query(prompt_norm)
            if norm_key:
                T.norm_hash_index[norm_key] = entry
            deep_key = deep_normalize(prompt_norm)
            if deep_key and deep_key != norm_key:
                T.norm_hash_index[deep_key] = entry
            # Also store spelling-corrected variant for typo tolerance in hash lookup
            if SPELLING_CORRECTION_ENABLED:
                try:
                    from spelling import correct_spelling
                    corrected = correct_spelling(prompt_norm)
                    if corrected and corrected != prompt_norm:
                        corrected_deep = deep_normalize(corrected)
                        if corrected_deep and corrected_deep != deep_key and corrected_deep != norm_key:
                            T.norm_hash_index[corrected_deep] = entry
                except ImportError:
                    pass
                except Exception:
                    pass
            # FAISS index position must equal T.rows index — only append
            # to T.rows when we also add to FAISS.  Entries without embeddings
            # are still reachable via T.exact / T.norm_hash_index for exact/hash
            # lookups, but skipping T.rows prevents index misalignment that
            # would cause every subsequent semantic search to return wrong entries.
            if query_emb is not None:
                T.rows.append(entry)
                # Invalidate cached Pinecone hash lookup so it's rebuilt with the new entry
                if hasattr(T, '_hash_lookup'):
                    T._hash_lookup = None
                self._faiss_add(T, query_emb, tenant_id=tenant_id, entry_id=prompt_hash,
                                metadata={"model": model, "domain": entry_domain})
                # Also compute and add local embedding for the pre-filter gate
                if LOCAL_MODEL_ENABLED:
                    try:
                        local_text = deep_normalize(prompt_norm)
                        local_emb = get_local_embedding(local_text)
                        if local_emb is not None:
                            entry.local_embedding = local_emb
                            self._local_faiss_add(T, local_emb)
                    except Exception:
                        pass
            else:
                error_log.warning(
                    f"{tenant_id} | skipping T.rows/FAISS (no embedding) | "
                    f"entry still in exact/hash indexes | key={prompt_norm[:80]}"
                )

        # Phase 2 (background): persistence + enrichment only
        try:
            _query_org_id = _current_api_key_var.get().get("org_id")
        except Exception:
            _query_org_id = None

        def _persist_and_enrich():
            try:
                emb = entry.embedding
                if len(T.rows) % 10 == 0:
                    self._save_cache()

                # Redis (best-effort)
                try:
                    from redis_cache import store_exact_match, store_embedding
                    store_exact_match(tenant_id, prompt_hash, response_text, model, ttl_seconds)
                    if emb is not None:
                        store_embedding(tenant_id, prompt_hash, emb, ttl_seconds)
                except Exception:
                    pass

                # DB persistence (best-effort)
                try:
                    if _query_org_id:
                        from database import store_cache_entry
                        import datetime
                        ttl_dt = (datetime.datetime.utcnow() + datetime.timedelta(seconds=ttl_seconds)).isoformat()
                        store_cache_entry(
                            org_id=_query_org_id, prompt_hash=prompt_hash,
                            prompt_norm=prompt_norm, response_text=response_text,
                            embedding_bytes=emb.tobytes() if emb is not None else None,
                            model=model, ttl_expires_at=ttl_dt,
                            domain=entry_domain, tenant_id=tenant_id,
                        )
                except Exception as _db_err:
                    error_log.warning(f"DB cache store failed: {_db_err}")

                # Enrichment: response embedding for query-to-response matching
                try:
                    resp_emb = None
                    resp_text_for_embed = response_text[:500]
                    try:
                        resp_emb = get_embedding(resp_text_for_embed, user_id=user_id, is_query=False)
                    except Exception:
                        pass

                    with self._cache_lock:
                        entry.response_embedding = resp_emb
                        if resp_emb is not None:
                            row_idx = T.rows.index(entry) if entry in T.rows else len(T.rows) - 1
                            self._response_faiss_add(T, resp_emb, row_idx)
                        if len(T.rows) % 100 == 0 and len(T.rows) >= 50:
                            self._rebuild_clusters(T)
                except Exception:
                    pass
            except Exception as e:
                error_log.warning(f"Cache persist/enrich failed (non-fatal) | tenant={tenant_id} | {e}")

        _bg_executor.submit(_persist_and_enrich)

        return response_text, meta

    def lookup(
        self,
        tenant_id: str,
        prompt_norm: str,
        messages: List[dict],
        model: str,
        user_id: Optional[str] = None,
    ) -> Tuple[Optional[str], dict]:
        """Cache lookup only — returns (cached_response, meta) or (None, miss_meta).

        Unlike ``query()``, this never calls the LLM.  The caller is
        responsible for generating the response on a miss and then calling
        ``store_miss()`` to persist it.
        """
        # Run the full query, but intercept before the LLM call by
        # temporarily patching call_llm to raise a sentinel.
        #
        # Cleaner approach: replicate the lookup tiers here.  Since query()
        # is long and may evolve, we use a simpler strategy — attempt query
        # with a patched call_llm that returns a sentinel.

        class _CacheMiss(Exception):
            pass

        _original = globals().get("call_llm")

        def _raise_sentinel(*a, **kw):
            raise _CacheMiss()

        T = self.tenant(tenant_id)
        t0 = time.time()
        globals()["call_llm"] = _raise_sentinel
        try:
            ans, meta = self.query(tenant_id, prompt_norm, messages, model, user_id=user_id)
            return ans, meta  # cache hit
        except _CacheMiss:
            latency = round((time.time() - t0) * 1000, 2)
            # Undo the miss counter increment that query() did before calling call_llm
            T.misses = max(0, T.misses - 1)
            # Include the best similarity score the engine found (even though
            # it wasn't high enough for a hit).  This lets the frontend show
            # "MISS · 68.2% match" so users can see the engine IS working.
            best_sim = getattr(T, '_last_miss_similarity', 0.0)
            return None, {"hit": "miss", "similarity": best_sim, "latency_ms": latency, "strategy": "miss"}
        finally:
            globals()["call_llm"] = _original

    def store_miss(
        self,
        tenant_id: str,
        prompt_norm: str,
        response_text: str,
        messages: List[dict],
        model: str,
        ttl_seconds: int = 7 * 24 * 3600,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
    ):
        """Store a response after a cache miss (e.g. after streaming completes).

        Architecture: two-phase storage for resilience.
          Phase 1 (synchronous): Create the CacheEntry, insert into exact +
              hash indexes, compute embeddings, and add to FAISS immediately.
              This guarantees that the very next query — whether identical,
              normalized, or semantically similar — will be a cache hit.
          Phase 2 (background): Persist to Redis / DB / Pinecone and enrich
              with response + local embeddings.  Failures here degrade
              persistence but never break in-memory cache matching.
        """
        T = self.tenant(tenant_id)
        T.misses += 1
        prompt_hash = hashlib.md5(prompt_norm.encode()).hexdigest()
        self._append_event(T, tenant_id, prompt_hash, "miss", 0.0, 0.0)

        user_text = " ".join(m["content"] for m in messages if m.get("role") == "user") or prompt_norm
        entry_domain = domain_hint(user_text)

        # ── Phase 1: Synchronous — exact + hash + embedding + FAISS ──
        # Embedding MUST be computed synchronously so that the FAISS index
        # is populated before the next query arrives.  Without this, semantic
        # search sees T.index=None and skips entirely (the original race condition).
        emb = None
        try:
            emb, _ = self._get_embedding_for_query(messages, user_id=user_id)
        except Exception as emb_err:
            error_log.warning(f"{tenant_id} | embedding failed (non-fatal): {emb_err}")

        entry = CacheEntry(
            prompt_norm=prompt_norm,
            response_text=response_text,
            embedding=emb,
            model=model,
            ttl_seconds=ttl_seconds,
            domain=entry_domain,
            strategy="miss",
        )
        with self._cache_lock:
            T.exact[prompt_norm] = entry
            norm_key = normalize_query(prompt_norm)
            if norm_key:
                T.norm_hash_index[norm_key] = entry
            deep_key = deep_normalize(prompt_norm)
            if deep_key and deep_key != norm_key:
                T.norm_hash_index[deep_key] = entry
            # Also store spelling-corrected variant for typo tolerance
            if SPELLING_CORRECTION_ENABLED:
                try:
                    from spelling import correct_spelling
                    corrected = correct_spelling(prompt_norm)
                    if corrected and corrected != prompt_norm:
                        corrected_deep = deep_normalize(corrected)
                        if corrected_deep and corrected_deep != deep_key and corrected_deep != norm_key:
                            T.norm_hash_index[corrected_deep] = entry
                except ImportError:
                    pass
                except Exception:
                    pass
            # Only append to T.rows when we also add to FAISS — keeps
            # FAISS index positions aligned with T.rows indices.
            if emb is not None:
                T.rows.append(entry)
                self._faiss_add(T, emb, tenant_id=tenant_id, entry_id=prompt_hash,
                                metadata={"model": model, "domain": entry_domain})
                if LOCAL_MODEL_ENABLED:
                    try:
                        local_text = deep_normalize(prompt_norm)
                        local_emb = get_local_embedding(local_text)
                        if local_emb is not None:
                            entry.local_embedding = local_emb
                            self._local_faiss_add(T, local_emb)
                    except Exception:
                        pass
            else:
                error_log.warning(
                    f"{tenant_id} | store_miss skipping T.rows/FAISS (no embedding) | "
                    f"entry still in exact/hash indexes | key={prompt_norm[:80]}"
                )

        access_log.info(
            f"{tenant_id} | store_miss | phase1 done | exact+hash+faiss stored | "
            f"norm_key={norm_key!r} | deep_key={deep_key!r} | emb={'yes' if emb is not None else 'no'}"
        )

        # ── Phase 2: Background — persistence + enrichment ──
        _store_org_id = org_id
        def _persist_and_enrich():
            try:
                # Redis (best-effort)
                try:
                    from redis_cache import store_exact_match, store_embedding
                    store_exact_match(tenant_id, prompt_hash, response_text, model, ttl_seconds)
                    if emb is not None:
                        store_embedding(tenant_id, prompt_hash, emb, ttl_seconds)
                except Exception:
                    pass

                # DB persistence (best-effort)
                try:
                    if _store_org_id:
                        from database import store_cache_entry
                        import datetime
                        ttl_dt = (datetime.datetime.utcnow() + datetime.timedelta(seconds=ttl_seconds)).isoformat()
                        store_cache_entry(
                            org_id=_store_org_id, prompt_hash=prompt_hash,
                            prompt_norm=prompt_norm, response_text=response_text,
                            embedding_bytes=emb.tobytes() if emb is not None else None,
                            model=model, ttl_expires_at=ttl_dt,
                            domain=entry_domain, tenant_id=tenant_id,
                        )
                        access_log.info(f"{tenant_id} | DB cache stored (store_miss) | org={_store_org_id}")
                    else:
                        error_log.warning(f"{tenant_id} | DB cache skipped: org_id is None")
                except Exception as _db_err:
                    error_log.warning(f"DB cache store failed: {_db_err}")

                # Enrichment: response embedding for query-to-response matching
                try:
                    resp_emb = None
                    resp_text_for_embed = response_text[:500]
                    try:
                        resp_emb = get_embedding(resp_text_for_embed, user_id=user_id, is_query=False)
                    except Exception:
                        pass

                    with self._cache_lock:
                        entry.response_embedding = resp_emb
                        if resp_emb is not None:
                            row_idx = T.rows.index(entry) if entry in T.rows else len(T.rows) - 1
                            self._response_faiss_add(T, resp_emb, row_idx)
                        if len(T.rows) % 10 == 0:
                            self._save_cache()
                        if len(T.rows) % 100 == 0 and len(T.rows) >= 50:
                            self._rebuild_clusters(T)
                except Exception:
                    pass

            except Exception as e:
                error_log.warning(f"Cache persist/enrich failed (non-fatal) | tenant={tenant_id} | {e}")

        _bg_executor.submit(_persist_and_enrich)

    def metrics(self, tenant_id: str) -> dict:
        T = self.tenant(tenant_id)
        total = T.hits + T.misses
        p50 = np.percentile(T.latencies_ms, 50) if T.latencies_ms else 0
        p95 = np.percentile(T.latencies_ms, 95) if T.latencies_ms else 0
        avg_latency = np.mean(T.latencies_ms) if T.latencies_ms else 0
        semantic_hit_ratio = (T.semantic_hits / total) if total > 0 else 0.0

        semantic_events = [e for e in T.events if e.decision == "semantic"]
        avg_cosine = np.mean([e.similarity for e in semantic_events]) if semantic_events else 0.0
        avg_hybrid = np.mean([e.hybrid_score for e in semantic_events if e.hybrid_score > 0]) if semantic_events else 0.0
        high_confidence_hits = len([e for e in semantic_events if e.hybrid_score >= 0.85])

        near_misses = getattr(T, '_near_misses', [])
        tokens_saved_est = T.hits * 100
        entries_with_resp_emb = sum(1 for r in T.rows if r.response_embedding is not None)
        entries_with_local_emb = sum(1 for r in T.rows if r.local_embedding is not None)
        index_type = type(T.index).__name__ if T.index else "none"

        return {
            "tenant": tenant_id,
            "requests": total,
            "hits": T.hits,
            "semantic_hits": T.semantic_hits,
            "misses": T.misses,
            "hit_ratio": round((T.hits / total) if total else 0.0, 3),
            "semantic_hit_ratio": round(semantic_hit_ratio, 3),
            "total_requests": total,
            "avg_latency_ms": round(float(avg_latency), 2),
            "tokens_saved_est": tokens_saved_est,
            "sim_threshold": round(T.sim_threshold, 3),
            "entries": len(T.rows),
            "p50_latency_ms": round(float(p50), 2),
            "p95_latency_ms": round(float(p95), 2),
            "avg_confidence": round(avg_cosine, 3),
            "avg_hybrid_score": round(avg_hybrid, 3),
            "high_confidence_hits": high_confidence_hits,
            "high_confidence_ratio": round((high_confidence_hits / len(semantic_events)) if semantic_events else 0.0, 3),
            "near_miss_count": len(near_misses),
            "domain_thresholds": {k: round(v, 3) for k, v in T.domain_thresholds.items()},
            # Engine info
            "embed_model": EMBED_MODEL,
            "embed_dimensions": EMBED_DIMENSIONS,
            "index_type": index_type,
            "local_model": LOCAL_MODEL_NAME if LOCAL_MODEL_ENABLED else "disabled",
            "cross_encoder": CROSS_ENCODER_MODEL if CROSS_ENCODER_ENABLED else "disabled",
            "entries_with_response_embedding": entries_with_resp_emb,
            "entries_with_local_embedding": entries_with_local_emb,
            "norm_hash_index_size": len(T.norm_hash_index),
            "n_clusters": T.n_clusters,
        }

    def adapt_threshold(self, tenant_id: str):
        """Adapt threshold using both hit ratio and near-miss distribution.

        Strategy:
        - If many near-misses cluster just below threshold → lower threshold
          to capture them (they're likely valid matches).
        - If hit ratio is very high → raise threshold to improve precision.
        - Near-miss data provides a direct signal the old approach lacked.
        """
        T = self.tenant(tenant_id)
        total = T.hits + T.misses
        if total < 10:
            return

        hit_ratio = T.hits / total
        near_misses = getattr(T, '_near_misses', [])

        # Near-miss pull: if many near-misses are within 0.05 of threshold,
        # there's a cluster of queries being needlessly rejected.
        if len(near_misses) >= 5:
            close_misses = [s for s in near_misses if s >= T.sim_threshold - 0.05]
            close_ratio = len(close_misses) / len(near_misses)
            if close_ratio > 0.5:
                T.sim_threshold = max(0.55, T.sim_threshold - 0.02)
                semantic_log.info(
                    f"{tenant_id} | threshold_adapted_down | "
                    f"close_miss_ratio={close_ratio:.2f} | new={T.sim_threshold:.3f}"
                )
                return

        if hit_ratio < 0.25:
            T.sim_threshold = max(0.55, T.sim_threshold - 0.015)
        elif hit_ratio > 0.80:
            T.sim_threshold = min(0.75, T.sim_threshold + 0.01)

    def warmup(
        self,
        tenant_id: str,
        entries: List[dict],
        user_id: Optional[str] = None,
        ttl_seconds: int = 7 * 24 * 3600,
        skip_duplicates: bool = True,
        org_id: Optional[str] = None,
    ) -> dict:
        """
        Pre-populate cache with historical (prompt, response) pairs.
        Each entry: {"prompt": str, "response": str, "model": str (optional)}
        Returns: {"added": int, "skipped": int, "errors": int}
        """
        T = self.tenant(tenant_id)
        added, skipped, errors = 0, 0, 0
        for i, item in enumerate(entries):
            try:
                prompt = (item.get("prompt") or item.get("query") or "").strip()
                response_text = (item.get("response") or item.get("answer") or item.get("content") or "").strip()
                model = item.get("model") or CHAT_MODEL
                if not prompt or not response_text:
                    skipped += 1
                    continue
                prompt_norm = self.norm_text(prompt)
                if skip_duplicates and prompt_norm in T.exact:
                    skipped += 1
                    continue
                emb = get_embedding(prompt, user_id=user_id)
                user_text = prompt
                resp_emb = None
                try:
                    resp_emb = get_embedding(response_text[:500], user_id=user_id)
                except Exception:
                    pass
                local_text = deep_normalize(prompt_norm)
                local_emb = get_local_embedding(local_text) if LOCAL_MODEL_ENABLED else None

                entry = CacheEntry(
                    prompt_norm=prompt_norm,
                    response_text=response_text,
                    embedding=emb,
                    model=model,
                    ttl_seconds=ttl_seconds,
                    domain=domain_hint(user_text),
                    strategy="warmup",
                    response_embedding=resp_emb,
                    local_embedding=local_emb,
                )
                warmup_hash = hashlib.md5(prompt_norm.encode()).hexdigest()
                with self._cache_lock:
                    T.exact[prompt_norm] = entry
                    norm_key = normalize_query(prompt_norm)
                    if norm_key:
                        T.norm_hash_index[norm_key] = entry
                    deep_key = deep_normalize(prompt_norm)
                    if deep_key and deep_key != norm_key:
                        T.norm_hash_index[deep_key] = entry
                    T.rows.append(entry)
                    self._faiss_add(T, emb, tenant_id=tenant_id, entry_id=warmup_hash,
                                    metadata={"model": model, "domain": domain_hint(user_text)})
                    if local_emb is not None:
                        self._local_faiss_add(T, local_emb)
                    if resp_emb is not None:
                        self._response_faiss_add(T, resp_emb, len(T.rows) - 1)
                added += 1
                try:
                    from redis_cache import store_exact_match, store_embedding
                    prompt_hash = hashlib.md5(prompt_norm.encode()).hexdigest()
                    store_exact_match(tenant_id, prompt_hash, response_text, model, ttl_seconds)
                    store_embedding(tenant_id, prompt_hash, emb, ttl_seconds)
                except Exception:
                    pass
                # Persist to PostgreSQL (encrypted if configured)
                if org_id:
                    try:
                        from database import store_cache_entry
                        import datetime as _dt
                        ttl_dt = (_dt.datetime.utcnow() + _dt.timedelta(seconds=ttl_seconds)).isoformat()
                        _bg_executor.submit(
                            store_cache_entry,
                            org_id=org_id, prompt_hash=warmup_hash,
                            prompt_norm=prompt_norm, response_text=response_text,
                            embedding_bytes=emb.tobytes() if emb is not None else None,
                            model=model, ttl_expires_at=ttl_dt,
                            domain=domain_hint(user_text), tenant_id=tenant_id,
                        )
                    except Exception as _db_err:
                        error_log.warning(f"Warmup DB store failed: {_db_err}")
                if (i + 1) % 5 == 0:
                    time.sleep(0.05)
            except Exception as e:
                errors += 1
                error_log.warning(f"Warmup entry failed | tenant={tenant_id} | idx={i} | error={e}")
        if added > 0:
            _bg_executor.submit(self._save_cache)
        return {"added": added, "skipped": skipped, "errors": errors}

svc = SemanticCacheService()

# Save cache on shutdown
import atexit

def _save_cache_on_exit():
    """Save cache on normal exit."""
    try:
        svc._save_cache()
        system_log.info("Shutdown | cache saved")
    except Exception as e:
        app_log.warning(f"Failed to save cache on exit: {e}")

atexit.register(_save_cache_on_exit)

# -----------------------------
# FastAPI app + middleware + rate limiting
# -----------------------------
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


def _get_rate_limit_key(request: Request) -> str:
    """Use API key tenant as rate limit key when available, else fall back to IP."""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer sc-"):
        parts = auth[len("Bearer sc-"):].split("-", 1)
        if parts:
            return f"tenant:{parts[0]}"
    return get_remote_address(request)


limiter = Limiter(key_func=_get_rate_limit_key)
app = FastAPI(title="Semantys AI - Semantic Cache API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


# ── Global request body size limit (2MB) ──
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

_MAX_BODY_SIZE = 2 * 1024 * 1024  # 2 MB

class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > _MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Request body too large. Maximum is {_MAX_BODY_SIZE // (1024*1024)}MB."},
            )
        return await call_next(request)

app.add_middleware(MaxBodySizeMiddleware)


# ── Scheduled log cleanup (runs daily in background) ──
def _schedule_log_cleanup():
    """Run database log cleanup once per day in a background thread."""
    import time as _time
    def _cleanup_loop():
        while True:
            _time.sleep(24 * 3600)  # wait 24 hours
            try:
                from database import cleanup_old_logs
                cleanup_old_logs(usage_days=90, audit_days=365)
            except Exception:
                pass
    t = threading.Thread(target=_cleanup_loop, daemon=True)
    t.start()
    app_log.info("Scheduled daily log cleanup: usage_logs >90d, audit_logs >365d")

_schedule_log_cleanup()


from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def structured_http_error(request: Request, exc: StarletteHTTPException):
    rid = getattr(request.state, "request_id", None) if hasattr(request, "state") else None
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"message": str(exc.detail), "status": exc.status_code, "request_id": rid},
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    rid = getattr(request.state, "request_id", None) if hasattr(request, "state") else None
    error_log.exception(f"Unhandled exception | request_id={rid} | path={request.url.path} | error={exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {"message": "Internal server error", "status": 500, "request_id": rid},
        },
    )


# Prometheus metrics integration
try:
    from prometheus_metrics import CacheMetrics as _prom
except Exception:
    _prom = None

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing, access logging, and Prometheus metrics."""
    import uuid
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    access_log.info(
        f"{request_id} | REQ | {request.method} {request.url.path} | "
        f"ip={client_ip} | ua={user_agent[:100]}"
    )

    try:
        response = await call_next(request)
        latency_s = time.time() - start_time
        process_time = round(latency_s * 1000, 2)

        access_log.info(
            f"{request_id} | RESP | {request.method} {request.url.path} | "
            f"status={response.status_code} | time={process_time}ms"
        )

        if _prom:
            _prom.record_api_request(request.url.path, request.method, response.status_code, latency_s)

        if process_time > 5000:
            performance_log.warning(
                f"{request_id} | SLOW_REQUEST | {request.method} {request.url.path} | "
                f"time={process_time}ms | ip={client_ip}"
            )

        return response
    except Exception as e:
        latency_s = time.time() - start_time
        process_time = round(latency_s * 1000, 2)
        error_log.exception(
            f"{request_id} | REQ_ERROR | {request.method} {request.url.path} | "
            f"ip={client_ip} | time={process_time}ms | error={str(e)}"
        )
        if _prom:
            _prom.record_api_request(request.url.path, request.method, 500, latency_s)
        raise

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Admin-Key"],
    expose_headers=["X-Cache-Hit", "X-Cache-Similarity", "X-Cache-Latency", "X-Cache-Strategy"],
    max_age=3600,
)

# Define API Key Header
api_key_header = APIKeyHeader(
    name="Authorization",
    scheme_name="BearerAuth",
    description="Use format: Bearer sc-{tenant}-{anything}",
    auto_error=False,
)

# Custom OpenAPI schema with explicit auth
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Semantys AI Semantic Cache API",
        version="0.1.0",
        description=(
            "A semantic caching service for LLM apps. "
            "Authentication via Bearer API keys formatted as `Bearer sc-{tenant}-{anything}`."
        ),
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "sc-{tenant}-{anything}",
            "description": "Use tenant-based auth keys (e.g., Bearer sc-test-local)"
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Include admin router (after app is created)
def setup_admin_routes():
    """Setup admin routes after all dependencies are loaded."""
    try:
        from admin_api import admin_router
        app.include_router(admin_router)
        system_log.info("Admin routes registered")
    except Exception as e:
        error_log.warning(f"Could not register admin routes: {e}")

# Setup admin routes
setup_admin_routes()

# Simple API-key format: Bearer sc-{tenant}-{anything}
API_KEY_REGEX = re.compile(r"^Bearer\s+(sc-[A-Za-z0-9_-]{3,256})$")
_api_key_cache: OrderedDict = OrderedDict()  # Bounded LRU: token -> {"user_id": ..., "ts": epoch}
_API_KEY_CACHE_MAX = 10_000

# Request-scoped API key context (safe for concurrent async requests)
_current_api_key_var: ContextVar[dict] = ContextVar('_current_api_key', default={"key": None, "user_id": None})


def _is_allowed_api_scope(scope: Optional[str]) -> bool:
    return scope in {"read-only", "read-write", "admin"}


def get_tenant_from_key(request: Request) -> str:
    client_ip = request.client.host if request.client else "unknown"
    auth = request.headers.get("Authorization", "")
    m = API_KEY_REGEX.match(auth)
    if not m:
        security_log.warning(
            f"Auth failed | ip={client_ip} | reason=invalid_format | "
            f"header_length={len(auth)} | path={request.url.path}"
        )
        error_log.error(f"Unauthorized access | ip={client_ip} | Header length: {len(auth)}")
        raise HTTPException(status_code=401, detail="Missing or invalid API key")

    token = m.group(1)
    ctx = {
        "key": token,
        "user_id": None,
        "org_id": None,
        "scope": "read-write",
        "plan": "free",
        "tenant": None,
        "db_tenant_id": None,
    }
    _current_api_key_var.set(ctx)
    request.state.api_ctx = ctx  # Also store on request for generator access

    # Fast in-memory API key cache (avoids DB round-trip on every request)
    cached = _api_key_cache.get(token)
    if cached and (time.time() - cached["ts"]) < 300:
        tenant = cached.get("tenant")
        if not tenant:
            raise HTTPException(status_code=401, detail="Invalid API key")
        ctx["user_id"] = cached.get("user_id")
        ctx["org_id"] = cached.get("org_id")
        ctx["scope"] = cached.get("scope", "read-write")
        ctx["plan"] = cached.get("plan", "free")
        ctx["tenant"] = tenant
        ctx["db_tenant_id"] = cached.get("db_tenant_id", tenant)
        _current_api_key_var.set(ctx)
        if cached.get("expires_at") and time.time() > cached["expires_at"]:
            raise HTTPException(status_code=401, detail="API key expired")
        allowed = cached.get("allowed_ips")
        if allowed and client_ip not in allowed:
            security_log.warning(f"IP denied | tenant={tenant} | ip={client_ip}")
            raise HTTPException(status_code=403, detail="IP not allowed for this key")

        def _bg_usage():
            try:
                from database import update_api_key_usage
                update_api_key_usage(token, ctx["db_tenant_id"] or tenant)
            except Exception:
                pass

        _bg_executor.submit(_bg_usage)
        return tenant

    try:
        from database import get_api_key_info, get_org_for_api_key, update_api_key_usage

        key_info = get_api_key_info(token)
        if not key_info:
            security_log.warning(
                f"API key not found | ip={client_ip} | key_prefix={token[:20]}"
            )
            raise HTTPException(status_code=401, detail="Invalid API key")

        db_tenant_id = str(key_info.get("tenant_id") or "").strip()
        if not db_tenant_id:
            raise HTTPException(status_code=401, detail="Invalid API key")

        exp = key_info.get("expires_at")
        exp_ts = exp.timestamp() if hasattr(exp, "timestamp") else None
        if exp_ts and time.time() > exp_ts:
            raise HTTPException(status_code=401, detail="API key expired")

        org = None
        try:
            org = get_org_for_api_key(token)
        except Exception:
            org = None

        runtime_tenant = str(org.get("slug") or "").strip() if org else db_tenant_id
        resolved_scope = key_info.get("scope", "read-write")
        if not _is_allowed_api_scope(resolved_scope):
            resolved_scope = "read-write"
        resolved_plan = str(org.get("plan") or "").strip() if org else ""
        if not resolved_plan:
            resolved_plan = str(key_info.get("plan") or "free")

        allowed = key_info.get("allowed_ips")
        if allowed and client_ip not in allowed:
            security_log.warning(f"IP denied | tenant={runtime_tenant} | ip={client_ip}")
            raise HTTPException(status_code=403, detail="IP not allowed for this key")

        update_api_key_usage(token, db_tenant_id)
        ctx["user_id"] = key_info.get("user_id")
        ctx["org_id"] = str(key_info.get("org_id", "")) or None
        ctx["scope"] = resolved_scope
        ctx["plan"] = resolved_plan
        ctx["tenant"] = runtime_tenant
        ctx["db_tenant_id"] = db_tenant_id
        _current_api_key_var.set(ctx)
        _api_key_cache[token] = {
            "tenant": runtime_tenant,
            "db_tenant_id": db_tenant_id,
            "user_id": ctx["user_id"],
            "org_id": ctx["org_id"],
            "scope": ctx["scope"],
            "plan": ctx["plan"],
            "allowed_ips": allowed,
            "expires_at": exp_ts,
            "ts": time.time(),
        }
        while len(_api_key_cache) > _API_KEY_CACHE_MAX:
            _api_key_cache.popitem(last=False)
        security_log.debug(
            f"Auth success | tenant={runtime_tenant} | ip={client_ip} | "
            f"plan={ctx['plan']} | scope={ctx['scope']} | org_id={ctx['org_id']}"
        )
        return runtime_tenant
    except HTTPException:
        raise
    except Exception as e:
        error_log.warning(f"Database operation failed | key_prefix={token[:20]} | error={str(e)}")
        raise HTTPException(status_code=503, detail="Authentication service temporarily unavailable")


def _require_scope(request: Request, required: str):
    """Check that the current API key has the required scope."""
    ctx = _current_api_key_var.get()
    scope = ctx.get("scope", "read-write")
    scope_levels = {"read-only": 0, "read-write": 1, "admin": 2}
    if scope_levels.get(scope, 0) < scope_levels.get(required, 0):
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required: {required}, got: {scope}"
        )


_ORG_ROLE_LEVELS = {"member": 0, "admin": 1, "owner": 2}


def _get_user_org_membership(user_id: str, org_id: str) -> Optional[dict]:
    from database import get_user_orgs

    for org in get_user_orgs(user_id):
        if str(org.get("id")) == str(org_id):
            return org
    return None


def _require_org_membership(user_id: str, org_id: str, min_role: str = "member") -> dict:
    membership = _get_user_org_membership(user_id, org_id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    current_role = str(membership.get("role") or "member")
    required_level = _ORG_ROLE_LEVELS.get(min_role, _ORG_ROLE_LEVELS["member"])
    current_level = _ORG_ROLE_LEVELS.get(current_role, _ORG_ROLE_LEVELS["member"])
    if current_level < required_level:
        raise HTTPException(status_code=403, detail=f"{min_role} role required for this organization")
    return membership


def _normalize_origin(url: str) -> Optional[str]:
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _get_allowed_redirect_origins() -> List[str]:
    origins: List[str] = []
    for raw_origin in [FRONTEND_URL, *ALLOWED_ORIGINS]:
        origin = _normalize_origin(raw_origin)
        if origin and origin not in origins:
            origins.append(origin)
    return origins


def _resolve_billing_return_url(request: Request, candidate_url: str, fallback_path: str) -> str:
    allowed_origins = _get_allowed_redirect_origins()
    request_origin = _normalize_origin(request.headers.get("origin", ""))
    default_origin = request_origin if request_origin in allowed_origins else (allowed_origins[0] if allowed_origins else None)

    if candidate_url:
        candidate_origin = _normalize_origin(candidate_url)
        if not candidate_origin:
            raise HTTPException(status_code=400, detail="Invalid billing return URL")
        if candidate_origin not in allowed_origins:
            raise HTTPException(status_code=400, detail="Billing return URL origin is not allowed")
        return candidate_url

    if not default_origin:
        raise HTTPException(status_code=500, detail="Billing redirect origin is not configured")
    return f"{default_origin}{fallback_path}"

# -----------------------------
# Request/Response models (OpenAI-like)
# -----------------------------
class ChatMessage(BaseModel):
    role: str
    content: str

    @validator("role")
    def validate_role(cls, v):
        if len(v) > 50:
            raise ValueError("role must be under 50 characters")
        if v not in ("system", "user", "assistant", "function", "tool"):
            raise ValueError("invalid role")
        return v

    @validator("content")
    def validate_content(cls, v):
        if len(v) > 30_000:
            raise ValueError("content exceeds 30,000 character limit")
        return v

class ChatRequest(BaseModel):
    model: str = CHAT_MODEL
    messages: List[ChatMessage]
    temperature: float = 0.2
    ttl_seconds: int = 7 * 24 * 3600
    stream: bool = False

    @validator("model")
    def validate_model(cls, v):
        if len(v) > 100:
            raise ValueError("model name too long")
        return v

    @validator("temperature")
    def temp_range(cls, v):
        if not (0.0 <= v <= 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v

    @validator("ttl_seconds")
    def validate_ttl(cls, v):
        if v < 0 or v > 30 * 24 * 3600:
            raise ValueError("ttl_seconds must be between 0 and 30 days")
        return v

    @validator("messages")
    def messages_not_empty(cls, v):
        if not v:
            raise ValueError("messages list cannot be empty")
        if len(v) > 50:
            raise ValueError("too many messages (max 50)")
        return v

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/health")
@limiter.limit("60/minute")
def health(request: Request):
    """Health check endpoint with system status."""
    
    try:
        memory = None
        cpu_percent = 0.0
        try:
            import psutil
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0)
            has_system_metrics = True
        except ImportError:
            has_system_metrics = False
        
        total_tenants = len(svc.tenants)
        total_entries = sum(len(t.rows) for t in svc.tenants.values())
        
        # Redis health
        try:
            from redis_cache import health_check as redis_health
            redis_status = redis_health()
        except Exception:
            redis_status = {"status": "unavailable"}
        
        health_status = {
            "status": "ok",
            "service": "semantic-cache",
            "version": "3.0.0",
            "engine": {
                "embed_model": EMBED_MODEL,
                "embed_dimensions": EMBED_DIMENSIONS,
                "local_model": LOCAL_MODEL_NAME if LOCAL_MODEL_ENABLED else "disabled",
                "cross_encoder": CROSS_ENCODER_MODEL if CROSS_ENCODER_ENABLED else "disabled",
            },
            "cache": {
                "tenants": total_tenants,
                "total_entries": total_entries,
            },
            "redis": redis_status,
        }
        
        if has_system_metrics and memory is not None:
            health_status["system"] = {
                "memory_percent": round(memory.percent, 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "cpu_percent": round(cpu_percent, 2),
            }
        
        return health_status
    except Exception as e:
        error_log.exception(f"Health check failed | error={str(e)}")
        return {"status": "error", "service": "semantic-cache", "version": "2.0.0"}

@app.get("/metrics")
@limiter.limit("60/minute")
def get_metrics(request: Request, tenant: str = Depends(get_tenant_from_key)):
    """Get cache performance metrics for the tenant."""
    svc.adapt_threshold(tenant)
    m = svc.metrics(tenant)

    # If in-memory metrics are empty (e.g. after restart), enrich from database
    if m.get("requests", 0) == 0:
        try:
            from database import get_usage_stats
            db_stats = get_usage_stats(tenant, days=30)
            db_total = int(db_stats.get("total_requests", 0))
            db_hits = int(db_stats.get("total_hits", 0))
            db_misses = int(db_stats.get("total_misses", 0))
            _db_tokens = int(db_stats.get("total_tokens", 0))  # noqa: F841
            if db_total > 0:
                m["requests"] = db_total
                m["total_requests"] = db_total
                m["hits"] = db_hits
                m["misses"] = db_misses if db_misses > 0 else max(db_total - db_hits, 0)
                m["hit_ratio"] = round(db_hits / db_total, 3) if db_total > 0 else 0.0
                m["tokens_saved_est"] = db_hits * 100
                # Estimate avg latency if we have no real data
                if m.get("avg_latency_ms", 0) == 0:
                    m["avg_latency_ms"] = 45.0  # reasonable default for cached responses
        except Exception as e:
            error_log.warning(f"Failed to enrich metrics from DB for {tenant}: {e}")

    access_log.info(f"{tenant} | /metrics | hit_ratio={m['hit_ratio']}")
    return m

@app.get("/prometheus/metrics")
@limiter.limit("30/minute")
def prometheus_metrics(request: Request):
    """Prometheus metrics endpoint."""
    try:
        from prometheus_metrics import get_metrics_response
        return get_metrics_response()
    except ImportError:
        # Prometheus not available, return basic metrics
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            "# Prometheus metrics not available. Install prometheus-client for full metrics.\n"
            "# Basic metrics:\n"
            f"cache_entries_total {sum(len(t.rows) for t in svc.tenants.values())}\n"
            f"cache_tenants_total {len(svc.tenants)}\n",
            media_type="text/plain"
        )
    except Exception as e:
        error_log.exception(f"Prometheus metrics endpoint failed | error={str(e)}")
        raise HTTPException(status_code=500, detail="Metrics endpoint failed")

@app.get("/query")
@limiter.limit("200/minute")
def simple_query(request: Request, prompt: str = Query(...), model: str = CHAT_MODEL, tenant: str = Depends(get_tenant_from_key)):
    # --- Input guard (runs before cache pipeline) ---
    from input_guard import guard_request
    messages = [{"role": "user", "content": prompt}]
    messages, guard_err = guard_request(messages, 0.2, model)
    if guard_err:
        raise HTTPException(status_code=400, detail=guard_err)

    prompt_norm = SemanticCacheService.extract_cache_query(messages)
    prompt_hash = hashlib.md5(prompt_norm.encode()).hexdigest()[:8]

    endpoint_start = time.time()
    try:
        # Get user_id from current API key context
        _ctx = _current_api_key_var.get()
        user_id = _ctx.get("user_id")

        # Enforce plan limits (Redis counter for speed, DB fallback)
        try:
            from billing import get_plan_limits
            from redis_cache import increment_monthly_usage
            plan = _ctx.get("plan", "free")
            current_requests = increment_monthly_usage(tenant)
            if current_requests == -1:
                from database import get_usage_stats
                usage = get_usage_stats(tenant, days=30)
                current_requests = int(usage.get("total_requests", 0))
            limits = get_plan_limits(plan)
            max_req = limits.get("max_requests_month", 1000)
            if current_requests > max_req:
                raise HTTPException(
                    status_code=429,
                    detail=f"Monthly request limit reached for your '{plan}' plan ({current_requests}/{max_req}). "
                           f"Upgrade at /settings to continue.",
                )
        except HTTPException:
            raise
        except Exception:
            pass

        ans, meta = svc.query(tenant, prompt_norm, messages, model, user_id=user_id)
        query_time = round((time.time() - endpoint_start) * 1000, 2)
        
        # Get metrics (fast - just reading from memory)
        metrics_start = time.time()
        metrics = svc.metrics(tenant)
        metrics_time = round((time.time() - metrics_start) * 1000, 2)
        
        # Enhanced logging (fast - just file write)
        log_start = time.time()
        access_log.info(
            f"{tenant} | /query | {meta['hit']} | sim={meta['similarity']:.3f} | "
            f"latency={meta['latency_ms']}ms | prompt_hash={prompt_hash} | "
            f"model={model} | prompt_len={len(prompt)}"
        )
        log_time = round((time.time() - log_start) * 1000, 2)
        
        # Capture context for async logging (ContextVar is not inherited by threads)
        _log_api_key = _ctx.get("key", "unknown")
        _log_user_id = user_id
        
        # Log usage to database asynchronously (non-blocking - database can be slow)
        def log_usage_async():
            try:
                from database import log_usage
                api_key = _log_api_key
                user_id = _log_user_id
                log_usage(
                    api_key=api_key,
                    tenant_id=tenant,
                    endpoint="/query",
                    request_count=1,
                    cache_hits=1 if meta.get('hit') != 'miss' else 0,
                    cache_misses=1 if meta.get('hit') == 'miss' else 0,
                    tokens_used=0,
                    cost_estimate=0,
                    user_id=user_id,
                    decision=meta.get('hit', 'miss'),
                    similarity=float(meta.get('similarity', 0.0)),
                    latency_ms=float(meta.get('latency_ms', 0.0)),
                    prompt_hash=meta.get('prompt_hash', '')
                )
            except Exception as e:
                error_log.warning(f"Could not log usage to database | tenant={tenant} | error={str(e)}")
        
        # Run database logging in background thread (non-blocking)
        _bg_executor.submit(log_usage_async)
        
        # Log timing breakdown
        before_return = time.time()
        endpoint_total = round((before_return - endpoint_start) * 1000, 2)
        access_log.debug(
            f"{tenant} | /query-timing | query={query_time}ms | metrics={metrics_time}ms | "
            f"log={log_time}ms | total={endpoint_total}ms | response_len={len(ans)}"
        )
        
        # Return immediately with metrics (database logging happens async)
        return {"answer": ans, "meta": meta, "metrics": metrics}
    except Exception as e:
        error_log.exception(
            f"{tenant} | /query | error: {e} | prompt_hash={prompt_hash} | "
            f"prompt_len={len(prompt)} | model={model}"
        )
        raise HTTPException(status_code=500, detail="Internal error")

@app.get("/events")
@limiter.limit("60/minute")
def get_events(request: Request, limit: int = Query(100, ge=1, le=1000), tenant: str = Depends(get_tenant_from_key)):
    """Get recent cache events from DB (persisted across restarts)."""
    try:
        from database import get_events_from_db
        db_events = get_events_from_db(tenant, limit)
        return [
            {
                "timestamp": str(e.get("logged_at", "")),
                "tenant_id": e.get("tenant_id", tenant),
                "prompt_hash": e.get("prompt_hash", ""),
                "decision": e.get("decision", "miss"),
                "similarity": float(e.get("similarity", 0.0)),
                "latency_ms": float(e.get("latency_ms", 0.0)),
            }
            for e in db_events
        ]
    except Exception as _e:
        error_log.warning(f"Failed to load events from DB: {_e}")
        # Fallback to in-memory events
        T = svc.tenant(tenant)
        events = T.events[-limit:] if len(T.events) > limit else T.events
        return [
            {
                "timestamp": e.timestamp,
                "tenant_id": e.tenant_id,
                "prompt_hash": e.prompt_hash,
                "decision": e.decision,
                "similarity": e.similarity,
                "latency_ms": e.latency_ms,
            }
            for e in reversed(events)
        ]

class SettingsUpdate(BaseModel):
    sim_threshold: Optional[float] = None
    ttl_days: Optional[int] = None
    domain_thresholds: Optional[Dict[str, float]] = None

@app.get("/settings")
@limiter.limit("60/minute")
def get_settings(request: Request, tenant: str = Depends(get_tenant_from_key)):
    """Get current cache settings for the tenant."""
    T = svc.tenant(tenant)
    return {
        "sim_threshold": round(T.sim_threshold, 3),
        "ttl_days": 7,
        "entries": len(T.rows),
        "domain_thresholds": {k: round(v, 3) for k, v in T.domain_thresholds.items()},
        "available_domains": list(DOMAIN_MAP.keys()),
        "embed_model": EMBED_MODEL,
        "embed_dimensions": EMBED_DIMENSIONS,
        "local_model": LOCAL_MODEL_NAME if LOCAL_MODEL_ENABLED else "disabled",
        "cross_encoder": CROSS_ENCODER_MODEL if CROSS_ENCODER_ENABLED else "disabled",
        "ivf_upgrade_threshold": IVF_UPGRADE_THRESHOLD,
        "index_type": type(T.index).__name__ if T.index else "none",
        "norm_hash_index_size": len(T.norm_hash_index),
        "n_clusters": T.n_clusters,
    }

class WarmupEntry(BaseModel):
    prompt: str = ""
    response: str = ""
    model: Optional[str] = None

    @validator("prompt", "response")
    def limit_field_length(cls, v: str) -> str:  # noqa: N805
        if len(v) > 10_000:
            raise ValueError("Field exceeds 10 000 character limit")
        return v


class WarmupRequest(BaseModel):
    entries: List[WarmupEntry]
    tenant: Optional[str] = None
    skip_duplicates: bool = True


@app.post("/api/cache/warmup")
@limiter.limit("10/hour")
def cache_warmup(body: WarmupRequest, request: Request):
    """
    Pre-populate cache with historical (prompt, response) pairs.
    Use your previous application queries to warm the cache for immediate semantic hits.
    Requires Supabase JWT. Entries: [{"prompt": "...", "response": "...", "model": "gpt-4o-mini"}]
    """
    try:
        user = _get_user_from_supabase_token(request)
        from database import get_user_orgs, list_api_keys

        orgs = get_user_orgs(user["id"])
        keys = list_api_keys(user_id=user["id"])
        org_slug_by_id = {
            str(org.get("id")): str(org.get("slug"))
            for org in orgs
            if org.get("id") and org.get("slug")
        }
        allowed_tenants: Dict[str, str] = {}
        for org in orgs:
            slug = str(org.get("slug") or "").strip()
            if slug:
                allowed_tenants[slug] = slug
        for key in keys:
            raw_tenant = str(key.get("tenant_id") or "").strip()
            runtime_tenant = org_slug_by_id.get(str(key.get("org_id") or ""), raw_tenant)
            if raw_tenant:
                allowed_tenants[raw_tenant] = runtime_tenant
            if runtime_tenant:
                allowed_tenants[runtime_tenant] = runtime_tenant

        requested_tenant = (body.tenant or "").strip()
        if requested_tenant:
            tenant = allowed_tenants.get(requested_tenant)
            if not tenant:
                raise HTTPException(status_code=403, detail="Requested tenant is not assigned to your account")
        elif allowed_tenants:
            tenant = next(iter(allowed_tenants.values()))
        else:
            tenant = f"usr_{user['id'][:8]}"
        selected_org = next(
            (org for org in orgs if str(org.get("slug") or "").strip() == tenant),
            orgs[0] if orgs else None,
        )

        # Enforce plan limits (Redis counter for speed, DB fallback)
        try:
            from billing import get_plan_limits
            from redis_cache import increment_monthly_usage
            org_plan = selected_org.get("plan", "free") if selected_org else "free"
            current_requests = increment_monthly_usage(tenant)
            if current_requests == -1:
                from database import get_usage_stats
                usage = get_usage_stats(tenant, days=30)
                current_requests = int(usage.get("total_requests", 0))
            limits = get_plan_limits(org_plan)
            max_req = limits.get("max_requests_month", 1000)
            if current_requests > max_req:
                raise HTTPException(
                    status_code=429,
                    detail=f"Monthly request limit reached for your '{org_plan}' plan ({current_requests}/{max_req}). "
                           f"Upgrade at /settings to continue.",
                )
        except HTTPException:
            raise
        except Exception:
            pass

        entries = [
            {"prompt": e.prompt, "response": e.response, "model": e.model}
            for e in body.entries
        ]
        if len(entries) > 500:
            raise HTTPException(status_code=400, detail="Maximum 500 entries per request")
        warmup_org_id = str(selected_org.get("id") or "") if selected_org else ""
        result = svc.warmup(
            tenant,
            entries,
            user_id=user["id"],
            skip_duplicates=body.skip_duplicates,
            org_id=warmup_org_id or None,
        )
        app_log.info(f"Cache warmup | tenant={tenant} | added={result['added']} | skipped={result['skipped']} | errors={result['errors']}")
        return {"message": "Warmup complete", **result}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Cache warmup failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/v1/cache/warmup")
@limiter.limit("10/hour")
def cache_warmup_api_key(body: WarmupRequest, request: Request, tenant: str = Depends(get_tenant_from_key)):
    """
    Pre-populate cache with historical (prompt, response) pairs. Uses API key auth.
    Entries: [{"prompt": "...", "response": "...", "model": "gpt-4o-mini"}]
    """
    try:
        _ctx = _current_api_key_var.get()
        user_id = _ctx.get("user_id")

        # Enforce plan limits (Redis counter for speed, DB fallback)
        try:
            from billing import get_plan_limits
            from redis_cache import increment_monthly_usage
            plan = _ctx.get("plan", "free")
            current_requests = increment_monthly_usage(tenant)
            if current_requests == -1:
                from database import get_usage_stats
                usage = get_usage_stats(tenant, days=30)
                current_requests = int(usage.get("total_requests", 0))
            limits = get_plan_limits(plan)
            max_req = limits.get("max_requests_month", 1000)
            if current_requests > max_req:
                raise HTTPException(
                    status_code=429,
                    detail=f"Monthly request limit reached for your '{plan}' plan ({current_requests}/{max_req}). "
                           f"Upgrade at /settings to continue.",
                )
        except HTTPException:
            raise
        except Exception:
            pass

        entries = [
            {"prompt": e.prompt, "response": e.response, "model": e.model}
            for e in body.entries
        ]
        if len(entries) > 500:
            raise HTTPException(status_code=400, detail="Maximum 500 entries per request")
        api_org_id: str = _ctx.get("org_id", "")
        result = svc.warmup(
            tenant,
            entries,
            user_id=user_id,
            skip_duplicates=body.skip_duplicates,
            org_id=api_org_id or None,
        )
        return {"message": "Warmup complete", **result}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Cache warmup failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ── Cache Entry Management Endpoints ──

@app.get("/api/cache/entries")
@limiter.limit("30/minute")
def list_cache_entries_endpoint(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, max_length=200),
):
    """List cache entries for the authenticated user's org. Supports pagination and search."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import get_user_orgs, list_cache_entries, count_cache_entries
        orgs = get_user_orgs(user["id"])
        if not orgs:
            return {"entries": [], "total": 0}
        org_id: str = orgs[0].get("id", "")
        tenant_id: str = orgs[0].get("slug", "")
        if not org_id:
            return {"entries": [], "total": 0}
        entries = list_cache_entries(org_id, limit=limit, offset=offset, search=search, tenant_id=tenant_id)
        total = count_cache_entries(org_id, search=search)
        # Truncate response_text for listing
        for e in entries:
            if e.get("response_text") and len(e["response_text"]) > 200:
                e["response_text"] = e["response_text"][:200] + "..."
            for dt_field in ("created_at", "last_used_at", "ttl_expires_at"):
                if e.get(dt_field) is not None:
                    e[dt_field] = str(e[dt_field])
        return {"entries": entries, "total": total}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"List cache entries failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


class DeleteEntriesRequest(BaseModel):
    entry_ids: List[int]

    @validator("entry_ids")
    def validate_ids(cls, v):
        if len(v) > 500:
            raise ValueError("max 500 entries per delete request")
        return v


@app.delete("/api/cache/entries")
@limiter.limit("20/minute")
def delete_cache_entries_endpoint(request: Request, body: DeleteEntriesRequest):
    """Delete one or more cache entries by ID."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import get_user_orgs, delete_cache_entries_bulk
        orgs = get_user_orgs(user["id"])
        if not orgs:
            raise HTTPException(status_code=403, detail="No organization found")
        org_id: str = orgs[0].get("id", "")
        if not org_id:
            raise HTTPException(status_code=403, detail="No organization found")
        if len(body.entry_ids) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 entries per delete request")
        deleted = delete_cache_entries_bulk(body.entry_ids, org_id)
        app_log.info(f"Cache entries deleted | org={org_id} | deleted={deleted}")
        return {"deleted": deleted}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Delete cache entries failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.put("/settings")
@limiter.limit("30/minute")
def update_settings(request: Request, body: SettingsUpdate, tenant: str = Depends(get_tenant_from_key)):
    """Update cache settings for the tenant."""
    T = svc.tenant(tenant)
    changed = {}
    if body.sim_threshold is not None:
        clamped = max(0.50, min(0.99, body.sim_threshold))
        T.sim_threshold = clamped
        changed["sim_threshold"] = round(clamped, 3)
    if body.ttl_days is not None:
        changed["ttl_days"] = max(1, min(90, body.ttl_days))
    if body.domain_thresholds is not None:
        valid_domains = set(DOMAIN_MAP.keys()) | {"general"}
        for domain, thresh in body.domain_thresholds.items():
            if domain in valid_domains:
                T.domain_thresholds[domain] = max(0.50, min(0.99, thresh))
        changed["domain_thresholds"] = {k: round(v, 3) for k, v in T.domain_thresholds.items()}
    access_log.info(f"{tenant} | /settings | updated={changed}")

    # Persist to DB (org settings JSONB) in background
    def _persist_settings():
        try:
            ctx = _current_api_key_var.get()
            org_id = ctx.get("org_id")
            if org_id:
                from database import update_org_settings
                update_org_settings(org_id, {
                    "sim_threshold": round(T.sim_threshold, 3),
                    "domain_thresholds": {k: round(v, 3) for k, v in T.domain_thresholds.items()},
                })
        except Exception:
            pass
    _bg_executor.submit(_persist_settings)

    return {"status": "ok", "settings": {
        **changed,
        "sim_threshold": round(T.sim_threshold, 3),
        "domain_thresholds": {k: round(v, 3) for k, v in T.domain_thresholds.items()},
    }}

def _get_user_from_supabase_token(request: Request) -> dict:
    """Extract and verify Supabase JWT from Authorization header. Returns user profile dict."""
    from auth import verify_token
    from database import get_user_by_id

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    user["id"] = str(user["id"])
    return user


@app.get("/api/keys/current")
@limiter.limit("30/minute")
def get_current_api_key(request: Request):
    """Get the current user's API key (requires Supabase JWT)."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import list_api_keys

        api_keys = list_api_keys(user_id=user["id"])
        if api_keys:
            active_keys = [k for k in api_keys if k.get('is_active')]
            if active_keys:
                key = active_keys[0]
                return {
                    "api_key": key.get('api_key'),
                    "tenant_id": key.get('tenant_id'),
                    "plan": key.get('plan', 'free'),
                    "created_at": str(key.get('created_at', '')),
                    "exists": True
                }

        return {"exists": False, "message": "No API key found. Generate one in Settings."}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Get API key failed | error={str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get API key")

@app.post("/api/keys/generate")
@limiter.limit("5/hour")
def generate_api_key_endpoint(
    request: Request,
    tenant: Optional[str] = Query(None),
    length: int = Query(32, ge=16, le=64),
    plan: Optional[str] = Query(None),
    label: Optional[str] = Query(None),
    scope: str = Query("read-write"),
):
    """Generate a new API key for the authenticated user (requires Supabase JWT)."""
    try:
        user = _get_user_from_supabase_token(request)
        user_id = user["id"]
        from api_key_generator import generate_api_key
        from database import create_api_key, list_api_keys, get_api_key_info, get_user_orgs

        if scope not in {"read-only", "read-write"}:
            raise HTTPException(status_code=403, detail="Only read-only and read-write API key scopes are allowed")

        existing_keys = list_api_keys(user_id=user_id)
        if existing_keys and tenant is None:
            existing_key = existing_keys[0]
            return {
                "api_key": existing_key.get('api_key'),
                "tenant_id": existing_key.get('tenant_id'),
                "plan": existing_key.get('plan', 'free'),
                "created_at": str(existing_key.get('created_at', '')),
                "format": f"Bearer {existing_key.get('api_key')}",
                "message": "Using existing API key."
            }

        # Resolve org for user
        org_id = None
        resolved_plan = "free"
        org_slug = None
        try:
            orgs = get_user_orgs(user_id)
            if orgs:
                org = orgs[0]
                org_id = str(org["id"])
                resolved_plan = str(org.get("plan") or "free")
                org_slug = str(org.get("slug") or "").strip() or None
        except Exception:
            pass

        if org_slug:
            if tenant and tenant != org_slug:
                security_log.warning(
                    f"Blocked API key tenant override | user_id={user_id} | requested={tenant} | enforced={org_slug}"
                )
            tenant = org_slug
        if tenant is None:
            tenant = f"usr_{user_id[:8]}"
        if plan and plan != resolved_plan:
            security_log.warning(
                f"Blocked API key plan override | user_id={user_id} | requested={plan} | enforced={resolved_plan}"
            )

        api_key, tenant_id = generate_api_key(tenant=tenant, length=length, auto_tenant=False)
        result = create_api_key(
            api_key, tenant_id, user_id=user_id, plan=resolved_plan,
            org_id=org_id, scope=scope, label=label,
        )
        if not result:
            raise HTTPException(status_code=500, detail="Failed to save API key to database")

        saved_key = get_api_key_info(api_key)
        if not saved_key:
            raise HTTPException(status_code=500, detail="API key was not saved properly")

        # Audit log
        try:
            from database import log_audit
            log_audit(
                org_id=org_id, user_id=user_id, action="api_key.created",
                resource_type="api_key", resource_id=api_key[:20],
                details={"scope": scope, "label": label, "plan": resolved_plan},
                ip_address=request.client.host if request.client else None,
            )
        except Exception:
            pass

        app_log.info(f"API key generated | tenant={tenant_id} | user_id={user_id} | org={org_id}")

        return {
            "api_key": api_key,
            "tenant_id": tenant_id,
            "org_id": org_id,
            "plan": resolved_plan,
            "scope": scope,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "format": f"Bearer {api_key}",
            "message": "API key generated successfully. Save this key securely."
        }
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"API key generation failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate API key: {str(e)}")

# -----------------------------
# Authentication endpoints (Supabase JWT)
# Signup / login / password-reset are handled entirely by the
# frontend via @supabase/supabase-js. The backend only verifies tokens.
# -----------------------------

def _auto_provision_org(user: dict) -> Optional[dict]:
    """Auto-create org + API key for new users who have no org yet."""
    try:
        from database import create_organization, create_api_key
        import secrets

        email = user.get("email", "")
        name = user.get("name", email.split("@")[0])
        # Create org slug from email prefix
        slug = re.sub(r'[^a-z0-9]', '', email.split("@")[0].lower())[:20] or "user"
        # Ensure unique slug
        slug = f"{slug}_{secrets.token_hex(3)}"

        org = create_organization(
            name=f"{name}'s Workspace",
            slug=slug,
            owner_user_id=user["id"],
            plan="free",
        )
        if org:
            # Generate API key
            key_suffix = secrets.token_urlsafe(24)
            api_key = f"sc-{slug}-{key_suffix}"
            tenant_id = slug
            create_api_key(
                api_key=api_key,
                tenant_id=tenant_id,
                user_id=user["id"],
                plan="free",
                org_id=str(org["id"]),
                scope="read-write",
                label="Default key (auto-created)",
            )
            app_log.info(f"Auto-provisioned org={slug} + API key for user={user['id']}")

            # Send welcome email (non-blocking)
            try:
                from email_service import send_welcome_email
                _bg_executor.submit(send_welcome_email, email, name)
            except Exception:
                pass

            return org
    except Exception as e:
        error_log.warning(f"Auto-provision failed for user={user.get('id')}: {e}")
    return None


@app.get("/api/auth/me")
@limiter.limit("30/minute")
def get_current_user(request: Request):
    """Get current authenticated user info from Supabase JWT."""
    try:
        user = _get_user_from_supabase_token(request)
        orgs = []
        try:
            from database import get_user_orgs
            orgs = get_user_orgs(user["id"])
        except Exception:
            pass

        # Auto-provision org + API key for new users
        if not orgs:
            new_org = _auto_provision_org(user)
            if new_org:
                try:
                    from database import get_user_orgs
                    orgs = get_user_orgs(user["id"])
                except Exception:
                    pass

        return {
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "is_admin": user.get('is_admin', False),
            "created_at": str(user.get('created_at', '')),
            "orgs": [{
                "id": str(o["id"]),
                "name": o["name"],
                "slug": o["slug"],
                "plan": o.get("plan", "free"),
                "role": o.get("role", "member"),
            } for o in orgs],
        }
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Get current user failed | error={str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

class OpenAIKeyRequest(BaseModel):
    api_key: str

    @validator("api_key")
    def validate_key(cls, v):
        if len(v) > 256:
            raise ValueError("API key too long")
        if not v.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format")
        return v

@app.post("/api/users/openai-key")
@limiter.limit("10/hour")
def set_user_openai_key_endpoint(request: OpenAIKeyRequest, auth_request: Request):
    """Set user's OpenAI API key (requires Supabase JWT)."""
    try:
        user = _get_user_from_supabase_token(auth_request)
        from database import set_user_openai_key
        from encryption import encrypt_api_key, is_api_key_encryption_configured

        if not is_api_key_encryption_configured():
            raise HTTPException(
                status_code=503,
                detail="OpenAI key storage is not configured. Set ENCRYPTION_KEY and ENCRYPTION_SALT first."
            )

        try:
            encrypted_key = encrypt_api_key(request.api_key)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        success = set_user_openai_key(user["id"], encrypted_key)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save OpenAI API key")

        app_log.info(f"OpenAI API key set | user_id={user['id']}")
        return {"message": "OpenAI API key saved successfully", "key_set": True}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Set OpenAI key failed | error={str(e)}")
        raise HTTPException(status_code=500, detail="Failed to set OpenAI API key")

@app.get("/api/users/openai-key")
@limiter.limit("30/minute")
def get_user_openai_key_status(request: Request):
    """Check if user has OpenAI API key set (requires Supabase JWT)."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import get_user_openai_key_encrypted

        encrypted_key = get_user_openai_key_encrypted(user["id"])
        if encrypted_key:
            try:
                from encryption import decrypt_api_key
                decrypted = decrypt_api_key(encrypted_key)
                preview = "sk-..." + decrypted[-4:] if len(decrypted) > 4 else "sk-***"
            except Exception:
                preview = "sk-***"
            return {"key_set": True, "key_preview": preview}
        return {"key_set": False, "message": "No OpenAI API key configured"}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Get OpenAI key status failed | error={str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get OpenAI API key status")

@app.delete("/api/users/openai-key")
@limiter.limit("10/hour")
def remove_user_openai_key(request: Request):
    """Remove user's OpenAI API key (requires Supabase JWT)."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import clear_user_openai_key

        success = clear_user_openai_key(user["id"])
        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove OpenAI API key")

        app_log.info(f"OpenAI API key removed | user_id={user['id']}")
        return {"message": "OpenAI API key removed successfully", "key_set": False}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Remove OpenAI key failed | error={str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove OpenAI API key")

@app.post("/api/auth/logout")
@limiter.limit("10/minute")
def logout(request: Request):
    """Logout (client clears Supabase session)."""
    return {"message": "Logged out successfully"}

# ── Organization endpoints ──

class CreateOrgRequest(BaseModel):
    name: str
    slug: str

    @validator("name")
    def validate_name(cls, v):
        if not v or len(v) > 255:
            raise ValueError("name must be 1-255 characters")
        return v.strip()

    @validator("slug")
    def validate_slug(cls, v):
        import re as _re
        if not v or len(v) > 100:
            raise ValueError("slug must be 1-100 characters")
        if not _re.match(r'^[a-z0-9][a-z0-9-]*$', v):
            raise ValueError("slug must be lowercase alphanumeric with hyphens")
        return v

@app.post("/api/orgs")
@limiter.limit("10/hour")
def create_org(body: CreateOrgRequest, request: Request):
    """Create a new organization (requires Supabase JWT)."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import create_organization, log_audit
        org = create_organization(body.name, body.slug, user["id"])
        if not org:
            raise HTTPException(status_code=400, detail="Could not create organization")
        log_audit(
            org_id=str(org["id"]), user_id=user["id"], action="org.created",
            resource_type="organization", resource_id=str(org["id"]),
            ip_address=request.client.host if request.client else None,
        )
        return {"org": {k: str(v) for k, v in org.items()}}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Create org failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/orgs")
@limiter.limit("30/minute")
def list_user_orgs(request: Request):
    """List organizations for the current user."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import get_user_orgs
        orgs = get_user_orgs(user["id"])
        return {"orgs": [{k: str(v) for k, v in o.items()} for o in orgs]}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"List orgs failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")

class InviteMemberRequest(BaseModel):
    email: str
    role: str = "member"

    @validator("email")
    def validate_email(cls, v):
        if not v or len(v) > 255 or "@" not in v:
            raise ValueError("invalid email address")
        return v.strip().lower()

    @validator("role")
    def validate_role(cls, v):
        if v not in ("owner", "admin", "member"):
            raise ValueError("role must be owner, admin, or member")
        return v

@app.post("/api/orgs/{org_id}/members")
@limiter.limit("20/hour")
def invite_member(org_id: str, body: InviteMemberRequest, request: Request):
    """Add a member to an organization."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import add_org_member, get_user_by_email, log_audit

        _require_org_membership(user["id"], org_id, min_role="admin")
        target = get_user_by_email(body.email)
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        ok = add_org_member(org_id, str(target["id"]), body.role)
        if not ok:
            raise HTTPException(status_code=400, detail="Already a member")
        log_audit(
            org_id=org_id, user_id=user["id"], action="member.added",
            resource_type="org_member", resource_id=str(target["id"]),
            details={"role": body.role, "email": body.email},
            ip_address=request.client.host if request.client else None,
        )
        return {"message": f"Added {body.email} as {body.role}"}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Invite member failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")

class OrgSettingsUpdate(BaseModel):
    webhook_url: Optional[str] = None

    @validator("webhook_url")
    def validate_webhook_url(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) > 2048:
            raise ValueError("webhook URL too long (max 2048)")
        if not v.startswith(("https://", "http://")):
            raise ValueError("webhook URL must start with https:// or http://")
        return v

@app.patch("/api/orgs/{org_id}/settings")
@limiter.limit("20/minute")
def update_org_settings_endpoint(org_id: str, body: OrgSettingsUpdate, request: Request):
    """Update organization settings (e.g. webhook URL for cache events)."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import update_org_settings

        _require_org_membership(user["id"], org_id, min_role="admin")
        updates = {}
        if body.webhook_url is not None:
            updates["webhook_url"] = body.webhook_url.strip() or None
        if updates:
            update_org_settings(org_id, updates)
        return {"message": "Settings updated"}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Update org settings failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/orgs/{org_id}/audit")
@limiter.limit("30/minute")
def get_audit_logs(org_id: str, request: Request, limit: int = Query(50, ge=1, le=500)):
    """Get audit logs for an organization."""
    try:
        user = _get_user_from_supabase_token(request)
        _require_org_membership(user["id"], org_id, min_role="member")
        from database import get_db_connection
        from psycopg2.extras import RealDictCursor
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                """SELECT id, org_id, user_id, action, resource_type, resource_id,
                          details, ip_address, created_at
                   FROM audit_logs WHERE org_id = %s
                   ORDER BY created_at DESC LIMIT %s""",
                (org_id, limit)
            )
            logs = [dict(r) for r in cur.fetchall()]
        return {"audit_logs": [{k: str(v) for k, v in row.items()} for row in logs]}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Audit logs failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")

def _sse_chunk(content: str, chunk_id: str) -> str:
    """Format a content delta as OpenAI SSE chunk."""
    obj = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": CHAT_MODEL,
        "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
    }
    return f"data: {json.dumps(obj)}\n\n"


@app.post("/v1/chat/completions")
@limiter.limit("200/minute")
def openai_compatible(request: Request, body: ChatRequest, tenant: str = Depends(get_tenant_from_key)):
    """OpenAI-compatible endpoint for zero-code integration.
    
    Point your OpenAI client at this server:
        client = openai.OpenAI(base_url="https://api.semantys.ai/v1", api_key="sc-...")
    Supports stream=True for streaming responses.
    """
    _ctx = getattr(request.state, 'api_ctx', None) or _current_api_key_var.get()
    _require_scope(request, "read-write")

    # Enforce plan limits (Redis counter for speed, DB fallback)
    try:
        from billing import get_plan_limits
        from redis_cache import increment_monthly_usage
        plan = _ctx.get("plan", "free")
        current_requests = increment_monthly_usage(tenant)
        if current_requests == -1:
            # Redis unavailable — fall back to DB (slower)
            from database import get_usage_stats
            usage = get_usage_stats(tenant, days=30)
            current_requests = int(usage.get("total_requests", 0))
        limits = get_plan_limits(plan)
        max_req = limits.get("max_requests_month", 1000)
        if current_requests > max_req:
            raise HTTPException(
                status_code=429,
                detail=f"Monthly request limit reached for your '{plan}' plan ({current_requests}/{max_req}). "
                       f"Upgrade at /settings to continue.",
            )
    except HTTPException:
        raise
    except Exception:
        pass  # If billing check fails, allow the request through

    # --- Credits check (Semantys Key users only — BYOK users skip this) ---
    try:
        from billing import is_byok_user, get_credits_balance
        _user_id_for_check = _ctx.get("user_id")
        _org_id_for_check = _ctx.get("org_id")
        if _org_id_for_check and not is_byok_user(_user_id_for_check):
            balance = get_credits_balance(_org_id_for_check)
            if balance <= 0:
                raise HTTPException(
                    status_code=402,
                    detail="Insufficient credits. Add credits at /settings to continue using the Semantys API key. "
                           "Or add your own OpenAI key (BYOK) to avoid credit charges.",
                )
    except HTTPException:
        raise
    except Exception:
        pass  # If credits check fails, allow the request through

    # --- Input guard (runs before cache pipeline) ---
    from input_guard import guard_request
    raw_messages = [m.model_dump() for m in body.messages]
    messages, guard_err = guard_request(raw_messages, body.temperature, body.model)
    if guard_err:
        raise HTTPException(status_code=400, detail=guard_err)

    prompt_norm = SemanticCacheService.extract_cache_query(messages)

    try:
        user_id = _ctx.get("user_id")
        # Capture context values NOW — ContextVar may not propagate into generator/thread
        _captured_key = _ctx.get("key", "unknown")
        _captured_uid = _ctx.get("user_id")
        _captured_org = _ctx.get("org_id")
        chunk_id = f"chatcmpl-{hashlib.md5(str(time.time()).encode()).hexdigest()[:24]}"

        if body.stream:
            # Cache lookup BEFORE generator so metadata is available for response headers
            cached_ans, meta = svc.lookup(
                tenant, prompt_norm, messages, body.model, user_id=user_id,
            )

            def stream_generator():
                _log_key = _captured_key
                _log_uid = _captured_uid
                _log_org = _captured_org

                def _bg_log(hit_type, response_text="", similarity=0.0, latency_ms=0.0, p_hash=""):
                    try:
                        from database import log_usage
                        from billing import calculate_token_cost, is_byok_user, deduct_credits
                        _p_tokens = sum(len(m.get("content", "").split()) * 4 // 3 for m in raw_messages)
                        _c_tokens = len(response_text.split()) * 4 // 3 if response_text else 0
                        _tokens = _p_tokens + _c_tokens
                        _is_byok = is_byok_user(_log_uid)

                        # Cost calculation: BYOK users pay $0, Semantys Key users pay per-token on misses
                        if hit_type == "miss" and not _is_byok:
                            _cost = calculate_token_cost(_p_tokens, _c_tokens)
                            # Deduct from prepaid credits
                            if _log_org and _cost > 0:
                                deduct_credits(_log_org, _cost, reason="token_usage")
                        else:
                            _cost = 0.0

                        # Tokens saved tracking: on cache hits, record what would have been used
                        _tokens_saved = _tokens if hit_type != "miss" else 0
                        _cost_saved = calculate_token_cost(_p_tokens, _c_tokens) if hit_type != "miss" else 0.0

                        access_log.info(f"{tenant} | _bg_log | hit={hit_type} | key={_log_key[:20]} | org={_log_org} | tokens={_tokens} | byok={_is_byok}")
                        log_usage(
                            api_key=_log_key, tenant_id=tenant,
                            endpoint="/v1/chat/completions", request_count=1,
                            cache_hits=1 if hit_type != "miss" else 0,
                            cache_misses=1 if hit_type == "miss" else 0,
                            tokens_used=_tokens, cost_estimate=_cost,
                            user_id=_log_uid, org_id=_log_org,
                            decision=hit_type, similarity=similarity,
                            latency_ms=latency_ms, prompt_hash=p_hash,
                            tokens_saved=_tokens_saved, cost_saved=_cost_saved,
                            is_byok=_is_byok,
                        )
                    except Exception as _e:
                        error_log.warning(f"log_usage failed in stream: {_e}")
                        import traceback
                        error_log.warning(traceback.format_exc())

                def _fire_webhook(m):
                    try:
                        from webhooks import fire_cache_event
                        fire_cache_event(
                            _ctx.get("org_id"), tenant, "cache.decision",
                            {"hit": m["hit"], "similarity": m["similarity"], "latency_ms": m["latency_ms"]},
                        )
                    except Exception:
                        pass

                if cached_ans is not None:
                    # ── Cache hit: stream the cached response in larger chunks ──
                    access_log.info(f"{tenant} | /v1/chat/completions | stream | {meta['hit']} | {meta['latency_ms']}ms")
                    try:
                        _bg_log(meta["hit"], cached_ans,
                                similarity=float(meta.get("similarity", 0.0)),
                                latency_ms=float(meta.get("latency_ms", 0.0)),
                                p_hash=meta.get("prompt_hash", ""))
                    except Exception as _e2:
                        error_log.warning(f"direct _bg_log failed: {_e2}")
                    _bg_executor.submit(_fire_webhook, meta)
                    # Send cached text in word-sized chunks for a natural feel
                    words = cached_ans.split(' ')
                    for i, word in enumerate(words):
                        token = word if i == 0 else ' ' + word
                        yield _sse_chunk(token, chunk_id)
                else:
                    # ── Cache miss: real streaming from OpenAI ──
                    access_log.info(f"{tenant} | /v1/chat/completions | stream | miss | live")
                    full_response_parts = []
                    for token in call_llm_stream(messages, body.temperature, user_id, model=body.model):
                        full_response_parts.append(token)
                        yield _sse_chunk(token, chunk_id)
                    # Store the completed response in cache
                    full_response = "".join(full_response_parts)
                    meta["hit"] = "miss"
                    try:
                        _bg_log("miss", full_response,
                                similarity=0.0,
                                latency_ms=float(meta.get("latency_ms", 0.0)),
                                p_hash=meta.get("prompt_hash", ""))
                    except Exception as _e2:
                        error_log.warning(f"log_usage failed in stream: {_e2}")
                    _bg_executor.submit(_fire_webhook, meta)
                    svc.store_miss(
                        tenant, prompt_norm, full_response, messages,
                        body.model, ttl_seconds=body.ttl_seconds, user_id=user_id,
                        org_id=_log_org,
                    )

                # Finish SSE stream
                yield f"data: {json.dumps({'id': chunk_id, 'object': 'chat.completion.chunk', 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                    "X-Cache-Hit": str(meta.get("hit", "miss")),
                    "X-Cache-Similarity": str(meta.get("similarity", 0.0)),
                    "X-Cache-Latency": str(meta.get("latency_ms", 0.0)),
                    "X-Cache-Strategy": str(meta.get("strategy", "miss")),
                },
            )

        ans, meta = svc.query(
            tenant,
            prompt_norm,
            messages,
            body.model,
            ttl_seconds=body.ttl_seconds,
            temperature=body.temperature,
            user_id=user_id,
        )
        prompt_tokens = sum(len(m.content.split()) * 4 // 3 for m in body.messages)
        completion_tokens = len(ans.split()) * 4 // 3
        total_tokens = prompt_tokens + completion_tokens

        _log_key = _ctx.get("key", "unknown")
        _log_uid = _ctx.get("user_id")
        _log_org = _ctx.get("org_id")
        _log_hit = meta.get("hit")
        _log_tokens = total_tokens
        _log_p_tokens = prompt_tokens
        _log_c_tokens = completion_tokens
        def _bg_log():
            try:
                from database import log_usage
                from billing import calculate_token_cost, is_byok_user, deduct_credits
                _is_byok = is_byok_user(_log_uid)

                # Cost: BYOK = $0, Semantys Key = per-token on misses only
                if _log_hit == "miss" and not _is_byok:
                    _cost = calculate_token_cost(_log_p_tokens, _log_c_tokens)
                    if _log_org and _cost > 0:
                        deduct_credits(_log_org, _cost, reason="token_usage")
                else:
                    _cost = 0.0

                # Tokens saved: on cache hits, record what would have been used
                _tokens_saved = _log_tokens if _log_hit != "miss" else 0
                _cost_saved = calculate_token_cost(_log_p_tokens, _log_c_tokens) if _log_hit != "miss" else 0.0

                log_usage(
                    api_key=_log_key, tenant_id=tenant,
                    endpoint="/v1/chat/completions", request_count=1,
                    cache_hits=1 if _log_hit != "miss" else 0,
                    cache_misses=1 if _log_hit == "miss" else 0,
                    tokens_used=_log_tokens, cost_estimate=_cost,
                    user_id=_log_uid, org_id=_log_org,
                    decision=_log_hit,
                    similarity=float(meta.get("similarity", 0.0)),
                    latency_ms=float(meta.get("latency_ms", 0.0)),
                    prompt_hash=meta.get("prompt_hash", ""),
                    tokens_saved=_tokens_saved, cost_saved=_cost_saved,
                    is_byok=_is_byok,
                )
            except Exception:
                pass
        _bg_executor.submit(_bg_log)

        access_log.info(f"{tenant} | /v1/chat/completions | {meta['hit']} | sim={meta['similarity']:.3f} | {meta['latency_ms']}ms")

        if _prom:
            _prom.record_cache_request(tenant, meta.get("hit", "miss"), meta["latency_ms"] / 1000)
            _prom.record_tokens(tenant, body.model, prompt_tokens, completion_tokens)
            if meta.get("hit") != "miss":
                _prom.record_tokens_saved(tenant, prompt_tokens + completion_tokens)

        try:
            from webhooks import fire_cache_event
            fire_cache_event(
                _ctx.get("org_id"),
                tenant,
                "cache.decision",
                {"hit": meta["hit"], "similarity": meta["similarity"], "latency_ms": meta["latency_ms"]},
            )
        except Exception:
            pass
        return {
            "id": chunk_id,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": ans},
                "finish_reason": "stop",
                "logprobs": None,
            }],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            "system_fingerprint": f"semantys-{meta.get('hit', 'miss')}",
            "meta": meta,
        }
    except Exception as e:
        error_log.exception(f"{tenant} | /v1/chat/completions | error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


@app.get("/v1/models")
@limiter.limit("60/minute")
def list_models(request: Request, tenant: str = Depends(get_tenant_from_key)):
    """OpenAI-compatible models listing for proxy compatibility."""
    return {
        "object": "list",
        "data": [
            {"id": "gpt-4o-mini", "object": "model", "created": 1700000000, "owned_by": "semantys-cache"},
            {"id": "gpt-4o", "object": "model", "created": 1700000000, "owned_by": "semantys-cache"},
            {"id": "gpt-4", "object": "model", "created": 1700000000, "owned_by": "semantys-cache"},
            {"id": "gpt-3.5-turbo", "object": "model", "created": 1700000000, "owned_by": "semantys-cache"},
        ],
    }


# ── Billing endpoints ──

@app.get("/api/billing/plans")
@limiter.limit("30/minute")
def get_billing_plans(request: Request):
    """Get available billing plans and their limits."""
    from billing import PLANS, is_enabled
    return {"plans": PLANS, "stripe_enabled": is_enabled()}


@app.get("/api/billing/status")
@limiter.limit("30/minute")
def get_billing_status(request: Request):
    """Get billing status for the current user's org."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import get_user_orgs, get_usage_stats_by_org
        from billing import get_plan_limits
        orgs = get_user_orgs(user["id"])
        if not orgs:
            return {"plan": "free", "limits": get_plan_limits("free")}
        org = orgs[0]
        plan = org.get("plan", "free")
        
        # Get current usage by org_id (not slug)
        usage = {}
        try:
            usage = get_usage_stats_by_org(str(org["id"]), days=30)
        except Exception:
            pass

        total_requests = int(usage.get("total_requests", 0))
        # If usage_logs by org_id is empty, try by tenant_id from org's API keys
        if total_requests == 0:
            try:
                from database import get_db_connection, get_usage_stats
                from psycopg2.extras import RealDictCursor
                with get_db_connection() as conn:
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute(
                        "SELECT tenant_id FROM api_keys WHERE org_id = %s AND is_active = TRUE",
                        (str(org["id"]),)
                    )
                    for row in cur.fetchall():
                        tenant_usage = get_usage_stats(row["tenant_id"], days=30)
                        t_reqs = int(tenant_usage.get("total_requests", 0))
                        if t_reqs > 0:
                            total_requests += t_reqs
                            for k in ("total_hits", "total_misses", "total_tokens", "total_cost"):
                                usage[k] = int(usage.get(k, 0)) + int(tenant_usage.get(k, 0))
                    if total_requests > 0:
                        usage["total_requests"] = total_requests
            except Exception:
                pass

        total_hits = int(usage.get("total_hits", 0))
        total_misses = int(usage.get("total_misses", 0))
        total_cost = float(usage.get("total_cost", 0))
        total_tokens_saved = int(usage.get("total_tokens_saved", 0))
        total_cost_saved = float(usage.get("total_cost_saved", 0))

        # Savings estimate: use actual tracked cost_saved if available, else fallback
        if total_cost_saved > 0:
            estimated_savings_usd = round(total_cost_saved, 2)
        elif total_misses > 0 and total_cost > 0:
            avg_cost_per_request = total_cost / total_misses
            estimated_savings_usd = round(total_hits * avg_cost_per_request, 2)
        elif total_hits > 0:
            estimated_savings_usd = round(total_hits * 0.002, 2)
        elif total_requests > 0 and total_hits == 0 and total_misses == 0:
            estimated_hits = int(total_requests * 0.3)
            total_hits = estimated_hits
            estimated_savings_usd = round(estimated_hits * 0.002, 2)
        else:
            estimated_savings_usd = 0.0

        # Get credits balance
        credits_balance = 0.0
        try:
            from database import get_org_credits_balance
            credits_balance = get_org_credits_balance(str(org["id"]))
        except Exception:
            pass

        limits = get_plan_limits(plan)
        return {
            "org_id": str(org["id"]),
            "org_name": org["name"],
            "plan": plan,
            "limits": limits,
            "credits_balance": round(credits_balance, 6),
            "usage_30d": usage,
            "savings_estimate": {
                "cached_requests": total_hits,
                "total_requests": total_requests,
                "estimated_savings_usd": estimated_savings_usd,
                "tokens_saved": total_tokens_saved,
                "cost_saved_usd": round(total_cost_saved, 4),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Billing status failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


FRONTEND_URL = os.getenv("FRONTEND_URL", "")

class UpgradePlanRequest(BaseModel):
    plan: str
    success_url: str = ""
    cancel_url: str = ""

    @validator("plan")
    def validate_plan(cls, v):
        if v not in ("pro", "team"):
            raise ValueError("invalid plan")
        return v

    @validator("success_url", "cancel_url")
    def validate_urls(cls, v):
        if v and len(v) > 2048:
            raise ValueError("URL too long")
        return v

@app.post("/api/billing/upgrade")
@limiter.limit("5/hour")
def upgrade_plan(body: UpgradePlanRequest, request: Request):
    """Start a plan upgrade via Stripe Checkout."""
    try:
        user = _get_user_from_supabase_token(request)
        from billing import is_enabled, create_customer, create_checkout_session, STRIPE_PRICE_PRO
        
        if not is_enabled():
            # Stripe is not configured — paid upgrades require Stripe
            raise HTTPException(
                status_code=400,
                detail="Payments are not configured. Please contact support to upgrade your plan."
            )
        
        price_map = {
            "pro": STRIPE_PRICE_PRO,
        }
        price_id = price_map.get(body.plan)
        if not price_id:
            raise HTTPException(status_code=400, detail=f"Invalid plan: {body.plan}")
        
        from database import get_user_orgs, get_organization, update_org_settings
        orgs = get_user_orgs(user["id"])
        if not orgs:
            raise HTTPException(status_code=400, detail="No organization found")
        org = orgs[0]
        org_id = str(org["id"])
        org_name = org.get("name", "Semantys")
        user_email = user.get("email", "")
        
        org_full = get_organization(org_id)
        settings = (org_full.get("settings") if org_full else None) or {}
        customer_id = settings.get("stripe_customer_id")
        
        if not customer_id:
            customer_id = create_customer(org_id, org_name, user_email)
            if customer_id:
                update_org_settings(org_id, {"stripe_customer_id": customer_id})
        
        if not customer_id:
            raise HTTPException(status_code=500, detail="Failed to create Stripe customer")
        
        success_url = _resolve_billing_return_url(
            request,
            body.success_url,
            "/settings?billing=success",
        )
        cancel_url = _resolve_billing_return_url(
            request,
            body.cancel_url,
            "/settings?billing=cancel",
        )
        
        redirect_url = create_checkout_session(
            customer_id, price_id, success_url, cancel_url, org_id, body.plan
        )
        return {"message": f"Redirect to Stripe checkout for {body.plan}", "redirect_url": redirect_url}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Plan upgrade failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/billing/portal")
@limiter.limit("10/hour")
def billing_portal(request: Request):
    """Create a Stripe Customer Portal session for managing subscriptions."""
    try:
        user = _get_user_from_supabase_token(request)
        from billing import is_enabled, create_portal_session
        if not is_enabled():
            raise HTTPException(status_code=400, detail="Billing not configured")
        from database import get_user_orgs, get_organization
        orgs = get_user_orgs(user["id"])
        if not orgs:
            raise HTTPException(status_code=400, detail="No organization found")
        org_full = get_organization(str(orgs[0]["id"]))
        settings = (org_full.get("settings") if org_full else None) or {}
        customer_id = settings.get("stripe_customer_id")
        if not customer_id:
            raise HTTPException(status_code=400, detail="No active subscription found")
        return_url = _resolve_billing_return_url(request, "", "/settings")
        url = create_portal_session(customer_id, return_url)
        if not url:
            raise HTTPException(status_code=500, detail="Failed to create portal session")
        return {"portal_url": url}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Billing portal failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/billing/webhook")
@limiter.limit("100/hour")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events for subscription lifecycle."""
    try:
        from billing import handle_webhook
        payload = await request.body()
        sig = request.headers.get("stripe-signature", "")
        event = handle_webhook(payload, sig)
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook")

        event_type = event.get("type")
        obj = event.get("data") or {}
        app_log.info(f"Stripe webhook | type={event_type}")

        def _extract_org_id(data):
            metadata = data.get("metadata", {}) if isinstance(data, dict) else getattr(data, "metadata", None) or {}
            return metadata.get("org_id") if isinstance(metadata, dict) else None

        def _update_org_plan(org_id, plan):
            from database import get_db_connection
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("UPDATE organizations SET plan = %s WHERE id = %s", (plan, org_id))

        if event_type == "checkout.session.completed":
            org_id = _extract_org_id(obj)
            metadata = obj.get("metadata", {}) if isinstance(obj, dict) else {}
            plan = metadata.get("plan", "pro") if isinstance(metadata, dict) else "pro"
            if org_id:
                try:
                    _update_org_plan(org_id, plan)
                    # Grant starting credits for the new plan
                    from billing import get_plan_limits, add_credits
                    plan_limits = get_plan_limits(plan)
                    starting_credits = plan_limits.get("starting_credits_usd")
                    if starting_credits and starting_credits > 0:
                        add_credits(org_id, starting_credits, reason="starting_credits")
                    app_log.info(f"Webhook | plan upgraded to {plan} | org={org_id} | credits={starting_credits}")
                except Exception as e:
                    error_log.error(f"Webhook plan update failed | org={org_id} | error={e}")

        elif event_type in ("customer.subscription.deleted", "customer.subscription.canceled"):
            customer_id = obj.get("customer") if isinstance(obj, dict) else getattr(obj, "customer", None)
            if customer_id:
                try:
                    from database import get_db_connection
                    with get_db_connection() as conn:
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE organizations SET plan = 'free' WHERE settings->>'stripe_customer_id' = %s",
                            (customer_id,)
                        )
                    app_log.info(f"Webhook | subscription canceled | customer={customer_id}")
                except Exception as e:
                    error_log.error(f"Webhook subscription cancel failed | error={e}")

        elif event_type == "customer.subscription.updated":
            sub_status = obj.get("status") if isinstance(obj, dict) else getattr(obj, "status", None)
            cancel_at_end = obj.get("cancel_at_period_end") if isinstance(obj, dict) else False
            customer_id = obj.get("customer") if isinstance(obj, dict) else getattr(obj, "customer", None)
            if sub_status == "past_due" and customer_id:
                app_log.warning(f"Webhook | subscription past_due | customer={customer_id}")
            if cancel_at_end and customer_id:
                app_log.info(f"Webhook | subscription will cancel at period end | customer={customer_id}")

        elif event_type == "invoice.payment_failed":
            customer_id = obj.get("customer") if isinstance(obj, dict) else getattr(obj, "customer", None)
            app_log.warning(f"Webhook | invoice payment failed | customer={customer_id}")

        return {"received": True}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Webhook failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ── Credits endpoints ──

@app.get("/api/credits/balance")
@limiter.limit("30/minute")
def get_credits_balance_endpoint(request: Request):
    """Get the current prepaid credits balance for the user's org."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import get_user_orgs, get_org_credits_balance
        orgs = get_user_orgs(user["id"])
        if not orgs:
            return {"credits_balance": 0.0, "org_id": None}
        org_id = str(orgs[0]["id"])
        balance = get_org_credits_balance(org_id)
        return {"credits_balance": round(balance, 6), "org_id": org_id}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Credits balance failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


class AddCreditsRequest(BaseModel):
    amount_usd: float = 0.0

    @validator("amount_usd")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        if v > 500:
            raise ValueError("Maximum single top-up is $500")
        return round(v, 2)

@app.post("/api/credits/add")
@limiter.limit("3/hour")
def add_credits_endpoint(body: AddCreditsRequest, request: Request):
    """Add prepaid credits to the user's org. Requires admin privileges."""
    try:
        user = _get_user_from_supabase_token(request)
        # Only admins can add credits (regular users pay via Stripe)
        if not user.get("is_admin"):
            raise HTTPException(status_code=403, detail="Only admins can add credits directly. Use the billing page to purchase credits.")
        from database import get_user_orgs
        from billing import add_credits
        orgs = get_user_orgs(user["id"])
        if not orgs:
            raise HTTPException(status_code=400, detail="No organization found")
        org_id = str(orgs[0]["id"])
        success = add_credits(org_id, body.amount_usd, reason="topup")
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add credits")
        from database import get_org_credits_balance
        new_balance = get_org_credits_balance(org_id)
        return {"message": f"Added ${body.amount_usd:.2f} credits", "credits_balance": round(new_balance, 6)}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Add credits failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/credits/history")
@limiter.limit("30/minute")
def get_credits_history_endpoint(request: Request, limit: int = Query(50, ge=1, le=500)):
    """Get credits transaction history for the user's org."""
    try:
        user = _get_user_from_supabase_token(request)
        from database import get_user_orgs, get_credits_history
        orgs = get_user_orgs(user["id"])
        if not orgs:
            return {"transactions": []}
        org_id = str(orgs[0]["id"])
        history = get_credits_history(org_id, limit)
        return {"transactions": [{k: str(v) for k, v in row.items()} for row in history]}
    except HTTPException:
        raise
    except Exception as e:
        error_log.exception(f"Credits history failed | error={e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# -----------------------------
# Public product assistant (no auth required)
# -----------------------------

ASSISTANT_SYSTEM_PROMPT = """You are the Semantys AI product assistant. You ONLY answer questions about Semantys AI and its features. If a question is not related to Semantys AI, politely decline and redirect the user to ask about Semantys AI.

About Semantys AI:
- Semantys AI is an intelligent semantic caching layer that sits between your application and LLM providers (OpenAI, Anthropic, etc.)
- It reduces LLM API costs by up to 80% by caching and reusing responses for semantically similar queries.
- Response latency drops to under 50ms for cache hits vs 1-3 seconds for fresh LLM calls.
- It's a drop-in replacement: just change your base URL. Works with any OpenAI-compatible SDK.
- Multi-tier caching: L1 (Redis in-memory), L2 (FAISS vector similarity), L3 (PostgreSQL persistence).
- Features: real-time analytics dashboard, cache warmup, configurable similarity thresholds, TTL controls, multi-tenant support, API key management.
- SDKs available: Python, TypeScript, with integrations for LangChain, LlamaIndex, FastAPI, Express, Django.
- Enterprise ready: SOC-2 compliant architecture, rate limiting, audit logs, team management.
- Pricing: Free tier available, usage-based paid plans with credits system.
- Getting started: Sign up, get an API key, point your OpenAI SDK base URL to Semantys AI, done.

Keep answers concise (2-3 sentences max). Be friendly and helpful."""


class AssistantRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

    @validator("message")
    def message_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("message cannot be empty")
        if len(v) > 1000:
            raise ValueError("message too long (max 1000 chars)")
        return v.strip()

    @validator("history")
    def history_limit(cls, v):
        return v[-10:]  # keep last 10 messages


@app.post("/api/assistant")
@limiter.limit("20/minute")
def product_assistant(request: Request, body: AssistantRequest):
    """Public product assistant endpoint — no auth required.
    Rate-limited to prevent abuse."""
    try:
        messages = [{"role": "system", "content": ASSISTANT_SYSTEM_PROMPT}]
        for h in body.history:
            if h.get("role") in ("user", "assistant") and h.get("content"):
                messages.append({"role": h["role"], "content": h["content"][:500]})
        messages.append({"role": "user", "content": body.message})

        client = _get_openai_client(OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=300,
        )
        reply = response.choices[0].message.content or "Sorry, I couldn't generate a response."
        return {"reply": reply}
    except Exception as e:
        error_log.exception(f"Assistant endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Assistant unavailable")


# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    import sys
    port = int(os.getenv("PORT", 8000))
    
    # Log startup
    system_log.info(
        f"Server starting | port={port} | version=0.1.0 | "
        f"python={sys.version.split()[0]}"
    )
    
    app_log.info(f"Semantys AI Semantic Cache API running on http://0.0.0.0:{port}")
    app_log.info(f"Logs directory: {os.path.abspath('logs')}")
    app_log.info("Access logs: logs/access.log")
    app_log.info("Error logs: logs/errors.log")
    app_log.info("Semantic logs: logs/semantic_ops.log")
    app_log.info("Performance logs: logs/performance.log")
    app_log.info("Security logs: logs/security.log")
    app_log.info("System logs: logs/system.log")
    app_log.info("Application logs: logs/application.log")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        system_log.info("Server stopped by user")
    except Exception as e:
        error_log.exception(f"Server startup failed | error={str(e)}")
        raise
