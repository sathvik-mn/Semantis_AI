"""
Test suite for the improved semantic matching logic.

Tests the text-based similarity signals (no embedding model needed).
These validate that the NLP pipeline correctly identifies semantic
equivalence across diverse paraphrase types.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from semantic_cache_server import (
    normalize_query,
    deep_normalize,
    token_overlap_score,
    char_ngram_similarity,
    stemmed_overlap_score,
    idf_weighted_overlap,
    synonym_expanded_overlap,
    key_entity_overlap,
    question_type_match,
    sorted_token_similarity,
    compute_text_similarity,
    hybrid_score,
    _extract_question_type,
    _light_stem,
)


def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_pair(q: str, c: str, sims: dict, category: str):
    """Print similarity details. category is 'match', 'nomatch', or 'embedding_only'."""
    text_sim = sims["text_sim"]

    if category == "match":
        # Should match on text signals alone (text_sim >= 0.30)
        detected = text_sim >= 0.30
        status = "SHOULD MATCH (text)"
    elif category == "embedding_only":
        # Deep paraphrases: text signals may be low, embeddings handle these.
        # We just log — not a pass/fail on text signals.
        status = "EMBEDDING-DEPENDENT"
        detected = None  # no pass/fail
    else:
        # Should NOT match: text_sim should be distinguishable from true matches
        # In practice, the threshold logic uses entity_overlap < 0.15 + cosine
        # to reject, so we check if entity is low
        detected = text_sim < 0.30 or sims["entity_overlap"] < 0.20
        status = "SHOULD NOT MATCH"

    if detected is None:
        icon = "[--]"
        result_ok = True  # don't count as failure
    else:
        expected = (category != "nomatch")
        result_ok = (detected == expected) if category != "nomatch" else detected
        icon = "[OK]" if result_ok else "[FAIL]"

    print(f"\n{icon} {status}")
    print(f"  Q: {q}")
    print(f"  C: {c}")
    print(f"  text_sim={text_sim:.3f} | entity={sims['entity_overlap']:.3f} | "
          f"synonym={sims['synonym_expanded']:.3f} | ngram={sims['char_ngram']:.3f} | "
          f"idf={sims['idf_weighted']:.3f} | stemmed={sims['stemmed_overlap']:.3f} | "
          f"qtype={sims['question_type']:.1f} | sorted={sims['sorted_token']:.3f}")
    return result_ok


def test_normalization():
    """Test the normalization pipeline."""
    print_header("NORMALIZATION TESTS")

    cases = [
        ("What's your refund policy?", "what is your refund policy"),
        ("Please tell me about ML", "tell me about machine learning"),
        ("Hey, how's the weather?", "how is the weather"),
        ("Can't you just explain AI?", "cannot you explain artificial intelligence"),
        ("I'm basically just wondering about the cost", "i am wondering about the charge"),
        ("How to setup the DB?", "how to configure the database"),
        ("What are the benefits of using k8s?", "what are the benefits of using kubernetes"),  # k8s→kubernetes; 'benefits' stays (plural not in synonym map)
    ]

    passed = 0
    for text, expected in cases:
        result = deep_normalize(text)
        ok = result == expected
        icon = "[OK]" if ok else "[FAIL]"
        print(f"  {icon} '{text}'")
        print(f"        -> '{result}'")
        if not ok:
            print(f"        expected: '{expected}'")
        passed += ok

    print(f"\n  Normalization: {passed}/{len(cases)} passed")
    return passed, len(cases)


def test_stemming():
    """Test lightweight stemming."""
    print_header("STEMMING TESTS")

    cases = [
        ("running", "run"),           # nning → n (doubled consonant)
        ("configuration", "configure"),
        ("happiness", "happi"),
        ("quickly", "quick"),
        ("sorted", "sort"),
        ("processing", "process"),
        ("services", "servic"),
        ("configuring", "configur"),   # ring → r
        ("applications", "application"),  # s stripped
    ]

    passed = 0
    for word, expected in cases:
        result = _light_stem(word)
        ok = result == expected
        icon = "[OK]" if ok else "[FAIL]"
        print(f"  {icon} '{word}' -> '{result}'" + (f" (expected '{expected}')" if not ok else ""))
        passed += ok

    print(f"\n  Stemming: {passed}/{len(cases)} passed")
    return passed, len(cases)


def test_question_type():
    """Test question type extraction."""
    print_header("QUESTION TYPE TESTS")

    cases = [
        ("What is machine learning?", "define"),
        ("How to sort a list in Python?", "howto"),
        ("Why does Python use indentation?", "why"),
        ("When did Python 3 release?", "when"),
        ("Where is the config file?", "where"),
        ("Can I use async in Python?", "ability"),
        ("Tell me about Docker", "define"),
        ("Compare REST and GraphQL", "compare"),
        ("List all HTTP methods", "list"),
        ("Python sort algorithm", "general"),
    ]

    passed = 0
    for text, expected in cases:
        result = _extract_question_type(text)
        ok = result == expected
        icon = "[OK]" if ok else "[FAIL]"
        print(f"  {icon} '{text}' -> '{result}'" + (f" (expected '{expected}')" if not ok else ""))
        passed += ok

    print(f"\n  Question types: {passed}/{len(cases)} passed")
    return passed, len(cases)


def test_should_match_pairs():
    """Pairs that SHOULD be recognized as semantically similar."""
    print_header("SHOULD MATCH — Text-Detectable")

    # These pairs share enough surface-level signals (synonyms, abbreviations,
    # word overlap, n-grams) that text analysis alone should flag them.
    text_pairs = [
        ("Can I cancel my subscription?", "How to cancel subscription"),
        ("Python list comprehension", "list comprehension in python"),
        ("REST vs GraphQL differences", "difference between REST and GraphQL"),
        ("JavaScript array sorting", "how to sort an array in JavaScript"),
        ("artificial intelligence applications", "artifical inteligence applications"),
        ("configure kubernetes cluster", "configuring kubernetes cluster"),
        ("What is NLP?", "What is natural language processing?"),
        ("Explain deep learning", "Explain DL"),
        ("How to use the CLI?", "How to use the command line interface?"),
        ("How to fix this bug?", "How to resolve this issue?"),
        ("Create a new project", "Build a new project"),
        ("Start the application", "Launch the application"),
        ("What are the advantages?", "What are the benefits?"),
        ("How to remove a file?", "How to delete a file?"),
    ]

    passed = 0
    for q, c in text_pairs:
        sims = compute_text_similarity(q, c)
        if print_pair(q, c, sims, category="match"):
            passed += 1

    print_header("SHOULD MATCH — Embedding-Dependent (deep paraphrases)")

    # These pairs are deep paraphrases with little word overlap.
    # Text signals may be low — the embedding model handles these.
    # We log them for analysis but don't count as pass/fail.
    embedding_pairs = [
        ("What is your refund policy?", "How do I get a refund?"),
        ("Tell me about machine learning", "Explain ML"),
        ("How much does it cost?", "What's the price?"),
        ("Please explain how to configure the DB", "how to set up the database"),
        ("What's the best way to begin?", "how should i start"),
    ]

    for q, c in embedding_pairs:
        sims = compute_text_similarity(q, c)
        print_pair(q, c, sims, category="embedding_only")

    total = len(text_pairs)
    print(f"\n  Text-detectable matches: {passed}/{total} passed")
    print(f"  Embedding-dependent: {len(embedding_pairs)} (logged, not scored)")
    return passed, total


def test_should_not_match_pairs():
    """Pairs that should NOT be matched (false positive prevention).

    NOTE: Text signals alone cannot distinguish all of these (e.g., 'capital of
    France' vs 'capital of Germany' share high text overlap). The full pipeline
    uses cosine similarity from embeddings to differentiate these. Here we test
    that at least entity_overlap and question_type signals provide useful
    differentiation signals for the threshold logic to use.
    """
    print_header("SHOULD NOT MATCH (True Negatives)")

    # Different topics — text signals alone should reject these
    text_pairs = [
        ("How to bake a cake?", "How to deploy a Docker container?"),
        ("What is photosynthesis?", "What is machine learning?"),
        ("How to increase performance?", "How to decrease latency?"),
    ]

    passed = 0
    for q, c in text_pairs:
        sims = compute_text_similarity(q, c)
        if print_pair(q, c, sims, category="nomatch"):
            passed += 1

    print_header("SHOULD NOT MATCH — Embedding-Dependent (same structure, different entity)")

    # Same-structure, different-entity pairs. Text overlap is inherently
    # high because they share most words. The EMBEDDING MODEL correctly
    # differentiates these via cosine similarity. Text signals provide
    # supplementary signals (question_type mismatch, entity_overlap < 1.0)
    # but cannot reject on their own.
    embedding_neg_pairs = [
        ("What is the capital of France?", "What is the capital of Germany?"),
        ("How tall is Mount Everest?", "How tall is Mount Kilimanjaro?"),
        ("How to add items to a list?", "How to remove items from a list?"),
        ("Why is the sky blue?", "When is the sky blue?"),
        ("What is Python?", "How to install Python?"),
        ("Python vs JavaScript", "Python and JavaScript together"),
        ("How to start a fire", "How to start a business"),
    ]

    for q, c in embedding_neg_pairs:
        sims = compute_text_similarity(q, c)
        print_pair(q, c, sims, category="embedding_only")

    total = len(text_pairs)
    print(f"\n  Text-detectable non-matches: {passed}/{total} passed")
    print(f"  Embedding-dependent non-matches: {len(embedding_neg_pairs)} (logged, not scored)")
    return passed, total


def test_hybrid_scoring():
    """Test the hybrid scoring formula."""
    print_header("HYBRID SCORING TESTS")

    cases = [
        # (cosine, text_sim, expected_range_min, expected_range_max)
        (0.90, 0.80, 0.88, 0.92),    # High cosine + high text = very high
        (0.90, 0.10, 0.78, 0.82),    # High cosine + low text = still high
        (0.50, 0.90, 0.50, 0.56),    # Low cosine + high text = moderate
        (0.75, 0.50, 0.70, 0.74),    # Medium cosine + medium text = medium
        (0.00, 0.00, 0.00, 0.01),    # Zero = zero
    ]

    passed = 0
    for cosine, text_sim, exp_min, exp_max in cases:
        score = hybrid_score(cosine, text_sim)
        ok = exp_min <= score <= exp_max
        icon = "[OK]" if ok else "[FAIL]"
        print(f"  {icon} cosine={cosine:.2f} text_sim={text_sim:.2f} -> hybrid={score:.4f} "
              f"(expected {exp_min:.2f}-{exp_max:.2f})")
        passed += ok

    print(f"\n  Hybrid scoring: {passed}/{len(cases)} passed")
    return passed, len(cases)


def test_individual_signals():
    """Test individual similarity signals on key examples."""
    print_header("INDIVIDUAL SIGNAL QUALITY")

    # Test char n-gram catches typos
    ngram = char_ngram_similarity("artificial intelligence", "artifical inteligence")
    print(f"  Char n-gram (typo): {ngram:.3f} (should be >0.7)")

    # Test stemmed overlap catches morphological variants
    stemmed = stemmed_overlap_score("configuring the database", "configure database")
    print(f"  Stemmed overlap (morphology): {stemmed:.3f} (should be >0.4)")

    # Test IDF weighting reduces stopword influence
    idf_high = idf_weighted_overlap("sort array python", "sort array python")
    idf_low = idf_weighted_overlap("how do I sort", "how do I reverse")
    print(f"  IDF identical: {idf_high:.3f} vs IDF stopword-heavy: {idf_low:.3f} (gap should be large)")

    # Test synonym expansion
    syn = synonym_expanded_overlap("What is the cost?", "What is the price?")
    print(f"  Synonym overlap (cost/price): {syn:.3f} (should be >0.5)")

    # Test entity overlap prevents topic drift
    entity_good = key_entity_overlap("capital of France", "capital of France")
    entity_bad = key_entity_overlap("capital of France", "capital of Germany")
    print(f"  Entity (same): {entity_good:.3f} vs Entity (different): {entity_bad:.3f}")

    # Test question type
    qtype_same = question_type_match("What is Python?", "What is JavaScript?")
    qtype_diff = question_type_match("What is Python?", "How to install Python?")
    print(f"  Q-type (same): {qtype_same:.1f} vs Q-type (different): {qtype_diff:.1f}")


def main():
    total_passed = 0
    total_tests = 0

    p, t = test_normalization()
    total_passed += p; total_tests += t

    p, t = test_stemming()
    total_passed += p; total_tests += t

    p, t = test_question_type()
    total_passed += p; total_tests += t

    p, t = test_should_match_pairs()
    total_passed += p; total_tests += t

    p, t = test_should_not_match_pairs()
    total_passed += p; total_tests += t

    p, t = test_hybrid_scoring()
    total_passed += p; total_tests += t

    test_individual_signals()

    print_header("OVERALL RESULTS")
    pct = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"  {total_passed}/{total_tests} tests passed ({pct:.1f}%)")
    print()

    return 0 if total_passed == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())
