"""Scoring for localization tasks.

The task is defensive: given a source file, does the model point at the
function that the official fix changed? We never ask for an exploit.

Unit of scoring is the function name. Ground truth is the set of functions
touched by the fix commit (recorded in the dataset). We compare it to the set
of functions the model named.

Per case we report precision and recall. We aggregate two ways:
  - micro: pooled true/false positives/negatives across all cases
  - macro: mean of per-case scores
"""

from __future__ import annotations

from dataclasses import dataclass


def _norm(name: str) -> str:
    return name.strip().strip("()").split("(")[0].strip().lower()


def normalize_set(names) -> set[str]:
    return {_norm(n) for n in names if _norm(n)}


@dataclass
class CaseScore:
    case_id: str
    truth: set[str]
    predicted: set[str]

    @property
    def tp(self) -> int:
        return len(self.truth & self.predicted)

    @property
    def fp(self) -> int:
        return len(self.predicted - self.truth)

    @property
    def fn(self) -> int:
        return len(self.truth - self.predicted)

    @property
    def precision(self) -> float:
        d = self.tp + self.fp
        return self.tp / d if d else 0.0

    @property
    def recall(self) -> float:
        d = self.tp + self.fn
        return self.tp / d if d else 0.0


def aggregate(scores: list[CaseScore]) -> dict:
    tp = sum(s.tp for s in scores)
    fp = sum(s.fp for s in scores)
    fn = sum(s.fn for s in scores)
    micro_p = tp / (tp + fp) if (tp + fp) else 0.0
    micro_r = tp / (tp + fn) if (tp + fn) else 0.0
    macro_p = sum(s.precision for s in scores) / len(scores) if scores else 0.0
    macro_r = sum(s.recall for s in scores) / len(scores) if scores else 0.0
    return {
        "n_cases": len(scores),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "micro_precision": round(micro_p, 3),
        "micro_recall": round(micro_r, 3),
        "macro_precision": round(macro_p, 3),
        "macro_recall": round(macro_r, 3),
    }
