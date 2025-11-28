from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RepositoryOut(BaseModel):
    id: int
    full_name: str

    class Config:
        orm_mode = True


class PullRequestOut(BaseModel):
    id: int
    pr_number: int
    title: Optional[str]
    state: Optional[str]
    head_sha: Optional[str]
    last_reviewed_at: Optional[datetime]

    class Config:
        orm_mode = True


class ReviewIssueOut(BaseModel):
    id: int
    file_path: str
    line: Optional[int]
    kind: str
    severity: str
    message: str
    suggestion: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
