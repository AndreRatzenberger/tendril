from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from tendril.runtime.base import ProposalRequest, TendrilRuntimeError


CODEX_PROPOSAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["proposals"],
    "additionalProperties": False,
    "properties": {
        "proposals": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "topic_id",
                    "action",
                    "target",
                    "rationale",
                    "evidence",
                    "risk_tier",
                    "status",
                ],
                "additionalProperties": False,
                "properties": {
                    "topic_id": {"type": "string"},
                    "action": {"type": "string", "enum": ["add_node"]},
                    "target": {
                        "type": "object",
                        "required": ["type", "id", "title"],
                        "additionalProperties": False,
                        "properties": {
                            "type": {"type": "string", "enum": ["node"]},
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                        },
                    },
                    "rationale": {"type": "string"},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["artifact_id", "quote"],
                            "additionalProperties": False,
                            "properties": {
                                "artifact_id": {"type": "string"},
                                "quote": {"type": "string"},
                            },
                        },
                    },
                    "risk_tier": {"type": "string", "enum": ["low", "review", "high"]},
                    "status": {"type": "string", "enum": ["proposed"]},
                },
            },
        }
    },
}


class CodexRuntime:
    name = "codex"

    def __init__(self, *, model: str = "gpt-5.4") -> None:
        self.model = model

    def create_proposals(self, request: ProposalRequest) -> dict[str, Any]:
        codex_bin = _load_codex_cli()
        prompt = self.build_prompt(request)

        with tempfile.TemporaryDirectory(prefix="tendril-codex-") as temp_dir:
            temp_path = Path(temp_dir)
            schema_path = temp_path / "proposal-schema.json"
            response_path = temp_path / "response.json"
            schema_path.write_text(
                json.dumps(CODEX_PROPOSAL_SCHEMA, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    codex_bin,
                    "exec",
                    "--model",
                    self.model,
                    "--sandbox",
                    "read-only",
                    "--skip-git-repo-check",
                    "--output-schema",
                    str(schema_path),
                    "--output-last-message",
                    str(response_path),
                    "-",
                ],
                input=prompt,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                detail = result.stderr.strip() or result.stdout.strip()
                raise TendrilRuntimeError(f"Codex CLI runtime failed: {detail}")
            response = response_path.read_text(encoding="utf-8")

        parsed = self.parse_response(response)
        return {
            "runtime": {
                "name": self.name,
                "kind": "codex-cli",
                "model": self.model,
            },
            "proposals": parsed["proposals"],
        }

    def build_prompt(self, request: ProposalRequest) -> str:
        artifact = request.artifact
        topics = [
            {
                "id": topic.id,
                "title": topic.title,
                "description": topic.description,
            }
            for topic in request.topics
        ]
        artifact_context = {
            "id": artifact["id"],
            "path": artifact.get("path"),
            "content": str(artifact.get("content", ""))[:6000],
            "topics": topics,
        }
        return "\n".join(
            [
                "You are a Tendril topic agent.",
                "Return JSON only. Do not include markdown fences or commentary.",
                "Create graph-change proposals for the supplied artifact and topics.",
                "Use only the requested topic IDs.",
                "Every proposal must be grounded in a quote from the artifact.",
                "Allowed actions for M1: add_node.",
                "Prefer risk_tier review unless the proposal is clearly low risk.",
                "",
                "Artifact and requested topics:",
                json.dumps(artifact_context, indent=2, sort_keys=True),
                "",
                "Required JSON schema:",
                json.dumps(CODEX_PROPOSAL_SCHEMA, indent=2, sort_keys=True),
            ]
        )

    @staticmethod
    def parse_response(text: str) -> dict[str, Any]:
        payload = text.strip()
        if payload.startswith("```"):
            payload = _strip_markdown_fence(payload)
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise TendrilRuntimeError("Codex runtime did not return JSON") from exc

        if not isinstance(data, dict) or "proposals" not in data:
            raise TendrilRuntimeError("Codex runtime response missing proposals")
        if not isinstance(data["proposals"], list):
            raise TendrilRuntimeError("Codex runtime proposals must be a list")
        if not data["proposals"]:
            raise TendrilRuntimeError(
                "Codex runtime response must include at least one proposal"
            )
        return data


def _load_codex_cli() -> str:
    codex_bin = shutil.which("codex")
    if not codex_bin:
        raise TendrilRuntimeError("Codex runtime requires the codex CLI on PATH")
    return codex_bin


def _strip_markdown_fence(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
