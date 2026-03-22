import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .ameriabank import run_scraper as run_ameriabank
from .ardshinbank import run_scraper as run_ardshinbank
from .chunker import chunk_html_text, chunk_pdf_content
from .mellatbank import run_scraper as run_mellatbank

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("compiler")

ROOT_DIR = Path(__file__).resolve().parent.parent
JSON_OUTPUT_PATH = ROOT_DIR / "knowledge_base.json"
MARKDOWN_OUTPUT_PATH = ROOT_DIR / "knowledge_base.md"

SCRAPER_REGISTRY: dict[str, Callable[[], dict[str, Any]]] = {
    "ameriabank": run_ameriabank,
    "ardshinbank": run_ardshinbank,
    "mellatbank": run_mellatbank,
}
REQUIRED_CATEGORIES = ("deposits", "credits", "branches")


def normalize_bank_data(raw_bank_data: dict[str, Any]) -> dict[str, Any]:
    normalized_categories: dict[str, dict[str, Any]] = {}

    for category_key in REQUIRED_CATEGORIES:
        raw_category = raw_bank_data["categories"].get(category_key, {})

        text_chunks: list[str] = []
        for raw_text in raw_category.get("raw_texts", []):
            text_chunks.extend(chunk_html_text(raw_text))

        pdf_documents: list[dict[str, Any]] = []
        for pdf_doc in raw_category.get("pdf_documents", []):
            content = pdf_doc.get("content", "")
            content_chunks = chunk_pdf_content(content) if content else []
            pdf_documents.append(
                {
                    "title": pdf_doc.get("title", pdf_doc.get("url", "")),
                    "url": pdf_doc.get("url", ""),
                    "content_chunks": content_chunks,
                }
            )

        pages: list[dict[str, Any]] = []
        for raw_page in raw_category.get("pages", []):
            page_pdf_documents: list[dict[str, Any]] = []
            for pdf_doc in raw_page.get("pdf_documents", []):
                content = pdf_doc.get("content", "")
                content_chunks = chunk_pdf_content(content) if content else []
                page_pdf_documents.append(
                    {
                        "title": pdf_doc.get("title", pdf_doc.get("url", "")),
                        "url": pdf_doc.get("url", ""),
                        "content_chunks": content_chunks,
                    }
                )

            page_texts = raw_page.get("raw_texts", [])
            page_text_chunks: list[str] = []
            for page_text in page_texts:
                page_text_chunks.extend(chunk_html_text(page_text))

            pages.append(
                {
                    "title": raw_page.get("title", ""),
                    "url": raw_page.get("url", ""),
                    "headings": raw_page.get("headings", []),
                    "text_chunks": page_text_chunks,
                    "data_tables": raw_page.get("data_tables", []),
                    "pdf_documents": page_pdf_documents,
                }
            )

        normalized_categories[category_key] = {
            "label": raw_category.get("label", category_key.title()),
            "source_urls": raw_category.get("source_urls", []),
            "pages": pages,
            "text_chunks": text_chunks,
            "data_tables": raw_category.get("data_tables", []),
            "pdf_documents": pdf_documents,
        }

    return {
        "bank_id": raw_bank_data["bank_id"],
        "bank_name": raw_bank_data["bank_name"],
        "categories": normalized_categories,
    }


def build_knowledge_base(bank_ids: list[str] | None = None) -> dict[str, Any]:
    selected_bank_ids = bank_ids or list(SCRAPER_REGISTRY.keys())
    banks = []

    for bank_id in selected_bank_ids:
        logger.info("Scraping %s", bank_id)
        raw_bank_data = SCRAPER_REGISTRY[bank_id]()
        banks.append(normalize_bank_data(raw_bank_data))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "banks": banks,
    }


