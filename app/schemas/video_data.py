from typing import Optional

from pydantic import BaseModel


class UploadData(BaseModel):
    scenes: str
    location: str
    violation_category: str
    measure: str
    element: Optional[str] = None
    category: Optional[str] = None
    desc: Optional[str] = None
    basis_measure: Optional[str] = None
