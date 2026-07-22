from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ReviewIssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: str
    line: Optional[int]
    kind: str
    severity: str
    message: str
    suggestion: Optional[str]
    created_at: datetime
