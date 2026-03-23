"""
Pydantic models for structured data.
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str
    amount: str


class ExtractedData(BaseModel):
    invoice_id: str = ""
    client_name: str = ""
    total_amount: str = ""
    due_date: str = ""
    line_items: List[LineItem] = Field(default_factory=list)
    notes: str = ""
