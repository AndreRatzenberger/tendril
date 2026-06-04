from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from tendril.artifacts import ingest_artifact
from tendril.edges import EdgeProposalError, create_edge_proposal
from tendril.graph import ApplyError, apply_proposal
from tendril.meta import MetaProposalError, create_meta_proposal
from tendril.proof import ProofError, run_proof
from tendril.proposals import ProposalValidationError, create_proposals
from tendril.review import ReviewError, record_review
from tendril.runtime import RUNTIME_CHOICES
from tendril.runtime.base import TendrilRuntimeError
from tendril.store import DuplicateRecordError, RecordNotFoundError, Store, StoreError
from tendril.topic_state import (
    TopicStateError,
    bind_topic_runtime,
    clear_topic_runtime,
    list_topic_records,
    read_topic_record,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = Store(Path.cwd() / ".tendril")

    try:
        payload = args.func(args, store)
    except (
        ApplyError,
        DuplicateRecordError,
        EdgeProposalError,
        FileNotFoundError,
        MetaProposalError,
        ProofError,
        ProposalValidationError,
        RecordNotFoundError,
        ReviewError,
        StoreError,
        TendrilRuntimeError,
        TopicStateError,
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

    propose_edge = subparsers.add_parser(
        "propose-edge",
        help="create a graph edge proposal between existing nodes",
    )
    propose_edge.add_argument("--artifact", required=True, help="artifact ID")
    propose_edge.add_argument("--source", required=True, help="source node ID")
    propose_edge.add_argument("--target", required=True, help="target node ID")
    propose_edge.add_argument("--relationship", required=True, help="edge label")
    propose_edge.add_argument("--evidence", required=True, help="artifact evidence")
    propose_edge.set_defaults(func=_cmd_propose_edge)

    propose_meta = subparsers.add_parser(
        "propose-meta",
        help="create a bounded meta-change proposal",
    )
    propose_meta.add_argument("--artifact", required=True, help="artifact ID")
    propose_meta.add_argument(
        "--change-type",
        required=True,
        help="kind of system change being proposed",
    )
    propose_meta.add_argument("--target", required=True, help="change target")
    propose_meta.add_argument(
        "--expected-benefit",
        required=True,
        help="expected benefit of the meta change",
    )
    propose_meta.add_argument("--evidence", required=True, help="artifact evidence")
    propose_meta.add_argument(
        "--blast-radius",
        required=True,
        help="affected behavior or authority surface",
    )
    propose_meta.add_argument(
        "--rollback-path",
        required=True,
        help="how to undo or park the change",
    )
    propose_meta.set_defaults(func=_cmd_propose_meta)

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

    topic = subparsers.add_parser("topic", help="inspect and manage topic state")
    topic_subparsers = topic.add_subparsers(dest="topic_command", required=True)

    topic_list = topic_subparsers.add_parser("list", help="list topic records")
    topic_list.set_defaults(func=_cmd_topic_list)

    topic_show = topic_subparsers.add_parser("show", help="show one topic record")
    topic_show.add_argument("topic_id", help="topic ID")
    topic_show.set_defaults(func=_cmd_topic_show)

    topic_bind = topic_subparsers.add_parser(
        "bind-runtime",
        help="bind or update a topic runtime handle",
    )
    topic_bind.add_argument("topic_id", help="topic ID")
    topic_bind.add_argument("--runtime", required=True, choices=RUNTIME_CHOICES)
    topic_bind.add_argument("--thread-id", required=True, help="runtime thread ID")
    topic_bind.add_argument("--model", help="runtime model")
    topic_bind.set_defaults(func=_cmd_topic_bind_runtime)

    topic_clear = topic_subparsers.add_parser(
        "clear-runtime",
        help="clear a topic runtime handle",
    )
    topic_clear.add_argument("topic_id", help="topic ID")
    topic_clear.set_defaults(func=_cmd_topic_clear_runtime)

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


def _cmd_propose_edge(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    proposal = create_edge_proposal(
        store,
        args.artifact,
        source_id=args.source,
        target_id=args.target,
        relationship=args.relationship,
        evidence_quote=args.evidence,
    )
    return {"proposal_id": proposal["id"], "proposal": proposal}


def _cmd_propose_meta(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    proposal = create_meta_proposal(
        store,
        args.artifact,
        change_type=args.change_type,
        target=args.target,
        expected_benefit=args.expected_benefit,
        evidence_quote=args.evidence,
        blast_radius=args.blast_radius,
        rollback_path=args.rollback_path,
    )
    return {"proposal_id": proposal["id"], "proposal": proposal}


def _cmd_proof(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    return run_proof(store, args.proposal)


def _cmd_review(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    return record_review(store, args.proposal, args.decision, args.reason)


def _cmd_apply(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    return apply_proposal(store, args.proposal)


def _cmd_topic_list(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    return {"topics": list_topic_records(store)}


def _cmd_topic_show(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    return read_topic_record(store, args.topic_id)


def _cmd_topic_bind_runtime(
    args: argparse.Namespace,
    store: Store,
) -> dict[str, Any]:
    return bind_topic_runtime(
        store,
        args.topic_id,
        runtime_name=args.runtime,
        thread_id=args.thread_id,
        model=args.model,
    )


def _cmd_topic_clear_runtime(
    args: argparse.Namespace,
    store: Store,
) -> dict[str, Any]:
    return clear_topic_runtime(store, args.topic_id)


if __name__ == "__main__":
    raise SystemExit(main())
