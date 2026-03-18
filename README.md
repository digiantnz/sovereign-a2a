# sovereign-a2a

Lightweight A2A JSON-RPC 3.0 message primitives for Sovereign AI agent communications.

Single source of truth for the A2A 3.0 wire format across sovereign-core, nanobot-01, a2a-browser, and any future agent in the Sovereign ecosystem.

**No external dependencies — stdlib only.**

## Install

```bash
pip install git+https://github.com/digiantnz/sovereign-a2a.git
```

## Usage

```python
from sovereign_a2a import A2AMessage, A2AErrorCodes, A2AResponse

# Build a request (sender side)
msg = A2AMessage.request(
    method="imap-smtp-email/check_unread",
    params={"skill": "imap-smtp-email", "operation": "check_unread", "payload": {"account": "business"}},
    id="req-abc123",
    metadata={"context_hints": {"tier": "MID", "retry_strategy": "correct_payload"}},
)

# Build a success response (responder side)
response = A2AMessage.success(
    id="req-abc123",
    result={"success": True, "status_code": "IMAP OK", "data": {"messages": [...]}},
    hints={"execution_path": "dsl"},
    agent_card={"name": "nanobot-01", "skills": ["imap-smtp-email"], "trust_level": "internal_sidecar"},
)

# Build an error response (responder side)
response = A2AMessage.error(
    id="req-abc123",
    code=A2AErrorCodes.ADAPTER_UNAVAILABLE,
    message="IMAP connection refused",
    data={"skill": "imap-smtp-email", "operation": "check_unread"},
)

# Parse an incoming response (receiver side)
if A2AResponse.is_success(body):
    data = A2AResponse.get_result(body)
    hints = A2AResponse.get_hints(body)
    card = A2AResponse.get_agent_card(body)
elif A2AResponse.is_error(body):
    err = A2AResponse.get_error(body)
    code = err.get("code")   # A2AErrorCodes constant
    message = err.get("message")
```

## Error codes

| Constant | Code | Meaning |
|----------|------|---------|
| `PARSE_ERROR` | -32700 | Malformed JSON |
| `INVALID_REQUEST` | -32600 | Not a valid A2A request |
| `METHOD_NOT_FOUND` | -32601 | skill/operation not in DSL or registry |
| `INVALID_PARAMS` | -32602 | Validation failure |
| `SERVER_ERROR` | -32000 | General execution failure |
| `TIMEOUT` | -32001 | Execution exceeded timeout_ms |
| `SKILL_NOT_LOADED` | -32002 | Skill exists but not currently loaded |
| `ADAPTER_UNAVAILABLE` | -32003 | Underlying adapter not reachable |

## Backward compatibility

`A2AResponse.is_a2a(body)` returns `True` when the response has `"jsonrpc": "3.0"`.
Agents that need to handle legacy flat dicts alongside A2A 3.0 can branch on this.

## Version

A2A 3.0 is backward compatible with 2.0 clients — they will continue to work.
