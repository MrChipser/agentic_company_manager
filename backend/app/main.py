from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .db import Database
from .services import (
    ALLOWED_VAT_RATES,
    build_forecast,
    evaluate_discount,
    validate_invoice_input,
    vat_amount,
)


class InvoiceInput(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"direction": "OUTGOING", "amount": "1000000", "vat_rate": 27}})

    direction: str
    amount: Decimal = Field(gt=0)
    vat_rate: int
    issue_date: date = Field(default_factory=date.today)
    due_date: date = Field(default_factory=date.today)
    partner_name: str = Field(default="Demo partner", min_length=1)
    discount_days: int | None = Field(default=None, ge=0)
    discount_rate: Decimal | None = Field(default=None, ge=0, lt=100)
    credit_rate: Decimal = Field(default=Decimal("12.00"), ge=0)
    credit_limit: Decimal = Field(default=Decimal("5000000.00"), gt=0)

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, value: str) -> str:
        if value not in {"INCOMING", "OUTGOING"}:
            raise ValueError("Az irány INCOMING vagy OUTGOING lehet.")
        return value


class LoginInput(BaseModel):
    email: str
    password: str


app = FastAPI(title="KKV pénzügyi manager", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
db = Database(os.getenv("DATABASE_PATH", "financial_manager.db"))


def require_token(authorization: Annotated[str | None, Header()] = None) -> str:
    if authorization != "Bearer demo-token":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Érvénytelen vagy hiányzó token.")
    return "demo-admin"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(payload: LoginInput) -> dict[str, str]:
    if payload.email != "admin@demo.hu" or payload.password != "admin":
        raise HTTPException(status_code=401, detail="Hibás bejelentkezési adatok.")
    return {"access_token": "demo-token", "token_type": "bearer"}


@app.post("/api/invoices", status_code=200)
def create_invoice(payload: InvoiceInput, _: Annotated[str, Depends(require_token)]) -> dict:
    if payload.vat_rate not in ALLOWED_VAT_RATES:
        raise HTTPException(status_code=422, detail="Érvénytelen ÁFA-kulcs.")
    total_days = (payload.due_date - payload.issue_date).days
    if total_days <= 0:
        raise HTTPException(status_code=422, detail="Az esedékességnek a kiállítás után kell lennie.")
    try:
        validate_invoice_input(payload.amount, payload.vat_rate, payload.due_date, payload.discount_days, payload.discount_rate)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    calculated_vat = vat_amount(payload.amount, payload.vat_rate)
    data = payload.model_dump()
    data["vat_amount"] = calculated_vat
    invoice_id = db.add_invoice(data)
    recommendation = None
    if payload.discount_days is not None and payload.discount_rate is not None:
        decision = evaluate_discount(
            payload.amount, payload.vat_rate, total_days, payload.discount_days,
            payload.discount_rate, payload.credit_rate, payload.credit_limit,
        )
        recommendation = {
            "status": decision.status,
            "apr": str(decision.apr),
            "saving": str(decision.saving),
            "reason": decision.reason,
        }
    return {"id": invoice_id, "vat_amount": str(calculated_vat), "recommendation": recommendation}


@app.get("/api/invoices")
def invoices(_: Annotated[str, Depends(require_token)]) -> list[dict]:
    return [dict(row) for row in db.list_invoices()]


@app.get("/api/forecast")
def forecast(
    _: Annotated[str, Depends(require_token)],
    days: int = Query(default=30, ge=1, le=90),
    start: date | None = None,
) -> dict:
    state = db.account_state()
    invoice_data = [
        {
            "direction": row["direction"],
            "amount": Decimal(row["amount"]),
            "vat_amount": Decimal(row["vat_amount"]),
            "due_date": date.fromisoformat(row["due_date"]),
        }
        for row in db.list_invoices()
    ]
    points = build_forecast(
        start or date.today(), Decimal(state["starting_balance"]), invoice_data,
        Decimal(state["vat_balance"]), days,
    )
    deficits = [point for point in points if point.deficit > 0]
    return {
        "days": [
            {"date": point.day.isoformat(), "balance": str(point.balance), "vat_due": str(point.vat_due), "deficit": str(point.deficit)}
            for point in points
        ],
        "status": "LIQUIDITY_DEFICIT" if deficits else "OK",
        "deficit": str(max((point.deficit for point in points), default=Decimal("0.00"))),
    }


@app.post("/api/recommendations/{recommendation_id}/approve")
def approve_recommendation(recommendation_id: int, _: Annotated[str, Depends(require_token)]) -> dict:
    return {"id": recommendation_id, "status": "APPROVED"}


def reset_database() -> None:
    db.reset()