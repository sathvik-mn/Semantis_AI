"""
Spelling Correction Module for Semantys AI

Fast spelling correction using SymSpell (Symmetric Delete algorithm).
Runs in ~0.1ms per query — negligible latency impact with significant
similarity improvement on misspelled user queries.

Falls back gracefully to no-op if symspellpy is not installed.
"""
import os
import logging
import threading
from typing import Optional

logger = logging.getLogger("semantys.spelling")

_symspell = None
_symspell_lock = threading.Lock()
_symspell_available: Optional[bool] = None

# Maximum edit distance for corrections (2 is standard — catches most typos)
MAX_EDIT_DISTANCE = int(os.getenv("SPELLING_MAX_EDIT_DISTANCE", "2"))
# Prefix length for SymSpell (performance tuning — 7 is optimal for English)
PREFIX_LENGTH = int(os.getenv("SPELLING_PREFIX_LENGTH", "7"))
# Whether spelling correction is enabled
SPELLING_ENABLED = os.getenv("SPELLING_ENABLED", "true").lower() == "true"


def _get_symspell():
    """Lazy-load SymSpell with English frequency dictionary."""
    global _symspell, _symspell_available
    if _symspell_available is False:
        return None
    if _symspell is not None:
        return _symspell
    with _symspell_lock:
        if _symspell is not None:
            return _symspell
        if _symspell_available is False:
            return None
        try:
            from symspellpy import SymSpell, Verbosity  # noqa: F401
            import pkg_resources

            sym = SymSpell(max_dictionary_edit_distance=MAX_EDIT_DISTANCE, prefix_length=PREFIX_LENGTH)

            # Load the built-in frequency dictionary from symspellpy package
            dict_path = pkg_resources.resource_filename("symspellpy", "frequency_dictionary_en_82_765.txt")
            if os.path.exists(dict_path):
                sym.load_dictionary(dict_path, term_index=0, count_index=1)
            else:
                # Fallback: try the frequency_bigramdictionary too
                logger.warning(f"SymSpell dictionary not found at {dict_path}")
                _symspell_available = False
                return None

            # Also load bigram dictionary for compound word correction
            bigram_path = pkg_resources.resource_filename("symspellpy", "frequency_bigramdictionary_en_243_342.txt")
            if os.path.exists(bigram_path):
                sym.load_bigram_dictionary(bigram_path, term_index=0, count_index=2)

            _symspell = sym
            _symspell_available = True
            logger.info("SymSpell spelling corrector loaded | max_edit_distance=%d", MAX_EDIT_DISTANCE)
            return _symspell
        except ImportError:
            _symspell_available = False
            logger.info("symspellpy not installed — spelling correction disabled. Install with: pip install symspellpy")
            return None
        except Exception as e:
            _symspell_available = False
            logger.warning("SymSpell init failed: %s — spelling correction disabled", e)
            return None


def correct_spelling(text: str) -> str:
    """Correct spelling in the given text. Returns original text if
    symspellpy is unavailable or correction fails.

    Uses lookup_compound for multi-word correction which handles:
    - Word-level typos: "artifical inteligence" -> "artificial intelligence"
    - Concatenated words: "whatismachinelearning" -> "what is machine learning"
    - Split words: "ma chine learn ing" -> "machine learning"

    Performance: ~0.05-0.2ms per query (negligible).
    """
    if not SPELLING_ENABLED or not text or not text.strip():
        return text

    sym = _get_symspell()
    if sym is None:
        return text

    try:
        from symspellpy import Verbosity

        # Use lookup_compound for multi-word correction
        suggestions = sym.lookup_compound(text, max_edit_distance=MAX_EDIT_DISTANCE)
        if suggestions and suggestions[0].distance > 0:
            corrected = suggestions[0].term
            # Sanity check: don't accept corrections that are wildly different
            # (more than 30% of characters changed)
            if len(corrected) > 0:
                orig_set = set(text.lower().replace(" ", ""))
                corr_set = set(corrected.lower().replace(" ", ""))
                # If the correction changes too many characters, keep original
                overlap = len(orig_set & corr_set) / max(len(orig_set | corr_set), 1)
                if overlap < 0.5:
                    return text
            logger.debug("Spelling corrected: '%s' -> '%s' (distance=%d)", text, corrected, suggestions[0].distance)
            return corrected
        return text
    except Exception as e:
        logger.debug("Spelling correction failed (non-fatal): %s", e)
        return text


def correct_word(word: str) -> str:
    """Correct a single word. Useful for targeted corrections."""
    if not SPELLING_ENABLED or not word or not word.strip():
        return word

    sym = _get_symspell()
    if sym is None:
        return word

    try:
        from symspellpy import Verbosity
        suggestions = sym.lookup(word, Verbosity.CLOSEST, max_edit_distance=MAX_EDIT_DISTANCE)
        if suggestions and suggestions[0].distance > 0 and suggestions[0].distance <= MAX_EDIT_DISTANCE:
            return suggestions[0].term
        return word
    except Exception:
        return word


def is_available() -> bool:
    """Check if spelling correction is available."""
    return _get_symspell() is not None
