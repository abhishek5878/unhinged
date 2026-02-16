"""LinguisticAlignmentScorer -- Cross-attention Hinglish convergence tracker.

Tracks vocabulary convergence as a proxy for relational depth. The core insight:
when two people truly connect, their words infect each other. This module measures
that infection rate bidirectionally.

Uses indic-bert (ai4bharat/indic-bert) for embedding-space similarity, augmented
with n-gram overlap analysis, code-switch synchronization, and withdrawal detection.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from apriori.models.linguistic import ConvergenceRecord, LinguisticProfile


class LinguisticAlignmentScorer:
    """Tracks vocabulary convergence as a proxy for relational depth.

    When two people truly connect, their words infect each other. This class
    measures that infection rate bidirectionally using n-gram overlap, embedding
    similarity, and code-switch synchronization.

    Parameters
    ----------
    model_name:
        HuggingFace model for embeddings. Default ``"ai4bharat/indic-bert"``
        handles Hinglish natively.
    window_size:
        Number of recent turns to consider for convergence analysis.
    min_phrase_freq:
        Minimum frequency to count a phrase as part of an agent's signature.
        Ignores hapax legomena (frequency 1).
    """

    def __init__(
        self,
        model_name: str = "ai4bharat/indic-bert",
        window_size: int = 20,
        min_phrase_freq: int = 2,
    ) -> None:
        self._model_name = model_name
        self._window_size = window_size
        self._min_phrase_freq = min_phrase_freq

        # Lazy-loaded model + tokenizer
        self._tokenizer: Any = None
        self._model: Any = None

        # phrase_registry[agent_id][phrase] = count
        self._phrase_registry: Dict[str, Dict[str, int]] = defaultdict(lambda: Counter())
        # Raw utterances per agent, in order
        self._turn_registry: Dict[str, List[str]] = defaultdict(list)
        # Cached embeddings: (agent_id, turn_index) -> List[float]
        self._embedding_cache: Dict[Tuple[str, int], List[float]] = {}
        # Rolling alignment scores for trend detection
        self._alignment_history: List[float] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest_turn(self, agent_id: str, utterance: str) -> None:
        """Process one dialogue turn.

        1. Tokenize utterance into words.
        2. Extract n-grams (unigrams + bigrams) as candidate phrases.
        3. Register all phrases with frequency update.
        4. Append raw utterance to ``turn_registry[agent_id]``.
        5. Flag any phrases that match the OTHER agent's known signature.

        Parameters
        ----------
        agent_id:
            Identifier for the speaking agent.
        utterance:
            The raw text of the turn.
        """
        self._turn_registry[agent_id].append(utterance)
        tokens = self._tokenize(utterance)

        # Unigrams
        for token in tokens:
            self._phrase_registry[agent_id][token] += 1

        # Bigrams
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]} {tokens[i + 1]}"
            self._phrase_registry[agent_id][bigram] += 1

    def compute_convergence(
        self,
        agent_a_id: str,
        agent_b_id: str,
    ) -> Dict[str, Any]:
        """Full bidirectional convergence analysis.

        Returns
        -------
        dict
            a_absorbs_b: float
                % of B's signature phrases appearing in A's recent speech.
            b_absorbs_a: float
                Symmetric absorption.
            semantic_alignment: float
                Cosine similarity of recent turn embeddings.
            lexical_divergence: float
                1 - overlap coefficient of recent vocabulary.
            code_switch_sync: float
                Synchronization of Hindi<->English switching rates.
            resilience_delta: float
                Combined metric contributing to RelationshipResilienceScore.
            convergence_trend: str
                ``"accelerating"`` | ``"stable"`` | ``"diverging"``.
            top_borrowed_phrases: List[str]
                A's signature phrases that B has adopted.
            alarm: bool
                True if ``lexical_divergence > 0.7`` (linguistic withdrawal).
        """
        a_absorbs_b = self._compute_absorption(agent_a_id, agent_b_id)
        b_absorbs_a = self._compute_absorption(agent_b_id, agent_a_id)
        semantic = self._cross_attention_similarity(agent_a_id, agent_b_id)
        lexical_div = self._lexical_divergence(agent_a_id, agent_b_id)
        cs_sync = self._code_switch_sync(agent_a_id, agent_b_id)

        top_borrowed = self._find_borrowed_phrases(agent_a_id, agent_b_id)

        # Resilience delta: weighted combination
        resilience_delta = (
            0.3 * semantic
            + 0.2 * (a_absorbs_b + b_absorbs_a) / 2.0
            + 0.2 * cs_sync
            + 0.3 * (1.0 - lexical_div)
        )

        self._alignment_history.append(resilience_delta)
        trend = self._compute_trend()

        return {
            "a_absorbs_b": round(a_absorbs_b, 4),
            "b_absorbs_a": round(b_absorbs_a, 4),
            "semantic_alignment": round(semantic, 4),
            "lexical_divergence": round(lexical_div, 4),
            "code_switch_sync": round(cs_sync, 4),
            "resilience_delta": round(resilience_delta, 4),
            "convergence_trend": trend,
            "top_borrowed_phrases": top_borrowed[:10],
            "alarm": lexical_div > 0.7,
        }

    def get_linguistic_profile(self, agent_id: str) -> Dict[str, Any]:
        """Full linguistic fingerprint for an agent.

        Returns
        -------
        dict
            top_phrases, avg_turn_length, code_switch_rate, vocabulary_richness,
            total_turns, semantic_drift.
        """
        turns = self._turn_registry.get(agent_id, [])
        phrases = self._phrase_registry.get(agent_id, {})

        top_phrases = sorted(phrases.items(), key=lambda x: x[1], reverse=True)[:20]
        avg_length = self._avg_turn_length(agent_id)
        cs_rate = self._code_switch_rate(agent_id)
        ttr = self._type_token_ratio(agent_id)
        drift = self._semantic_drift(agent_id, window=10)

        return {
            "agent_id": agent_id,
            "top_phrases": top_phrases,
            "avg_turn_length": round(avg_length, 2),
            "code_switch_rate": round(cs_rate, 4),
            "vocabulary_richness": round(ttr, 4),
            "total_turns": len(turns),
            "semantic_drift": [round(d, 4) for d in drift],
        }

    def detect_withdrawal_signal(self, agent_id: str, window: int = 10) -> bool:
        """Detect linguistic withdrawal as a pre-collapse behavioral signal.

        Compares the last ``window // 2`` turns against the prior ``window // 2``.
        Alerts if vocabulary drops > 40% or average turn length drops > 50%.

        This signal is distinct from epistemic divergence -- it's behavioral.

        Parameters
        ----------
        agent_id:
            Agent to check.
        window:
            Total number of turns to analyze (split into two halves).

        Returns
        -------
        bool
            True if withdrawal is detected.
        """
        turns = self._turn_registry.get(agent_id, [])
        if len(turns) < window:
            return False

        half = window // 2
        recent = turns[-half:]
        earlier = turns[-window:-half]

        recent_vocab: Set[str] = set()
        earlier_vocab: Set[str] = set()
        for t in recent:
            recent_vocab.update(self._tokenize(t))
        for t in earlier:
            earlier_vocab.update(self._tokenize(t))

        if not earlier_vocab:
            return False

        vocab_ratio = len(recent_vocab) / len(earlier_vocab)

        recent_avg = sum(len(self._tokenize(t)) for t in recent) / max(len(recent), 1)
        earlier_avg = sum(len(self._tokenize(t)) for t in earlier) / max(len(earlier), 1)

        if earlier_avg == 0:
            return False

        length_ratio = recent_avg / earlier_avg

        return vocab_ratio < 0.6 or length_ratio < 0.5

    def reset(self) -> None:
        """Clear all internal state. Useful for testing or starting a new session."""
        self._phrase_registry.clear()
        self._turn_registry.clear()
        self._embedding_cache.clear()
        self._alignment_history.clear()

    # ------------------------------------------------------------------
    # Embedding
    # ------------------------------------------------------------------

    def _ensure_model_loaded(self) -> None:
        """Lazy-load the tokenizer and model from HuggingFace."""
        if self._tokenizer is not None:
            return
        from transformers import AutoModel, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        self._model = AutoModel.from_pretrained(self._model_name)

    def compute_embedding(self, text: str) -> List[float]:
        """Compute the CLS embedding for a text using indic-bert.

        Returns
        -------
        list[float]
            The CLS token embedding vector.
        """
        self._ensure_model_loaded()
        import torch

        inputs = self._tokenizer(
            text, return_tensors="pt", truncation=True, max_length=512, padding=True
        )
        with torch.no_grad():
            outputs = self._model(**inputs)
        cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().tolist()
        if isinstance(cls_embedding, float):
            cls_embedding = [cls_embedding]
        return cls_embedding

    def _get_turn_embedding(self, agent_id: str, turn_index: int) -> List[float]:
        """Get or compute and cache the embedding for a specific turn."""
        cache_key = (agent_id, turn_index)
        if cache_key not in self._embedding_cache:
            turns = self._turn_registry.get(agent_id, [])
            if turn_index < 0 or turn_index >= len(turns):
                return []
            self._embedding_cache[cache_key] = self.compute_embedding(turns[turn_index])
        return self._embedding_cache[cache_key]

    # ------------------------------------------------------------------
    # Cross-attention similarity
    # ------------------------------------------------------------------

    def _cross_attention_similarity(
        self,
        agent_a_id: str,
        agent_b_id: str,
        window: Optional[int] = None,
    ) -> float:
        """Compute semantic similarity between two agents' recent speech.

        Gets the last ``window`` turns for each agent, embeds each turn,
        computes the mean embedding per agent, and returns cosine similarity.
        Falls back to lexical overlap if the model is unavailable.
        """
        if window is None:
            window = self._window_size

        turns_a = self._turn_registry.get(agent_a_id, [])
        turns_b = self._turn_registry.get(agent_b_id, [])

        if not turns_a or not turns_b:
            return 0.0

        try:
            self._ensure_model_loaded()
        except Exception:
            return 1.0 - self._lexical_divergence(agent_a_id, agent_b_id)

        recent_a = turns_a[-window:]
        recent_b = turns_b[-window:]

        embs_a = [self.compute_embedding(t) for t in recent_a]
        embs_b = [self.compute_embedding(t) for t in recent_b]

        if not embs_a or not embs_b:
            return 0.0

        mean_a = self._mean_vector(embs_a)
        mean_b = self._mean_vector(embs_b)

        return self._cosine_similarity(mean_a, mean_b)

    # ------------------------------------------------------------------
    # Code-switch synchronization
    # ------------------------------------------------------------------

    def _code_switch_sync(self, agent_a_id: str, agent_b_id: str) -> float:
        """Measure synchronization of Hindi<->English code-switching between agents.

        Heuristic: turns with > 30% non-ASCII characters = predominantly Hindi.
        sync = 1 - |switch_rate_A - switch_rate_B| / max(switch_rate_A, switch_rate_B, 0.01)
        """
        rate_a = self._code_switch_rate(agent_a_id)
        rate_b = self._code_switch_rate(agent_b_id)
        max_rate = max(rate_a, rate_b, 0.01)
        return max(0.0, 1.0 - abs(rate_a - rate_b) / max_rate)

    def _code_switch_rate(self, agent_id: str) -> float:
        """Fraction of recent turns that are predominantly Hindi (non-ASCII > 30%)."""
        turns = self._turn_registry.get(agent_id, [])
        if not turns:
            return 0.0

        window = turns[-self._window_size:]
        hindi_count = 0
        for turn in window:
            if not turn:
                continue
            non_ascii = sum(1 for c in turn if ord(c) > 127)
            if non_ascii / max(len(turn), 1) > 0.3:
                hindi_count += 1

        return hindi_count / len(window)

    # ------------------------------------------------------------------
    # Absorption & borrowing
    # ------------------------------------------------------------------

    def _compute_absorption(self, absorber_id: str, donor_id: str) -> float:
        """Compute what % of the donor's signature phrases appear in absorber's recent speech."""
        donor_phrases = self._get_signature_phrases(donor_id)
        if not donor_phrases:
            return 0.0

        absorber_turns = self._turn_registry.get(absorber_id, [])
        recent = absorber_turns[-self._window_size:]
        recent_text = " ".join(recent).lower()

        matches = sum(1 for phrase in donor_phrases if phrase.lower() in recent_text)
        return matches / len(donor_phrases)

    def _find_borrowed_phrases(self, source_id: str, borrower_id: str) -> List[str]:
        """Find source's signature phrases that the borrower has adopted."""
        source_sigs = self._get_signature_phrases(source_id)
        borrower_phrases = self._phrase_registry.get(borrower_id, {})

        borrowed = []
        for phrase in source_sigs:
            if borrower_phrases.get(phrase, 0) >= self._min_phrase_freq:
                borrowed.append(phrase)

        return sorted(borrowed, key=lambda p: borrower_phrases.get(p, 0), reverse=True)

    def _get_signature_phrases(self, agent_id: str) -> List[str]:
        """Get phrases that qualify as an agent's signature (freq >= min_phrase_freq)."""
        phrases = self._phrase_registry.get(agent_id, {})
        return [p for p, count in phrases.items() if count >= self._min_phrase_freq]

    # ------------------------------------------------------------------
    # Lexical analysis
    # ------------------------------------------------------------------

    def _lexical_divergence(self, agent_a_id: str, agent_b_id: str) -> float:
        """Compute 1 - overlap coefficient of recent vocabulary.

        overlap = |A & B| / min(|A|, |B|);  divergence = 1 - overlap
        """
        vocab_a = self._recent_vocabulary(agent_a_id)
        vocab_b = self._recent_vocabulary(agent_b_id)

        if not vocab_a or not vocab_b:
            return 1.0

        intersection = vocab_a & vocab_b
        overlap = len(intersection) / min(len(vocab_a), len(vocab_b))
        return 1.0 - overlap

    def _recent_vocabulary(self, agent_id: str) -> Set[str]:
        """Unique tokens from an agent's recent turns."""
        turns = self._turn_registry.get(agent_id, [])
        recent = turns[-self._window_size:]
        vocab: Set[str] = set()
        for turn in recent:
            vocab.update(self._tokenize(turn))
        return vocab

    def _avg_turn_length(self, agent_id: str) -> float:
        """Mean token count per turn for an agent."""
        turns = self._turn_registry.get(agent_id, [])
        if not turns:
            return 0.0
        return sum(len(self._tokenize(t)) for t in turns) / len(turns)

    def _type_token_ratio(self, agent_id: str) -> float:
        """Type-token ratio: unique tokens / total tokens."""
        turns = self._turn_registry.get(agent_id, [])
        if not turns:
            return 0.0
        all_tokens: List[str] = []
        for turn in turns:
            all_tokens.extend(self._tokenize(turn))
        if not all_tokens:
            return 0.0
        return len(set(all_tokens)) / len(all_tokens)

    def _semantic_drift(self, agent_id: str, window: int = 10) -> List[float]:
        """Cosine distance between consecutive turn embeddings for the last ``window`` transitions."""
        turns = self._turn_registry.get(agent_id, [])
        if len(turns) < 2:
            return []

        recent_indices = list(range(max(0, len(turns) - window - 1), len(turns)))
        if len(recent_indices) < 2:
            return []

        try:
            self._ensure_model_loaded()
        except Exception:
            return []

        distances: List[float] = []
        for i in range(len(recent_indices) - 1):
            emb_a = self._get_turn_embedding(agent_id, recent_indices[i])
            emb_b = self._get_turn_embedding(agent_id, recent_indices[i + 1])
            if emb_a and emb_b:
                distances.append(1.0 - self._cosine_similarity(emb_a, emb_b))

        return distances

    # ------------------------------------------------------------------
    # Trend analysis
    # ------------------------------------------------------------------

    def _compute_trend(self) -> str:
        """Classify the convergence trend from alignment history."""
        hist = self._alignment_history
        if len(hist) < 6:
            return "stable"

        recent = hist[-3:]
        earlier = hist[-6:-3]
        diff = (sum(recent) / len(recent)) - (sum(earlier) / len(earlier))
        if diff > 0.05:
            return "accelerating"
        if diff < -0.05:
            return "diverging"
        return "stable"

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple whitespace + punctuation tokenizer. Lowercases all tokens."""
        return [t.lower() for t in re.findall(r"\b\w+\b", text) if len(t) > 1]

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _mean_vector(vectors: List[List[float]]) -> List[float]:
        """Compute element-wise mean of a list of vectors."""
        if not vectors:
            return []
        dim = len(vectors[0])
        result = [0.0] * dim
        for vec in vectors:
            for i, v in enumerate(vec):
                result[i] += v
        n = len(vectors)
        return [v / n for v in result]

    def __repr__(self) -> str:
        agents = list(self._turn_registry.keys())
        total_turns = sum(len(v) for v in self._turn_registry.values())
        return (
            f"LinguisticAlignmentScorer("
            f"model={self._model_name!r}, "
            f"agents={agents}, "
            f"total_turns={total_turns})"
        )
