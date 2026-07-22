from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PullRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pr_number: int
    title: Optional[str]
    state: Optional[str]
    head_sha: Optional[str]
    last_reviewed_at: Optional[datetime]
