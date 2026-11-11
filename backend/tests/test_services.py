from datetime import date
from decimal import Decimal

from app.services import build_forecast, evaluate_discount, vat_amount


def test_vat_amount_for_outgoing_invoice():
    assert vat_amount(Decimal("1000000"), 27) == Decimal("270000.00")


def test_discount_is_recommended_when_apr_beats_credit_rate():
    decision = evaluate_discount(Decimal("1000000"), 27, 30, 7, Decimal("2"), Decimal("12"), Decimal("5000000"))
    assert decision.apr == Decimal("32.38")
    assert decision.status == "RECOMMENDED"


def test_discount_boundary_and_credit_limit_are_not_recommended():
    equal_rate = evaluate_discount(Decimal("1000000"), 0, 30, 7, Decimal("0.75"), Decimal("12"), Decimal("5000000"))
    over_limit = evaluate_discount(Decimal("1000000"), 27, 30, 7, Decimal("2"), Decimal("12"), Decimal("100"))
    assert equal_rate.status == "NOT_RECOMMENDED"
    assert over_limit.status == "NOT_RECOMMENDED"


def test_cashflow_reports_negative_balance():
    points = build_forecast(
        date(2026, 11, 1), Decimal("1000"),
        [{"direction": "OUTGOING", "amount": Decimal("2000"), "vat_amount": Decimal("0"), "due_date": date(2026, 11, 2)}],
        Decimal("0"), 3,
    )
    assert points[1].balance == Decimal("-1000.00")
    assert points[1].deficit == Decimal("1000.00")