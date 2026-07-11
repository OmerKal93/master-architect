# AR003 — Tool or external call without timeout

- **Severity:** high
- **Confidence:** high
- **Category:** timeouts
- **Framework:** generic (Python)

## What it means

This finding fires on a call site recognized as an external/tool call (an HTTP client method or
an LLM provider SDK method — see below for the exact allowlist) where no `timeout=` keyword
argument was found at the call site. See "Known limitation" below: a genuinely configured
client/session-level timeout is invisible to this rule and will still be reported.

## Why it matters

A call to an external service with no timeout can hang the calling process indefinitely if the
remote end never responds — a stalled connection, a slow upstream, or a network partition. In an
agent loop this blocks the whole run (or, if the loop itself is unbounded, combines with AR001
into a process that never returns and never stops accruing cost).

## What this rule looks for (and doesn't)

The frontend (`agent_reliability.lint.frontend.calls`) records **every** attribute-chain call
site (`obj.method(...)`) as a candidate `ToolCall` — it does not itself judge which of those are
"really" external calls. That classification is this rule's job, done with a conservative, named
allowlist rather than a blanket "any attribute call" match:

- **Recognized:** module-qualified HTTP client calls — `requests.get/post/put/patch/delete/head/
  options/request`, the same set for `httpx` (plus `httpx.stream`), and `urllib3.request` /
  `urllib3.urlopen`. Also recognized: call chains whose trailing dotted segments match a known
  OpenAI or Anthropic Python SDK method shape, e.g. `....chat.completions.create`,
  `....completions.create`, `....embeddings.create`, `....images.generate`, `....images.edit`,
  `....audio.transcriptions.create`, `....audio.translations.create`, `....audio.speech.create`,
  `....moderations.create`, `....responses.create`, `....messages.create`, `....messages.stream`.
- **Known, accepted collision risk: short (2-segment) SDK suffixes.** `....messages.create`
  (Anthropic's single most common call shape) and a few others above are only 2 dotted segments
  — indistinguishable, by trailing text alone, from unrelated application code sharing the same
  method name (a notification service's own `notification.messages.create(...)`, a forms app's
  `form.completions.create(...)`). This is a real, accepted trade-off, not an oversight: this
  rule's job is defined by CODEX_HANDOFF.md as recognizing OpenAI/Anthropic calls "already
  recognizable by the current frontend" — the frontend's textual callee already is
  `client.messages.create` for Anthropic's real shape, so excluding it to reduce false positives
  would silently under-deliver required scope. This is the identical class of trade-off AR001's
  own docs.md already accepts for its loop heuristic ("this rule will fire on non-agent code
  too... accepted trade-off, not a bug"), applied consistently here. Narrowing this list happened
  once during review and was reverted after a second review round found it dropped required
  scope — re-narrowing again needs a stronger disambiguation signal than trailing-text matching
  (e.g. import-aware typing), not just a lower false-positive count.
- **Not recognized (silence, not a guess):** any other attribute-chain call, including
  instance/session-based HTTP calls (`session.post(...)`, `client.get(...)`) where the variable's
  type can't be statically determined, and any other SDK/API shape not in the list above — for
  example a Stripe-like `client.payments.charges.create(...)` call is deliberately **not**
  flagged even with no timeout, because the frontend cannot tell that `client` is a payments SDK
  and not, say, a local wrapper object. Firing on unrecognized shapes would trade a real risk of
  false positives for marginal recall; this rule stays silent instead.
- A call **with** a `timeout=` keyword argument present and set to a literal number, or to a
  variable/config lookup whose value can't be statically read, never fires. A call to a
  **`requests`/`httpx` HTTP method** whose `timeout=` keyword is the literal `None` **does**
  fire — `timeout=None` disables the timeout entirely for those two libraries specifically
  (documented, verified behavior), so it is exactly as unbounded as an absent keyword, not a
  weaker-but-present bound. (An earlier version of this rule only checked keyword *presence* and
  incorrectly treated `timeout=None` as safe for HTTP calls; caught by independent review, fixed
  via `TimeoutPolicy.explicit_none`.) For **OpenAI/Anthropic SDK shapes**, `timeout=None` is
  treated the same as a non-literal timeout (never fires) — the "disables the timeout entirely"
  claim is verified for requests/httpx specifically and does not automatically extend to every
  other recognized callee; an earlier version of this rule applied it uniformly, which
  independent review correctly flagged as an unverified generalization (the same class of
  mistake as the `max_retries=None` claim below).
- Calls made through an imported-by-name callable (`from openai import chat; chat(...)`) are
  invisible to the frontend entirely (see `calls.py`'s own capability statement) and so never
  reach this rule — a known, documented limitation, not specific to AR003.

## Known limitation: client/session-level timeout configuration is not recognized (real false positives)

This is a materially significant gap, not a minor edge case, flagged during independent review
and deliberately not fixed in this PR because closing it properly is a much larger analyzer
capability than anything else here. Many real SDKs let you configure a timeout **once**, at
client construction, and have every subsequent call through that client inherit it:

```python
client = OpenAI(timeout=30)
client.chat.completions.create(model=model, messages=messages)  # actually has a real timeout
```

This rule has no way to see that: the IR (`ToolCall.timeout`) only ever reflects the `timeout=`
keyword at the call site itself, never a client/session's construction-time configuration.
Detecting the pattern above correctly would require tracking which variable a call is made on,
where that variable was constructed, and what it was constructed with — real inter-statement
data-flow/alias analysis, a capability this frontend does not have and which is out of proportion
to add as part of this rule (see the frontend's own module docstring: this analyzer is
deliberately parse-only with no cross-statement tracking). Until that capability exists, this
rule **will** false-positive on the exact pattern shown above — a known, real cost, not a
theoretical one. If this proves too noisy in practice, the corrective action is a follow-up PR
adding client-construction tracking to the frontend, not a change to this rule's own matching
logic.

## Remediation

Pass an explicit `timeout=` (seconds, or a library-specific timeout object) at each recognized
call site. Configuring a timeout once on the client/session **does** make the call genuinely
safe, but — per the limitation above — will not silence this specific finding until client-level
tracking exists; per-call `timeout=` is the only remediation this rule can currently verify.

```python
# Before
requests.post(url, json=payload)

# After
requests.post(url, json=payload, timeout=10)
```

```python
# Before
client.chat.completions.create(model=model, messages=messages)

# After
client.chat.completions.create(model=model, messages=messages, timeout=30)
```

## Suppressing this finding

Inline suppressions (`# art: ignore[AR003] reason="..."`) are not implemented yet — they land in
`EXECUTION.md` E07. Until then, the only way to silence a finding you've reviewed and accepted is
to add the `timeout=` keyword the rule is looking for.
