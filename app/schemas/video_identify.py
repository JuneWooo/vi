from typing import Optional

from pydantic import BaseModel


class VideoIdentify(BaseModel):
    scenes: str
    location: str
    violation_category: str


class VideoIdentifyMatch(VideoIdentify):
    desc: Optional[str]
    measure: Optional[str]
    element: Optional[str]
    category: Optional[str]
    basis_measure: Optional[str]
    source: Optional[list]


class VideoIdentifyCustom(VideoIdentify):
    measure: Optional[str]
    source: Optional[list]
