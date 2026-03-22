import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = ROOT_DIR / "system_prompt.md"
KNOWLEDGE_BASE_JSON_PATH = ROOT_DIR / "knowledge_base.json"
KNOWLEDGE_BASE_MD_PATH = ROOT_DIR / "knowledge_base.md"
REPORT_OUTPUT_PATH = ROOT_DIR / "evaluation_report.json"

EXPECTED_BANKS = ("ameriabank", "ardshinbank", "mellatbank")
REQUIRED_PROMPT_RULES = (
    "Always respond in Armenian unless the user explicitly asks for another language.",
    "Use only the knowledge base injected below.",
    "Do not use outside knowledge, prior assumptions, or general banking knowledge.",
    "If the user asks about another bank, say that you only support Mellat Bank, Ameriabank, and Ardshinbank.",
    "If the user asks about a topic outside deposits, credits, or branches, refuse politely.",
    "If the user asks about cards, transfers, exchange rates, investments, insurance, or any other unsupported banking product, refuse politely.",
    "If the knowledge base does not contain the requested detail, say you do not have that exact detail and suggest contacting the bank directly.",
    "If the question could match more than one bank and the user did not specify which bank, ask a short clarifying question before answering.",
    "Never invent rates, fees, branch addresses, working hours, or eligibility rules.",
)

MIN_PAGE_COVERAGE = {
    "ameriabank": {"deposits": 3, "credits": 20, "branches": 1},
    "ardshinbank": {"deposits": 1, "credits": 15, "branches": 1},
    "mellatbank": {"deposits": 1, "credits": 5, "branches": 1},
}
MIN_TOTALS = {"pages": 70, "tables": 40, "pdfs": 10}


def _load_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def _load_knowledge_base() -> dict:
    return json.loads(KNOWLEDGE_BASE_JSON_PATH.read_text(encoding="utf-8"))


def _check(name: str, passed: bool, details: str) -> dict:
    return {"name": name, "passed": passed, "details": details}


def build_report() -> dict:
    prompt = _load_prompt()
    knowledge_base = _load_knowledge_base()
    banks_by_id = {bank["bank_id"]: bank for bank in knowledge_base.get("banks", [])}

    report = {
        "generated_from": str(ROOT_DIR),
        "checks": [],
        "banks": {},
        "totals": {},
    }

    for bank_id in EXPECTED_BANKS:
        report["checks"].append(
            _check(
                name=f"bank:{bank_id}",
                passed=bank_id in banks_by_id,
                details="present in knowledge_base.json" if bank_id in banks_by_id else "missing from knowledge_base.json",
            )
        )

    for rule in REQUIRED_PROMPT_RULES:
        report["checks"].append(
            _check(
                name=f"prompt:{rule[:40]}...",
                passed=rule in prompt,
                details="found in system prompt" if rule in prompt else "missing from system prompt",
            )
        )

    json_size = KNOWLEDGE_BASE_JSON_PATH.stat().st_size
    markdown_size = KNOWLEDGE_BASE_MD_PATH.stat().st_size
    report["checks"].append(
        _check(
            name="artifact:prompt_markdown_smaller_than_json",
            passed=markdown_size < json_size,
            details=f"knowledge_base.md={markdown_size} bytes, knowledge_base.json={json_size} bytes",
        )
    )

    total_pages = 0
    total_tables = 0
    total_pdfs = 0

    for bank_id, thresholds in MIN_PAGE_COVERAGE.items():
        bank_report = {"checks": [], "coverage": {}}
        bank = banks_by_id.get(bank_id)

        if not bank:
            report["banks"][bank_id] = bank_report
            continue

        for category_key, minimum_pages in thresholds.items():
            category = bank["categories"][category_key]
            pages = len(category.get("pages", []))
            tables = len(category.get("data_tables", []))
            pdfs = len(category.get("pdf_documents", []))

            total_pages += pages
            total_tables += tables
            total_pdfs += pdfs

            bank_report["coverage"][category_key] = {
                "pages": pages,
                "tables": tables,
                "pdfs": pdfs,
            }
            bank_report["checks"].append(
                _check(
                    name=f"{category_key}:min_pages",
                    passed=pages >= minimum_pages,
                    details=f"pages={pages}, minimum={minimum_pages}",
                )
            )

        report["banks"][bank_id] = bank_report

    report["totals"] = {"pages": total_pages, "tables": total_tables, "pdfs": total_pdfs}
    for key, minimum in MIN_TOTALS.items():
        report["checks"].append(
            _check(
                name=f"totals:{key}",
                passed=report["totals"][key] >= minimum,
                details=f"{key}={report['totals'][key]}, minimum={minimum}",
            )
        )

    return report


def main() -> None:
    report = build_report()
    REPORT_OUTPUT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote evaluation report to {REPORT_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
