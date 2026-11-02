"""Read-only client for the ProfitEMS installation data API."""

from typing import Any

import aiohttp

from .const import API_URL

_TIMEOUT = aiohttp.ClientTimeout(total=20)


class ProfitEmsError(Exception):
    """The API could not be reached or returned an unexpected response."""


class InvalidAuth(ProfitEmsError):
    """The access key is invalid, disabled or no longer valid for this installation."""


class RateLimited(ProfitEmsError):
    """The request limit was exceeded."""

    def __init__(self, retry_after: int | None) -> None:
        super().__init__("Request limit exceeded")
        self.retry_after = retry_after


class ProfitEmsClient:
    """Fetches installation data. The API offers no way to control the inverter."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        self._session = session
        self._headers = {"Authorization": f"Bearer {api_key}"}

    async def async_get_installation(self) -> dict[str, Any]:
        """Return the current installation data."""
        try:
            async with self._session.get(
                API_URL, headers=self._headers, timeout=_TIMEOUT
            ) as response:
                if response.status == 401:
                    raise InvalidAuth
                if response.status == 429:
                    raise RateLimited(_parse_retry_after(response.headers.get("Retry-After")))
                if response.status != 200:
                    raise ProfitEmsError(f"Unexpected response status {response.status}")
                data = await response.json()
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise ProfitEmsError(type(err).__name__) from err
        if not isinstance(data, dict) or not data.get("numerBramki"):
            raise ProfitEmsError("Unexpected response body")
        return data


def _parse_retry_after(value: str | None) -> int | None:
    return int(value) if value and value.isdecimal() else None
