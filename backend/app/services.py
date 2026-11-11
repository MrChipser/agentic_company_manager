from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP


MONEY_PLACES = Decimal("0.01")
ALLOWED_VAT_RATES = {0, 5, 18, 27}


def money(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def validate_invoice_input(
    amount: Decimal,
    vat_rate: int,
    due_date: date,
    discount_days: int | None,
    discount_rate: Decimal | None,
) -> None:
    if amount <= 0:
        raise ValueError("Az összegnek pozitívnak kell lennie.")
    if vat_rate not in ALLOWED_VAT_RATES:
        raise ValueError("Az ÁFA-kulcs csak 0, 5, 18 vagy 27 lehet.")
    if discount_days is not None and discount_days >= (due_date - date.today()).days:
        raise ValueError("A korai fizetési határidőnek a teljes határidő előtt kell lennie.")
    if discount_rate is not None and not 0 <= discount_rate < 100:
        raise ValueError("A skontó százaléka 0 és 100 között lehet.")


def vat_amount(net_amount: Decimal, vat_rate: int) -> Decimal:
    return money(net_amount * Decimal(vat_rate) / Decimal(100))


def discount_apr(
    total_days: int, early_days: int, discount_rate: Decimal
) -> Decimal:
    if early_days >= total_days or early_days < 0:
        raise ValueError("A korai fizetési napnak a teljes határidő előtt kell lennie.")
    remaining_days = total_days - early_days
    return (discount_rate / (Decimal(100) - discount_rate) * Decimal(365) / remaining_days * 100).quantize(
        MONEY_PLACES, rounding=ROUND_DOWN
    )


@dataclass(frozen=True)
class DiscountDecision:
    apr: Decimal
    status: str
    saving: Decimal
    reason: str


def evaluate_discount(
    net_amount: Decimal,
    vat_rate: int,
    total_days: int,
    early_days: int,
    discount_rate: Decimal,
    credit_rate: Decimal,
    credit_limit: Decimal,
) -> DiscountDecision:
    gross_amount = money(net_amount + vat_amount(net_amount, vat_rate))
    saving = money(gross_amount * discount_rate / Decimal(100))
    apr = discount_apr(total_days, early_days, discount_rate)
    within_limit = gross_amount <= credit_limit
    recommended = apr > credit_rate and within_limit and saving > 0
    if recommended:
        reason = f"A skontó APR-je {apr}% és meghaladja a {credit_rate}% hitelkamatot."
        status = "RECOMMENDED"
    elif not within_limit:
        reason = "A kifizetés túllépné a rendelkezésre álló hitelkeretet."
        status = "NOT_RECOMMENDED"
    else:
        reason = f"A skontó APR-je {apr}%, nem haladja meg a {credit_rate}% hitelkamatot."
        status = "NOT_RECOMMENDED"
    return DiscountDecision(apr, status, saving, reason)


@dataclass(frozen=True)
class ForecastPoint:
    day: date
    balance: Decimal
    vat_due: Decimal
    deficit: Decimal


def build_forecast(
    start_day: date,
    starting_balance: Decimal,
    invoices: list[dict],
    vat_balance: Decimal,
    days: int = 30,
    vat_due_day: int = 20,
) -> list[ForecastPoint]:
    balance = money(starting_balance)
    current_vat = money(vat_balance)
    points: list[ForecastPoint] = []
    for offset in range(days):
        current_day = start_day + timedelta(days=offset)
        for invoice in invoices:
            if invoice["due_date"] == current_day:
                gross = money(invoice["amount"] + invoice["vat_amount"])
                balance += gross if invoice["direction"] == "INCOME" else -gross
        vat_due = money(0)
        if current_day.day == vat_due_day:
            vat_due = max(current_vat, money(0))
            balance -= vat_due
            current_vat = money(0)
        balance = money(balance)
        deficit = money(-balance) if balance < 0 else money(0)
        points.append(ForecastPoint(current_day, balance, vat_due, deficit))
    return points