from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from tendril.artifacts import ingest_artifact
from tendril.graph import ApplyError, apply_proposal
from tendril.proof import ProofError, run_proof
from tendril.proposals import ProposalValidationError, create_proposals
from tendril.review import ReviewError, record_review
from tendril.runtime import RUNTIME_CHOICES
from tendril.runtime.base import TendrilRuntimeError
from tendril.store import DuplicateRecordError, RecordNotFoundError, Store, StoreError


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = Store(Path.cwd() / ".tendril")

    try:
        payload = args.func(args, store)
    except (
        ApplyError,
        DuplicateRecordError,
        FileNotFoundError,
        ProofError,
        ProposalValidationError,
        RecordNotFoundError,
        ReviewError,
        StoreError,
        TendrilRuntimeError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tendril",
        description="Run Tendril's local graph-change proposal loop.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="ingest a markdown artifact")
    ingest.add_argument("path", help="path to the artifact to ingest")
    ingest.set_defaults(func=_cmd_ingest)

    propose = subparsers.add_parser("propose", help="create graph-change proposals")
    propose.add_argument("--artifact", required=True, help="artifact ID")
    propose.add_argument(
        "--runtime",
        choices=RUNTIME_CHOICES,
        default="fake",
        help="proposal runtime to use",
    )
    propose.set_defaults(func=_cmd_propose)

    proof = subparsers.add_parser("proof", help="run proof checks for a proposal")
    proof.add_argument("--proposal", required=True, help="proposal ID")
    proof.set_defaults(func=_cmd_proof)

    review = subparsers.add_parser("review", help="record a review decision")
    review.add_argument("--proposal", required=True, help="proposal ID")
    review.add_argument("--decision", required=True, choices=["accept", "reject"])
    review.add_argument("--reason", required=True, help="review rationale")
    review.set_defaults(func=_cmd_review)

    apply = subparsers.add_parser("apply", help="apply an accepted proposal")
    apply.add_argument("--proposal", required=True, help="proposal ID")
    apply.set_defaults(func=_cmd_apply)

    return parser


def _cmd_ingest(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    artifact = ingest_artifact(store, Path(args.path))
    return {"artifact_id": artifact["id"], "artifact": artifact}


def _cmd_propose(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    proposals = create_proposals(store, args.artifact, runtime_name=args.runtime)
    return {
        "artifact_id": args.artifact,
        "runtime": args.runtime,
        "proposal_ids": [proposal["id"] for proposal in proposals],
        "proposals": proposals,
    }


def _cmd_proof(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    return run_proof(store, args.proposal)


def _cmd_review(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    return record_review(store, args.proposal, args.decision, args.reason)


def _cmd_apply(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    return apply_proposal(store, args.proposal)


if __name__ == "__main__":
    raise SystemExit(main())
