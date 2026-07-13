from datetime import datetime, timezone

import httpx

from app.platforms.base import NormalizedSubmission, PlatformClient

BASE_URL = "https://codeforces.com/api"


class CodeforcesClient(PlatformClient):
    """Fetches submissions from the public Codeforces API (no auth required)."""

    name = "codeforces"

    def fetch_recent(self, count: int = 20) -> list[NormalizedSubmission]:
        resp = httpx.get(
            f"{BASE_URL}/user.status",
            params={"handle": self.username, "from": 1, "count": count},
            timeout=20,
        )
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") != "OK":
            return []

        out: list[NormalizedSubmission] = []
        for s in payload.get("result", []):
            problem = s.get("problem", {})
            contest_id = problem.get("contestId")
            index = problem.get("index")
            external_problem_id = f"{contest_id}{index}" if contest_id else str(index or "")
            rating = problem.get("rating")
            difficulty = None
            if rating is not None:
                difficulty = "hard" if rating >= 1900 else "medium" if rating >= 1400 else "easy"

            memory_bytes = s.get("memoryConsumedBytes")
            out.append(
                NormalizedSubmission(
                    external_id=str(s["id"]),
                    external_problem_id=external_problem_id,
                    title=problem.get("name", external_problem_id),
                    accepted=s.get("verdict") == "OK",
                    submitted_at=datetime.fromtimestamp(s["submittedSeconds"], tz=timezone.utc),
                    language=s.get("programmingLanguage"),
                    difficulty=difficulty,
                    runtime_ms=s.get("timeConsumedMillis"),
                    memory_kb=(memory_bytes // 1024) if memory_bytes is not None else None,
                    topics=problem.get("tags", []),
                    url=(
                        f"https://codeforces.com/contest/{contest_id}/problem/{index}"
                        if contest_id
                        else None
                    ),
                )
            )
        return out
