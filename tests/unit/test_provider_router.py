import pytest
from unittest.mock import AsyncMock
from backend.app.ai.provider_router import ProviderRouter, ProviderError
from backend.app.ai.providers.base import BaseLLMProvider

class FakeProvider(BaseLLMProvider):
    def __init__(self, name, available=True, should_fail=False):
        self.name = name
        self.is_available = available
        self.should_fail = should_fail

    async def generate_response(self, messages, **kwargs):
        if self.should_fail:
            raise ProviderError("fail")
        return f"response from {self.name}"

    async def generate_stream(self, messages, **kwargs):
        if self.should_fail:
            raise ProviderError("fail")
        async def _stream():
            yield f"chunk from {self.name}"
        return _stream()

@pytest.fixture
def providers():
    return [
        FakeProvider("A", available=True),
        FakeProvider("B", available=True),
    ]

@pytest.mark.asyncio
async def test_router_uses_first_available(providers):
    router = ProviderRouter(providers)
    resp = await router.generate_response([{"role": "user", "content": "test"}])
    assert "response from A" in resp

@pytest.mark.asyncio
async def test_router_fallsback_on_error(providers):
    providers[0].should_fail = True
    router = ProviderRouter(providers)
    resp = await router.generate_response([{"role": "user", "content": "test"}])
    assert "response from B" in resp

@pytest.mark.asyncio
async def test_router_skips_unavailable(providers):
    providers[0].is_available = False
    router = ProviderRouter(providers)
    resp = await router.generate_response([{"role": "user", "content": "test"}])
    assert "response from B" in resp