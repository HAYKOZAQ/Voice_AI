import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agent
import project_evaluation
from scraper import compiler


def test_build_agent_instructions_replaces_placeholder():
    instructions = agent.build_agent_instructions()
    assert "{{BANK_KNOWLEDGE_BASE}}" not in instructions
    assert "Ameriabank" in instructions
    assert "Ardshinbank" in instructions
    assert "Mellat" in instructions


def test_build_agent_uses_grounded_instructions():
    instructions = agent.build_agent_instructions()
    voice_agent = agent.build_agent(instructions)
    assert voice_agent.instructions == instructions
    assert "Use only the knowledge base injected below." in voice_agent.instructions


def test_validate_environment_reports_missing_vars(monkeypatch):
    for name in agent.REQUIRED_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        agent.validate_environment()


def test_system_prompt_contains_required_guardrails():
    prompt = Path("system_prompt.md").read_text(encoding="utf-8")
    for rule in project_evaluation.REQUIRED_PROMPT_RULES:
        assert rule in prompt


def test_validate_knowledge_base_reports_empty_required_category():
    knowledge_base = {
        "generated_at": "2026-03-22T00:00:00+00:00",
        "banks": [
            {
                "bank_id": "ameriabank",
                "bank_name": "Ameriabank",
                "categories": {
                    "deposits": {"text_chunks": ["ok"], "data_tables": [], "pdf_documents": []},
                    "credits": {"text_chunks": [], "data_tables": [], "pdf_documents": []},
                    "branches": {"text_chunks": ["ok"], "data_tables": [], "pdf_documents": []},
                },
            }
        ],
    }

    errors = compiler.validate_knowledge_base(knowledge_base, expected_banks=["ameriabank"])
    assert "ameriabank category has no usable content: credits" in errors


def test_generated_knowledge_base_has_expected_schema():
    path = Path("knowledge_base.json")
    if not path.exists():
        pytest.skip("knowledge_base.json has not been compiled yet")

    data = json.loads(path.read_text(encoding="utf-8"))
    assert "generated_at" in data
    assert "banks" in data

    for bank in data["banks"]:
        assert {"bank_id", "bank_name", "categories"} <= set(bank)
        assert set(bank["categories"]) == {"deposits", "credits", "branches"}
        for category in bank["categories"].values():
            assert category["source_urls"]
            assert category["pages"]
            for url in category["source_urls"]:
                assert "#" not in url
                assert "/en/" not in url
                assert "/ru/" not in url
                assert "lang=en" not in url
                assert "lang=ru" not in url
            for page in category["pages"]:
                assert "url" in page
                assert "title" in page


def test_static_evaluation_report_passes():
    report = project_evaluation.build_report()
    for check in report["checks"]:
        assert check["passed"], check

    for bank in project_evaluation.EXPECTED_BANKS:
        for check in report["banks"][bank]["checks"]:
            assert check["passed"], check