def render_markdown(knowledge_base: dict[str, Any]) -> str:
    lines = [
        "# Armenian Bank Knowledge Base",
        "",
        f"Generated at: {knowledge_base['generated_at']}",
        "",
    ]

    for bank in knowledge_base["banks"]:
        lines.append(f"## {bank['bank_name']}")
        lines.append("")

        for category_key in REQUIRED_CATEGORIES:
            category = bank["categories"][category_key]
            lines.append(f"### {category['label']}")
            lines.append("")

            if category["source_urls"]:
                lines.append("Source URLs:")
                for url in category["source_urls"]:
                    lines.append(f"- {url}")
                lines.append("")

            if category["pages"]:
                lines.append("Pages:")
                for page in category["pages"]:
                    lines.append(f"#### {page['title'] or page['url']}")
                    lines.append(f"URL: {page['url']}")
                    if page["headings"]:
                        lines.append("Headings:")
                        for heading in page["headings"]:
                            lines.append(f"- {heading}")
                    if page["text_chunks"]:
                        lines.append("Page Text Chunks:")
                        for idx, chunk in enumerate(page["text_chunks"], start=1):
                            lines.append(f"{idx}. {chunk}")
                    if page["data_tables"]:
                        lines.append("Page Tables:")
                        for idx, table in enumerate(page["data_tables"], start=1):
                            lines.append(f"- Table {idx}:")
                            lines.append("```json")
                            lines.append(json.dumps(table, ensure_ascii=False, indent=2))
                            lines.append("```")
                    if page["pdf_documents"]:
                        lines.append("Page PDFs:")
                        for pdf_doc in page["pdf_documents"]:
                            lines.append(f"- {pdf_doc['title']}: {pdf_doc['url']}")
                            for idx, chunk in enumerate(pdf_doc["content_chunks"], start=1):
                                lines.append(f"  - chunk {idx}: {chunk}")
                    lines.append("")

    return "\n".join(lines).strip() + "\n"


def validate_knowledge_base(knowledge_base: dict[str, Any], expected_banks: list[str]) -> list[str]:
    errors: list[str] = []
    banks_by_id = {bank["bank_id"]: bank for bank in knowledge_base.get("banks", [])}

    for bank_id in expected_banks:
        if bank_id not in banks_by_id:
            errors.append(f"Missing bank: {bank_id}")
            continue

        categories = banks_by_id[bank_id].get("categories", {})
        for category_key in REQUIRED_CATEGORIES:
            category = categories.get(category_key)
            if not category:
                errors.append(f"{bank_id} missing category: {category_key}")
                continue

            if not any(
                (
                    category.get("text_chunks"),
                    category.get("data_tables"),
                    category.get("pdf_documents"),
                )
            ):
                errors.append(f"{bank_id} category has no usable content: {category_key}")

    return errors


def write_outputs(knowledge_base: dict[str, Any]) -> None:
    JSON_OUTPUT_PATH.write_text(json.dumps(knowledge_base, indent=2, ensure_ascii=False), encoding="utf-8")
    MARKDOWN_OUTPUT_PATH.write_text(render_markdown(knowledge_base), encoding="utf-8")
    logger.info("Wrote %s and %s", JSON_OUTPUT_PATH, MARKDOWN_OUTPUT_PATH)


def compile_knowledge_base(bank_id: str | None = None, strict: bool = False) -> dict[str, Any]:
    bank_ids = [bank_id] if bank_id else list(SCRAPER_REGISTRY.keys())
    knowledge_base = build_knowledge_base(bank_ids=bank_ids)
    write_outputs(knowledge_base)

    errors = validate_knowledge_base(knowledge_base, expected_banks=bank_ids)
    if strict and errors:
        raise SystemExit("Knowledge base validation failed:\n- " + "\n- ".join(errors))

    return knowledge_base


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile the Armenian bank knowledge base.")
    parser.add_argument("--bank", choices=sorted(SCRAPER_REGISTRY.keys()), help="Compile a single bank.")
    parser.add_argument("--strict", action="store_true", help="Fail if required categories are empty.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    compile_knowledge_base(bank_id=args.bank, strict=args.strict)


if __name__ == "__main__":
    main()
