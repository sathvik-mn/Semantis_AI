"""
Input validation and prompt injection guard.

Runs BEFORE the cache pipeline — does not touch the hot path.
"""

import re
import logging

logger = logging.getLogger("input_guard")

# --- Sanitization ---

# Control characters (except newline, tab, carriage return)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

def sanitize_text(text: str) -> str:
    """Strip null bytes and control characters from input."""
    return _CONTROL_CHAR_RE.sub("", text)


# --- Validation ---

MAX_MESSAGE_LENGTH = 30_000
MAX_MESSAGES_COUNT = 50
ALLOWED_ROLES = {"user", "assistant", "system"}

def validate_messages(messages: list[dict]) -> tuple[bool, str]:
    """Validate message list structure. Returns (ok, error_message)."""
    if not messages:
        return False, "Messages list cannot be empty"

    if len(messages) > MAX_MESSAGES_COUNT:
        return False, f"Too many messages (max {MAX_MESSAGES_COUNT})"

    has_user_message = False
    for i, msg in enumerate(messages):
        role = msg.get("role", "")
        content = msg.get("content", "")

        if role not in ALLOWED_ROLES:
            return False, f"Invalid role '{role}' in message {i}"

        if role == "user":
            has_user_message = True

        if not isinstance(content, str):
            return False, f"Message {i} content must be a string"

        if len(content) > MAX_MESSAGE_LENGTH:
            return False, f"Message {i} too long ({len(content)} chars, max {MAX_MESSAGE_LENGTH})"

    if not has_user_message:
        return False, "At least one user message is required"

    return True, ""


def validate_temperature(temp: float) -> tuple[bool, str]:
    """Validate temperature parameter."""
    if not (0.0 <= temp <= 2.0):
        return False, f"Temperature must be between 0.0 and 2.0, got {temp}"
    return True, ""


def validate_model(model: str) -> tuple[bool, str]:
    """Validate model name format."""
    if not model or len(model) > 100:
        return False, "Invalid model name"
    # Only allow alphanumeric, hyphens, dots, colons, slashes
    if not re.match(r"^[a-zA-Z0-9\-\.:/]+$", model):
        return False, f"Invalid characters in model name: {model}"
    return True, ""


# --- Prompt injection detection ---

# Patterns that indicate injection attempts
_INJECTION_PATTERNS = [
    # Direct instruction override
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|context)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?)", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?)", re.IGNORECASE),

    # System prompt extraction
    re.compile(r"(reveal|show|print|output|display|repeat)\s+(your|the|system)\s+(system\s+)?(prompt|instructions?|rules?)", re.IGNORECASE),
    re.compile(r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?|rules?)", re.IGNORECASE),

    # Role manipulation
    re.compile(r"you\s+are\s+now\s+(a|an|in)\s+", re.IGNORECASE),
    re.compile(r"(pretend|act)\s+(like\s+)?you\s+are\s+", re.IGNORECASE),
    re.compile(r"switch\s+to\s+(\w+\s+)?mode", re.IGNORECASE),
    re.compile(r"enter\s+(developer|debug|admin|root|sudo|jailbreak)\s+mode", re.IGNORECASE),

    # Delimiter injection (trying to break out of user message context)
    re.compile(r"<\|?(system|im_start|im_end|endoftext)\|?>", re.IGNORECASE),
    re.compile(r"\[INST\]|\[/INST\]|\[SYS\]|\[/SYS\]", re.IGNORECASE),

    # Data exfiltration
    re.compile(r"(send|post|fetch|curl|wget|http)\s+.*(api[_\s]?key|secret|token|password|credentials)", re.IGNORECASE),
]

# Less severe — just flag but don't block
_SUSPICIOUS_PATTERNS = [
    re.compile(r"do\s+not\s+follow\s+(your|the)\s+(rules|guidelines)", re.IGNORECASE),
    re.compile(r"override\s+(your|the|all)\s+(safety|content)\s+(filters?|guidelines?)", re.IGNORECASE),
]


def check_prompt_injection(text: str) -> tuple[bool, str]:
    """
    Check text for prompt injection patterns.
    Returns (is_safe, reason).

    Note: This is a heuristic guard — it catches common injection patterns
    but is not foolproof. It's a defense-in-depth layer, not a silver bullet.
    """
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            logger.warning(f"Prompt injection blocked: matched pattern '{match.group()}'")
            return False, "Request blocked: potentially unsafe content detected"

    for pattern in _SUSPICIOUS_PATTERNS:
        match = pattern.search(text)
        if match:
            logger.info(f"Suspicious prompt detected (allowed): '{match.group()}'")

    return True, ""


def guard_request(messages: list[dict], temperature: float, model: str) -> tuple[list[dict], str]:
    """
    Full input guard pipeline. Returns (sanitized_messages, error_message).
    Empty error_message means all checks passed.
    """
    # 1. Validate structure
    ok, err = validate_messages(messages)
    if not ok:
        return messages, err

    ok, err = validate_temperature(temperature)
    if not ok:
        return messages, err

    ok, err = validate_model(model)
    if not ok:
        return messages, err

    # 2. Sanitize content
    sanitized = []
    for msg in messages:
        sanitized.append({
            **msg,
            "content": sanitize_text(msg["content"]),
        })

    # 3. Check for prompt injection in user messages
    for msg in sanitized:
        if msg.get("role") == "user":
            ok, err = check_prompt_injection(msg["content"])
            if not ok:
                return sanitized, err

    return sanitized, ""
