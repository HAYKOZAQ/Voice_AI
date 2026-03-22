import logging

from .base import BankScraper, CategoryTarget

logger = logging.getLogger("scraper.ameriabank")
logger.setLevel(logging.INFO)


class AmeriabankScraper(BankScraper):
    def __init__(self) -> None:
        super().__init__(
            bank_id="ameriabank",
            bank_name="Ameriabank",
            base_url="https://ameriabank.am",
            ignore_line_contains=("ասա կարծիքդ",),
            targets=(
                CategoryTarget(
                    key="deposits",
                    label="Deposits",
                    path="/personal/saving/deposits/see-all",
                    seed_paths=(
                        "/personal/saving/deposits/ameria-deposit",
                        "/personal/saving/deposits/kids-deposit",
                        "/personal/saving/deposits/cumulative-deposit",
                        "/business/micro/accounts/deposit-ameria",
                    ),
                    child_prefixes=("/personal/saving/deposits/",),
                    child_keywords=("deposit", "ավանդ"),
                    excluded_keywords=("bond", "obligation", "safe-deposit", "deposit-box", "depositbox"),
                    max_child_pages=0,
                    max_pdfs=4,
                ),
                CategoryTarget(
                    key="credits",
                    label="Credits",
                    path="/personal/loans/consumer-loans/consumer-loans",
                    seed_paths=(
                        "/personal/loans/consumer-loans/overdraft",
                        "/personal/loans/consumer-loans/credit-line",
                        "/personal/loans/consumer-loans/consumer-finance",
                        "/personal/loans/consumer-loan/online-consumer-finance",
                        "/loans/secured-loans/consumer-loan",
                        "/loans/secured-loans/overdraft",
                        "/loans/secured-loans/credit-line",
                        "/personal/loans/other-loans/investment-loan",
                        "/personal/loans/mortgage-loans",
                        "/personal/loans/mortgage/online",
                        "/personal/loans/mortgage/primary-market-loan",
                        "/personal/loans/mortgage/secondary-market",
                        "/personal/loans/mortgage/commercial-mortgage",
                        "/personal/loans/mortgage/renovation-mortgage",
                        "/personal/loans/mortgage/construction-mortgage",
                        "/personal/loans/mortgage/special-offers/for-the-usa-citizens",
                        "/personal/loans/car-loans",
                        "/personal/loans/car-loan/without-bank-visit",
                        "/personal/loans/car-loan/online-secondary-market",
                        "/personal/loans/car-loan/primary",
                        "/personal/loans/car-loan/secondary-market",
                        "/personal/loans/car-loan/secondary-market-unused",
                        "/business/micro/loans",
                        "/business/micro/loans/for-solar-systems",
                        "/business/micro/loans/overdraft-with-business-card",
                        "/business/micro/loans/secured-overdraft-with-business-card",
                        "/business/micro/loans/15-30-mln-with-collateral",
                        "/business/micro/loans/30-150-mln-with-collateral",
                        "/business/micro/loans/online-business-loan",
                        "/business/sme/financing/business-loan",
                        "/business/sme/financing/agricultural-loan",
                        "/business/sme/financing/online-loans",
                        "/business/corporate/financing/business-loan",
                        "/business/corporate/financing/loan-for-renewable-energy",
                    ),
                    child_prefixes=("/personal/loans/consumer-loans/", "/loans/consumer-loans/"),
                    child_keywords=("loan", "վարկ"),
                    max_child_pages=0,
                    max_pdfs=8,
                ),
                CategoryTarget(
                    key="branches",
                    label="Branches",
                    path="/service-network",
                    seed_paths=("/contact-us",),
                    child_keywords=("մասնաճյուղ", "atm", "terminal"),
                    max_child_pages=0,
                    max_pdfs=2,
                ),
            ),
        )


def run_scraper() -> dict:
    return AmeriabankScraper().scrape()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json

    print(json.dumps(run_scraper(), indent=2, ensure_ascii=False))
