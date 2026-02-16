"""Canonical schema for power plant entries.

This module defines the data model used both for the expert reference dataset
and for system outputs. All evaluation is performed on normalized instances
of these models.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FuelType(str, Enum):
    COAL = "coal"
    GAS = "gas"
    IMPORTED_LNG = "imported lng"
    OIL = "oil"
    UNKNOWN = "unknown"


class PlantStatus(str, Enum):
    RETIRED = "retired"
    OPERATIONAL = "operational"
    CONSTRUCTING = "constructing"
    PLANNED = "planned"
    PROPOSED = "proposed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class Plant(BaseModel):
    """A single power plant entry in canonical form.

    One row = one plant (not unit, not complex).  See ADR-4.
    """

    name: str = Field(..., description="Canonical plant name.")
    fuel: FuelType = Field(default=FuelType.UNKNOWN)
    status: PlantStatus = Field(default=PlantStatus.UNKNOWN)
    cod: Optional[str] = Field(default=None, description="Connection date (year or YYYY-MM-DD).")
    province: Optional[str] = Field(default=None)
    capacity_mwe: Optional[float] = Field(default=None, ge=0)


class SourcedPlant(Plant):
    """Plant entry with provenance information, for system outputs."""

    sources: list[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class MatchType(str, Enum):
    EXACT = "exact"
    EXACT_CAPACITY_DIFF = "exact_capacity_diff"
    FUZZY = "fuzzy"
    FUZZY_CAPACITY_DIFF = "fuzzy_capacity_diff"
    SYSTEM_ONLY = "system_only"
    REFERENCE_ONLY = "reference_only"


class ReconciliationEntry(BaseModel):
    """One row in the reconciliation table."""

    reference_name: Optional[str] = None
    system_name: Optional[str] = None
    reference_province: Optional[str] = None
    system_province: Optional[str] = None
    reference_fuel: Optional[str] = None
    system_fuel: Optional[str] = None
    reference_capacity_mwe: Optional[float] = None
    system_capacity_mwe: Optional[float] = None
    capacity_diff_pct: Optional[float] = None
    match_type: MatchType = MatchType.REFERENCE_ONLY
    fuel_match: Optional[bool] = None
    status_match: Optional[bool] = None
    province_match: Optional[bool] = None
    notes: str = ""
