import logging
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit

from playwright.sync_api import BrowserContext, Page, sync_playwright

from .pdf_parser import extract_text_from_pdf
from .utils import extract_tables_as_json

logger = logging.getLogger("scraper.base")

COMMON_NOISE_EXACT = {
    "EN",
    "IR",
    "Հայերեն",
    "English version",
    "Օնլայն բանկինգ",
    "I-BANKING",
}
COMMON_NOISE_CONTAINS = (
    "բոլոր իրավունքները պաշտպանված են",
    "վերահսկվում է հայաստանի հանրապետության կենտրոնական բանկի կողմից",
    "վերահսկվում է ՀՀ կենտրոնական բանկի կողմից",
    "privacy statement",
    "terms of use",
)
BLOCKED_SCHEMES = ("mailto:", "tel:", "javascript:")


@dataclass(frozen=True)
class CategoryTarget:
    key: str
    label: str
    path: str
    seed_paths: tuple[str, ...] = ()
    child_prefixes: tuple[str, ...] = ()
    child_keywords: tuple[str, ...] = ()
    excluded_keywords: tuple[str, ...] = ()
    max_child_pages: int = 4
    max_pdfs: int = 5


@dataclass
class BankScraper:
    bank_id: str
    bank_name: str
    base_url: str
    targets: tuple[CategoryTarget, ...]
    ignore_line_contains: tuple[str, ...] = field(default_factory=tuple)
    blocked_url_substrings: tuple[str, ...] = (
        "/en/",
        "/ru/",
        "lang=en",
        "lang=ru",
        "locale=en",
        "locale=ru",
    )

    def scrape(self) -> dict[str, Any]:
        categories: dict[str, dict[str, Any]] = {}

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1600, "height": 1200},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
            )
            try:
                for target in self.targets:
                    categories[target.key] = self._scrape_category(context, target)
            finally:
                browser.close()

        return {
            "bank_id": self.bank_id,
            "bank_name": self.bank_name,
            "categories": categories,
        }

    def _scrape_category(self, context: BrowserContext, target: CategoryTarget) -> dict[str, Any]:
        category_data = {
            "label": target.label,
            "source_urls": [],
            "pages": [],
            "raw_texts": [],
            "data_tables": [],
            "pdf_documents": [],
        }
        seen_urls: set[str] = set()
        seen_texts: set[str] = set()
        seen_tables: set[str] = set()
        seen_pdfs: set[str] = set()

        page = context.new_page()
        try:
            root_url = self._absolute_url(target.path)
            root_page = self._visit_page(page, root_url)
            seed_urls = [self._absolute_url(path) for path in target.seed_paths]
            if root_page:
                child_urls = self._discover_child_urls(page, target)
                urls_to_scrape = self._unique_urls([root_page, *seed_urls, *child_urls[: target.max_child_pages]])
            else:
                urls_to_scrape = self._unique_urls(seed_urls)

            for url in urls_to_scrape:
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                remaining_pdf_budget = max(target.max_pdfs - len(category_data["pdf_documents"]), 0)
                page_data = self._extract_page_data(context, url, target, pdf_budget=remaining_pdf_budget)
                if not page_data["url"]:
                    continue
                category_data["source_urls"].append(url)
                category_data["pages"].append(page_data)

                for text in page_data["raw_texts"]:
                    fingerprint = self._normalize_space(text)
                    if fingerprint and fingerprint not in seen_texts:
                        seen_texts.add(fingerprint)
                        category_data["raw_texts"].append(text)

                for table in page_data["data_tables"]:
                    fingerprint = self._normalize_space(str(table))
                    if fingerprint and fingerprint not in seen_tables:
                        seen_tables.add(fingerprint)
                        category_data["data_tables"].append(table)

                for pdf_doc in page_data["pdf_documents"]:
                    pdf_url = pdf_doc["url"]
                    if pdf_url in seen_pdfs or len(category_data["pdf_documents"]) >= target.max_pdfs:
                        continue
                    seen_pdfs.add(pdf_url)
                    category_data["pdf_documents"].append(pdf_doc)
        finally:
            page.close()

        return category_data

    def _extract_page_data(
        self, context: BrowserContext, url: str, target: CategoryTarget, pdf_budget: int
    ) -> dict[str, Any]:
        page = context.new_page()
        try:
            final_url = self._visit_page(page, url)
            if not final_url:
                return {
                    "title": "",
                    "url": "",
                    "headings": [],
                    "raw_texts": [],
                    "data_tables": [],
                    "pdf_documents": [],
                }

            text = self._clean_page_text(page.locator("body").inner_text())
            tables = extract_tables_as_json(page.locator("body"))
            pdf_documents = self._collect_pdf_documents(page, target, pdf_budget)
            headings = self._collect_page_headings(page)
            title = self._normalize_space(page.title())

            return {
                "title": title,
                "url": final_url,
                "headings": headings,
                "raw_texts": [text] if len(text) >= 200 else [],
                "data_tables": tables,
                "pdf_documents": pdf_documents,
            }
        finally:
            page.close()

    def _collect_pdf_documents(self, page: Page, target: CategoryTarget, pdf_budget: int) -> list[dict[str, Any]]:
        pdf_documents: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        if pdf_budget <= 0:
            return pdf_documents

        for link in page.locator("a[href]").all():
            href = (link.get_attribute("href") or "").strip()
            if not href or not href.lower().endswith(".pdf") and ".pdf?" not in href.lower():
                continue

            pdf_url = self._absolute_url(href)
            if not self._is_same_domain(pdf_url) or self._is_blocked_url(pdf_url) or pdf_url in seen_urls:
                continue

            seen_urls.add(pdf_url)
            title = self._normalize_space(link.inner_text()) or pdf_url.rsplit("/", 1)[-1]
            pdf_text = extract_text_from_pdf(pdf_url)
            if not pdf_text or pdf_text.startswith("Error "):
                continue

            pdf_documents.append({"title": title, "url": pdf_url, "content": pdf_text})
            if len(pdf_documents) >= min(target.max_pdfs, pdf_budget):
                break

        return pdf_documents

    def _discover_child_urls(self, page: Page, target: CategoryTarget) -> list[str]:
        child_urls: list[str] = []
        seen_urls: set[str] = set()

        for link in page.locator("a[href]").all():
            href = (link.get_attribute("href") or "").strip()
            if not href or href.startswith(BLOCKED_SCHEMES):
                continue

            absolute_url = self._absolute_url(href)
            if not self._is_same_domain(absolute_url) or self._is_blocked_url(absolute_url):
                continue

            parsed = urlparse(absolute_url)
            haystack = f"{parsed.path.lower()} {parsed.query.lower()} {link.inner_text().strip().lower()}"
            if target.excluded_keywords and any(keyword in haystack for keyword in target.excluded_keywords):
                continue

            matches_prefix = not target.child_prefixes or any(
                parsed.path.startswith(prefix) for prefix in target.child_prefixes
            )
            matches_keyword = not target.child_keywords or any(keyword in haystack for keyword in target.child_keywords)

            if target.child_prefixes and target.child_keywords:
                if not (matches_prefix and matches_keyword):
                    continue
            elif target.child_prefixes and not matches_prefix:
                continue
            elif target.child_keywords and not matches_keyword:
                continue

            normalized = absolute_url.rstrip("/")
            if normalized in seen_urls:
                continue

            seen_urls.add(normalized)
            child_urls.append(normalized)

        return child_urls

    def _visit_page(self, page: Page, url: str) -> str | None:
        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                page.wait_for_timeout(1500)
            self._dismiss_cookie_banner(page)
            return self._canonicalize_url(page.url)
        except Exception as exc:
            logger.warning("Failed to load %s for %s: %s", url, self.bank_name, exc)
            return None

    def _dismiss_cookie_banner(self, page: Page) -> None:
        for name in ("Accept", "I agree", "Agree"):
            try:
                button = page.get_by_role("button", name=name).first
                if button.is_visible(timeout=1000):
                    button.click()
                    page.wait_for_timeout(500)
                    return
            except Exception:
                continue

    def _collect_page_headings(self, page: Page) -> list[str]:
        headings: list[str] = []
        seen: set[str] = set()

        for selector in ("h1", "h2", "h3"):
            for element in page.locator(selector).all():
                heading = self._normalize_space(element.inner_text())
                if not heading or heading in seen:
                    continue
                seen.add(heading)
                headings.append(heading)
                if len(headings) >= 20:
                    return headings

        return headings

    def _clean_page_text(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines()]
        cleaned_lines: list[str] = []
        seen_compact: set[str] = set()

        for line in lines:
            if not line:
                continue

            compact = self._normalize_space(line)
            compact_lower = compact.lower()

            if compact in COMMON_NOISE_EXACT:
                continue
            if any(phrase in compact_lower for phrase in COMMON_NOISE_CONTAINS):
                continue
            if any(phrase in compact_lower for phrase in self.ignore_line_contains):
                continue
            if len(compact) < 2:
                continue
            if compact in seen_compact:
                continue

            seen_compact.add(compact)
            cleaned_lines.append(compact)

        return "\n".join(cleaned_lines)

    def _absolute_url(self, href: str) -> str:
        return self._canonicalize_url(urljoin(self.base_url, href))

    def _is_same_domain(self, url: str) -> bool:
        return urlparse(url).netloc == urlparse(self.base_url).netloc

    def _is_blocked_url(self, url: str) -> bool:
        lowered = url.lower()
        return any(token in lowered for token in self.blocked_url_substrings)

    @staticmethod
    def _canonicalize_url(url: str) -> str:
        parts = urlsplit(url)
        normalized_path = parts.path.rstrip("/") or "/"
        return urlunsplit((parts.scheme, parts.netloc.lower(), normalized_path, parts.query, ""))

    @staticmethod
    def _normalize_space(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _unique_urls(urls: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []

        for url in urls:
            if not url or url in seen:
                continue
            seen.add(url)
            ordered.append(url)

        return ordered
