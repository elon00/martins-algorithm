"""
GitHub Activity Adapter
========================
Fetches developer activity data for crypto projects from GitHub.
Used to populate the 'developer_activity' feature in Martin Candidates.

Metrics collected:
  - Recent commits (last 90 days)
  - Open issues count
  - Stars / forks
  - Last push date
  - Number of contributors
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


@dataclass(frozen=True)
class GitHubActivity:
    repo: str
    stars: int
    forks: int
    open_issues: int
    recent_commits: int        # commits in the last 90 days
    contributors: int
    days_since_push: int       # days since last push
    is_archived: bool


class GitHubActivityAdapter:
    """Read-only GitHub activity adapter."""

    def __init__(
        self,
        token: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.timeout = timeout

    def get_activity(self, owner: str, repo: str) -> GitHubActivity | None:
        """
        Fetch activity data for a GitHub repository.
        Returns None if the repo is not found or the request fails.
        """
        try:
            repo_data = self._get(f"/repos/{owner}/{repo}")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.debug("GitHub repo not found: %s/%s", owner, repo)
                return None
            raise

        # Recent commits
        recent_commits = self._count_recent_commits(owner, repo, days=90)

        # Contributors count
        contributors = self._count_contributors(owner, repo)

        # Days since last push
        pushed_at = repo_data.get("pushed_at")
        if pushed_at:
            pushed_dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            days_since = (datetime.now(timezone.utc) - pushed_dt).days
        else:
            days_since = 9999

        return GitHubActivity(
            repo=f"{owner}/{repo}",
            stars=repo_data.get("stargazers_count", 0),
            forks=repo_data.get("forks_count", 0),
            open_issues=repo_data.get("open_issues_count", 0),
            recent_commits=recent_commits,
            contributors=contributors,
            days_since_push=days_since,
            is_archived=repo_data.get("archived", False),
        )

    def developer_activity_score(self, owner: str, repo: str) -> float:
        """
        Return a developer activity score in [0, 1].
        Used for the 'developer_activity' feature in Martin Candidates.
        """
        activity = self.get_activity(owner, repo)
        if activity is None:
            return 0.0

        if activity.is_archived:
            return 0.05  # archived = mostly dead

        score = 0.0

        # Recent commits: 0 → 0, 50+ → 0.40
        score += min(0.40, activity.recent_commits / 50.0 * 0.40)

        # Freshness: pushed today → 0.30, pushed 365d ago → 0
        freshness = max(0.0, 1.0 - activity.days_since_push / 365.0)
        score += 0.30 * freshness

        # Stars/forks signal: log-normalized
        import math
        star_signal = min(1.0, math.log1p(activity.stars) / math.log1p(10000))
        score += 0.15 * star_signal

        # Contributors: 1 person → low, 10+ → full
        contrib_signal = min(1.0, activity.contributors / 10.0)
        score += 0.15 * contrib_signal

        return min(1.0, score)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _count_recent_commits(self, owner: str, repo: str, days: int) -> int:
        from datetime import timedelta
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        try:
            data = self._get(
                f"/repos/{owner}/{repo}/commits",
                params={"since": since, "per_page": 100},
            )
            return len(data) if isinstance(data, list) else 0
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError):
            return 0

    def _count_contributors(self, owner: str, repo: str) -> int:
        try:
            data = self._get(
                f"/repos/{owner}/{repo}/contributors",
                params={"per_page": 100, "anon": "false"},
            )
            return len(data) if isinstance(data, list) else 0
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError):
            return 0

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(GITHUB_API + path, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
