import logging

from .base import BankScraper, CategoryTarget

logger = logging.getLogger("scraper.ardshinbank")
logger.setLevel(logging.INFO)


class ArdshinbankScraper(BankScraper):
    def __init__(self) -> None:
        super().__init__(
            bank_id="ardshinbank",
            bank_name="Ardshinbank",
            base_url="https://ardshinbank.am",
            ignore_line_contains=("ուշադրություն.", "download our official apps"),
            targets=(
                CategoryTarget(
                    key="deposits",
                    label="Deposits",
                    path="/for-you/avand?lang=hy",
                    seed_paths=(
                        "/for-your-business/deposit",
                    ),
                    child_prefixes=("/for-you/avand",),
                    child_keywords=("ավանդ", "deposit"),
                    max_child_pages=0,
                    max_pdfs=5,
                ),
                CategoryTarget(
                    key="credits",
                    label="Credits",
                    path="/for-you/loans-ardshinbank",
                    seed_paths=(
                        "/for-you/consumer-loans",
                        "/for-you/mortgage",
                        "/for-you/ansharj-guyqi-gravov-varker",
                        "/for-you/cash-collateral-loans",
                        "/for-you/vark-zincarayoxnerin",
                        "/for-you/Usanoxakan-varker",
                        "/for-you/vosku-gravov-sparoxakan-vark",
                        "/for-you/varkeri-verakarucum",
                        "/for-you/varkayin-gits",
                        "/for-you/mortgage-ss-yeghbairner",
                        "/for-you/mortgage-filishin",
                        "/for-you/vark-hanrayin-carayoxnerin",
                        "/for-you/mortgage-non-resident",
                        "/for-you/mortgage-refinancing",
                        "/for-you/mortgage-loan-repairs-simplified",
                        "/for-you/mortgage-muller",
                        "/for-you/credits-secured-by-bonds",
                        "/for-you/veranorogum",
                        "/for-you/karucum",
                        "/for-your-business/loan",
                        "/for-your-business/parz-vark",
                        "/for-your-business/Overdraft-SME",
                        "/for-your-business/sme-express",
                        "/for-your-business/sme-flexi",
                        "/for-your-business/sme-loans",
                        "/for-your-business/refinancing-of-business-loans",
                        "/for-your-business/varkatesakner",
                        "/for-your-business/loans-sme",
                    ),
                    child_prefixes=(
                        "/for-you/loans-ardshinbank",
                        "/for-you/consumer-loans",
                        "/for-you/cash-collateral-loans",
                        "/for-you/ansharj-guyqi-gravov-varker",
                    ),
                    child_keywords=("վարկ", "loan"),
                    excluded_keywords=("mobile-banking", "payment-card", "card", "deposit"),
                    max_child_pages=0,
                    max_pdfs=8,
                ),
                CategoryTarget(
                    key="branches",
                    label="Branches",
                    path="/Information/branch-atm",
                    child_keywords=("մասնաճյուղ", "atm", "բանկոմատ"),
                    max_child_pages=0,
                    max_pdfs=1,
                ),
            ),
        )


def run_scraper() -> dict:
    return ArdshinbankScraper().scrape()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json

    print(json.dumps(run_scraper(), indent=2, ensure_ascii=False))
