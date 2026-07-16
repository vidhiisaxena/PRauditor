from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RepositoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str


class PullRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pr_number: int
    title: Optional[str]
    state: Optional[str]
    head_sha: Optional[str]
    last_reviewed_at: Optional[datetime]


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
