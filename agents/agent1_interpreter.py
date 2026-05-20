from pydantic import BaseModel
from typing import Optional

class PICOResult(BaseModel):
    population: str
    intervention: str
    comparison: Optional[str] = None
    outcome: str
    original_query: str