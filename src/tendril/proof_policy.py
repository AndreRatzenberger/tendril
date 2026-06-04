from __future__ import annotations

import json
from typing import Any

from tendril.store import Store


DEFAULT_PROOF_POLICY: dict[str, Any] = {
    "id": "default-proof-policy",
    "version": "m4-1",
    "allowed_actions": ["add_node", "add_edge", "meta_change"],
    "allowed_risk_tiers": ["low", "review", "high"],
    "min_rationale_chars": 24,
    "source_grounding": {
        "require_evidence_quotes": True,
        "normalize_whitespace": True,
    },
    "model_assisted_proof": {
        "enabled": False,
        "gate": "deterministic_checks_first",
    },
}


def read_proof_policy(store: Store) -> dict[str, Any]:
    store.initialize()
    path = store.root / "proof-policy.json"
    if not path.exists():
        store.write_json(path, DEFAULT_PROOF_POLICY, overwrite=False)
    return json.loads(path.read_text(encoding="utf-8"))
