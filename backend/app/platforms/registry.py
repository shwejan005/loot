from app.config import settings
from app.models import PlatformConnection
from app.platforms.base import PlatformClient
from app.platforms.codeforces import CodeforcesClient
from app.platforms.leetcode import LeetCodeClient

SUPPORTED = {
    "codeforces": CodeforcesClient,
    "leetcode": LeetCodeClient,
}


def build_client(conn: PlatformConnection) -> PlatformClient:
    """Instantiate the appropriate client for a platform connection."""
    client_cls = SUPPORTED.get(conn.platform.lower())
    if client_cls is None:
        raise ValueError(f"Unsupported platform: {conn.platform}")
    if conn.platform.lower() == "leetcode":
        return client_cls(conn.external_username, session=settings.leetcode_session)
    return client_cls(conn.external_username)
