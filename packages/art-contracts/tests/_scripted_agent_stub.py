"""Shared, deterministic Anthropic-transport stub modeling a naive agent that retries a
side-effecting tool call once, unconditionally, after seeing an error/timeout result -- the exact
retry-without-idempotency-awareness behavior real double-charge bugs come from. Identical script
for both the broken and fixed sample (the difference under test is entirely in the tool
implementation, not the agent's retry policy). Seeded/deterministic by construction: no real model
call, no randomness -- every run produces byte-identical request sequencing (AT2).
"""

from __future__ import annotations

from anthropic.types import Message as AnthropicMessage
from anthropic.types import TextBlock, ToolUseBlock, Usage


def make_naive_retry_stub(request_log: list[dict]):
    """Returns a stand-in for anthropic.resources.Messages.create. Script:
    call 1 -> tool_use(process_refund, req-1)
    call 2 -> (after seeing the tool_result, possibly mutated to a timeout by agent_chaos) ->
              tool_use(process_refund, req-1) AGAIN, unconditionally -- the naive retry.
    call 3 -> final text response, regardless of what the second tool_result says.
    """

    def _stub_messages_create(self_msg, **kwargs):
        request_log.append(kwargs)
        call_index = len(request_log)

        if call_index in (1, 2):
            return AnthropicMessage(
                id=f"msg_stub_{call_index}",
                type="message",
                role="assistant",
                model="claude-3-5-sonnet-20241022",
                content=[
                    ToolUseBlock(
                        type="tool_use",
                        id=f"toolu_stub_{call_index}",
                        name="process_refund",
                        input={"amount": 100.0, "request_id": "req-1"},
                    )
                ],
                stop_reason="tool_use",
                stop_sequence=None,
                usage=Usage(input_tokens=10, output_tokens=10),
            )

        return AnthropicMessage(
            id=f"msg_stub_{call_index}",
            type="message",
            role="assistant",
            model="claude-3-5-sonnet-20241022",
            content=[TextBlock(type="text", text="Done processing your refund request.")],
            stop_reason="end_turn",
            stop_sequence=None,
            usage=Usage(input_tokens=10, output_tokens=10),
        )

    return _stub_messages_create
