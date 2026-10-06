"""Pydantic request/response models for the REST API."""
from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str
    team_key: str = ""  # empty for admin


class LoginResponse(BaseModel):
    status: str  # "ok" | "error"
    username: str = ""
    team_key: str = ""
    is_controller: bool = False
    is_admin: bool = False
    phase: str = ""  # "start" | "storyboard" | "playing" | "admin"
    play_seed: int = 0
    storyboard_seen: bool = False
    error: str = ""
    admin_token: str = ""  # sent as X-Admin-Token on /api/admin/* requests
    game_state: Optional[dict] = None
    scenario_info: Optional[dict] = None
    slider_constraints: Optional[dict] = None
    competitors: Optional[list] = None


class LockYearRequest(BaseModel):
    team_key: str
    username: str
    allocations: list[float]
    subdecisions: dict[str, str]
    carryover: float = 0.5


class LockYearResponse(BaseModel):
    status: str  # "ok" | "error"
    year: int = 0
    year_result: dict = {}
    game_state: dict = {}
    all_teams_locked: bool = False
    locked_count: int = 0    # teams that have locked this year
    blocking_total: int = 0  # teams participating in the barrier
    error: str = ""


class SetPhaseRequest(BaseModel):
    phase: str  # "storyboard" | "playing"


class PauseRequest(BaseModel):
    paused: bool


class SetScenarioRequest(BaseModel):
    country: str
    industry: str


class AdminStatusResponse(BaseModel):
    teams: list[dict] = []
    sessions: list[dict] = []
    paused: bool = False
    phase: str = ""
    completed_teams: list[str] = []
    pending_teams: list[dict] = []
    leaderboard: list[dict] = []
