from tendril.topics import select_topics


def test_codex_artifacts_match_codex_runtime_topic() -> None:
    matches = select_topics("Codex threads can become application state.")

    assert matches[0]["topic_id"] == "codex-runtime"
    assert "codex" in matches[0]["matched_terms"]


def test_proof_artifacts_match_proof_and_governance_topic() -> None:
    matches = select_topics("Proof checks and approval gates prevent bad links.")

    assert any(match["topic_id"] == "proof-and-governance" for match in matches)


def test_unrelated_artifacts_use_default_bounded_autonomy_topic() -> None:
    matches = select_topics("A small note about gardening.")

    assert matches == [
        {
            "topic_id": "bounded-autonomy-software",
            "matched_terms": [],
            "reason": "default topic for M0 artifacts",
        }
    ]
