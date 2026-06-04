from __future__ import annotations

from tendril.runtime.base import ProposalRuntime, TendrilRuntimeError
from tendril.runtime.codex import CodexRuntime
from tendril.runtime.fake import FakeRuntime


def get_runtime(name: str) -> ProposalRuntime:
    if name == "fake":
        return FakeRuntime()
    if name == "codex":
        return CodexRuntime()
    raise TendrilRuntimeError(f"Unknown runtime: {name}")


RUNTIME_CHOICES = ("fake", "codex")

__all__ = [
    "CodexRuntime",
    "FakeRuntime",
    "ProposalRuntime",
    "RUNTIME_CHOICES",
    "TendrilRuntimeError",
    "get_runtime",
]
