import logging

from .base import BankScraper, CategoryTarget

logger = logging.getLogger("scraper.mellatbank")
logger.setLevel(logging.INFO)


class MellatBankScraper(BankScraper):
    def __init__(self) -> None:
        super().__init__(
            bank_id="mellatbank",
            bank_name="Mellat Bank",
            base_url="https://mellatbank.am",
            ignore_line_contains=("slide 1 of", "ավելին...", "english version"),
            targets=(
                CategoryTarget(
                    key="deposits",
                    label="Deposits",
                    path="/hy/Deposits",
                    child_prefixes=("/hy/Deposits",),
                    child_keywords=("deposit", "ավանդ"),
                    excluded_keywords=("depositbox", "safe-box"),
                    max_child_pages=0,
                    max_pdfs=4,
                ),
                CategoryTarget(
                    key="credits",
                    label="Credits",
                    path="/hy/loans_individual",
                    seed_paths=(
                        "/hy/Mortgage-loan1",
                        "/hy/repair_loan",
                        "/hy/student_loan",
                        "/hy/Car_loan",
                        "/hy/Express_consumer_loan",
                        "/hy/Privileged_Loan%20",
                        "/hy/loans_business",
                        "/hy/Business_Loan_1",
                        "/hy/Developer_loan",
                        "/hy/Express_Business_Loan",
                    ),
                    child_prefixes=("/hy/loans",),
                    child_keywords=("loan", "վարկ", "mortgage"),
                    max_child_pages=0,
                    max_pdfs=3,
                ),
                CategoryTarget(
                    key="branches",
                    label="Branches",
                    path="/hy/About%20Us",
                    child_keywords=("contact", "կապ"),
                    max_child_pages=0,
                    max_pdfs=1,
                ),
            ),
        )


def run_scraper() -> dict:
    return MellatBankScraper().scrape()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json

    print(json.dumps(run_scraper(), indent=2, ensure_ascii=False))
