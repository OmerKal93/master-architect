"""Regression test for independent-review finding: the async Anthropic transport used to be
unstubbed, reaching the real httpx async transport when `.ainvoke()` was used. Fixed by patching
AsyncMessages.create with a loud-failure guard. This test proves the guard fires BEFORE any real
network call, using pytest-asyncio's absence as a non-issue -- asyncio.run drives the coroutine
directly, no plugin needed.
"""

from __future__ import annotations

import asyncio

import pytest
from langchain_anthropic import ChatAnthropic

from agent_chaos.core.injector import ChaosInjector
from art_contracts.langgraph_adapter import AsyncPathNotStubbedError, patched_anthropic_with_chaos


def _sync_stub_should_never_be_called(self_msg, **kwargs):
    raise AssertionError("sync stub was called from an async path -- test setup is wrong")


def test_ainvoke_raises_loud_guard_instead_of_reaching_real_async_transport():
    injector = ChaosInjector(chaos=[])

    with patched_anthropic_with_chaos(injector, _sync_stub_should_never_be_called):
        model = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key="sk-ant-test-stub-no-real-key")

        async def _call():
            from langchain_core.messages import HumanMessage

            return await model.ainvoke([HumanMessage(content="hello")])

        with pytest.raises(AsyncPathNotStubbedError):
            asyncio.run(_call())
