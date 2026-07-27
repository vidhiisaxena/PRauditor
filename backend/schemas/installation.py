from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class InstallationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    github_installation_id: int
    account_login: Optional[str] = None
    account_type: Optional[str] = None


class InstallationStatusOut(BaseModel):
    """Response for GET /api/installations — read purely from our DB."""

    installed: bool
    installations: List[InstallationSummary]


class RepositorySummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    private: Optional[bool] = None
    active: bool
