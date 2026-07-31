"""Versioned request and response contracts for model-backed inference."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class LoanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    loan_id: Annotated[int, Field(gt=0)]
    loan_amnt: Annotated[float, Field(gt=0, le=5_000_000)]
    term: Literal["36 months", "60 months"]
    emp_length: Annotated[float, Field(ge=0, le=70)]
    home_ownership: Literal["RENT", "MORTGAGE", "OWN", "OTHER"]
    annual_inc: Annotated[float, Field(gt=0, le=100_000_000)]
    purpose: str = Field(min_length=1, max_length=80)
    dti: Annotated[float, Field(ge=0, le=200)]
    delinq_2yrs: Annotated[int, Field(ge=0, le=100)]
    open_acc: Annotated[int, Field(ge=0, le=500)]
    pub_rec: Annotated[int, Field(ge=0, le=100)]
    revol_util: Annotated[float, Field(ge=0, le=500)]
    total_acc: Annotated[int, Field(ge=0, le=1000)]


class PredictionResponse(BaseModel):
    request_id: str
    risk_probability: float
    review_recommended: bool
    reason_codes: list[str]
    model_version: str
    policy_version: str


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=8, max_length=128)
    outcome: Literal["reviewed", "approved", "declined", "defaulted", "repaid"]
    observed_at: AwareDatetime
