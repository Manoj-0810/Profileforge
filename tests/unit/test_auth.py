"""Unit tests for API key verification."""

from __future__ import annotations

import pytest

from app.auth import verify_api_key
from app.config import settings
from app.errors import ErrorCode, ProfileForgeError


@pytest.mark.asyncio
async def test_valid_api_key():
    valid_key = settings.API_KEYS[0]
    result = await verify_api_key(x_api_key=valid_key)
    assert result == valid_key


@pytest.mark.asyncio
async def test_missing_api_key():
    with pytest.raises(ProfileForgeError) as exc_info:
        await verify_api_key(x_api_key=None)
    assert exc_info.value.error_code == ErrorCode.UNAUTHORIZED
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_invalid_api_key():
    with pytest.raises(ProfileForgeError) as exc_info:
        await verify_api_key(x_api_key="totally-wrong-key-abc")
    assert exc_info.value.error_code == ErrorCode.UNAUTHORIZED
    assert exc_info.value.status_code == 401
