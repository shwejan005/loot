from datetime import datetime, timezone

import httpx

from app.config import settings
from app.platforms.base import NormalizedSubmission, PlatformClient

GRAPHQL_URL = "https://leetcode.com/graphql/"

# recentSubmissionList returns accepted AND rejected submissions (recent first).
RECENT_SUBMISSIONS_QUERY = """
query recentSubmissions($username: String!, $limit: Int!) {
  recentSubmissionList(username: $username, limit: $limit) {
    id
    title
    titleSlug
    statusDisplay
    lang
    timestamp
  }
}
"""


class LeetCodeClient(PlatformClient):
    """Fetches submissions from LeetCode's GraphQL endpoint.

    A `LEETCODE_SESSION` cookie is required for private submission history.
    Without it the request may be rate-limited or return empty results.
    """

    name = "leetcode"

    def __init__(self, username: str, session: str | None = None) -> None:
        super().__init__(username)
        self.session = session or settings.leetcode_session

    def fetch_recent(self, count: int = 20) -> list[NormalizedSubmission]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Loot/0.1 (coding-memory)",
            "Referer": "https://leetcode.com",
        }
        if self.session:
            headers["Cookie"] = f"LEETCODE_SESSION={self.session}"

        body = {
            "query": RECENT_SUBMISSIONS_QUERY,
            "variables": {"username": self.username, "limit": count},
        }
        resp = httpx.post(GRAPHQL_URL, json=body, headers=headers, timeout=20)
        resp.raise_for_status()
        payload = resp.json()

        data = payload.get("data") or {}
        submissions = data.get("recentSubmissionList") or []
        if not submissions and payload.get("errors"):
            # Surface upstream GraphQL errors for debugging.
            raise RuntimeError(f"LeetCode GraphQL error: {payload['errors']}")

        out: list[NormalizedSubmission] = []
        for s in submissions:
            ts = int(s["timestamp"])
            slug = s.get("titleSlug")
            out.append(
                NormalizedSubmission(
                    external_id=str(s["id"]),
                    external_problem_id=slug or str(s["id"]),
                    title=s.get("title") or (slug or s["id"]),
                    accepted=s.get("statusDisplay") == "Accepted",
                    submitted_at=datetime.fromtimestamp(ts, tz=timezone.utc),
                    language=s.get("lang"),
                    difficulty=None,
                    runtime_ms=None,
                    memory_kb=None,
                    topics=[],
                    url=f"https://leetcode.com/problems/{slug}/" if slug else None,
                )
            )
        return out
