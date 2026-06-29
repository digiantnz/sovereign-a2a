"""A2A JSON-RPC 3.0 message primitives.

Three classes — agents only need to know these:

  A2AMessage     — static factory methods: request(), success(), error(), partial()
  A2AErrorCodes  — named error code constants
  A2AResponse    — thin parser for incoming responses; never throws on malformed input

Wire format (sovereign-core → agent):
  {
    "jsonrpc": "3.0",
    "id":      "<request_id>",
    "method":  "<skill>/<operation>",
    "params":  {"skill": "...", "operation": "...", "payload": {}},
    "metadata": {
      "priority": "normal|high",
      "stream":   false,
      "capabilities": [],
      "context_hints": {"tier": "LOW|MID|HIGH", "retry_strategy": "none|correct_payload"}
    }
  }

Wire format (agent → sovereign-core, success):
  {
    "jsonrpc": "3.0",
    "id":      "<request_id>",
    "result":  {"success": true, "status_code": "HTTP 201|IMAP OK|...", "data": {}},
    "metadata": {
      "agent_card":    {"name": "...", "skills": [...], "capabilities": [...], "trust_level": "..."},
      "context_hints": {"execution_path": "dsl|llm", "protocol_quirks": null, "raw_error": null}
    }
  }

Wire format (agent → sovereign-core, error):
  {
    "jsonrpc": "3.0",
    "id":      "<request_id>",
    "error":   {"code": -32000, "message": "verbatim error", "data": {"skill": "...", "operation": "..."}},
    "metadata": {"context_hints": {"execution_path": "dsl|llm", "suggested_retry": null}}
  }

Backward compatibility: agents accept legacy flat dicts (no "jsonrpc" key).
A2AResponse.is_a2a() distinguishes the two formats.
"""
from __future__ import annotations

from typing import Any


class A2AErrorCodes:
    """Standard A2A error codes.

    -32700 to -32600 are reserved by JSON-RPC spec.
    -32000 to -32099 are available for implementation-defined server errors.
    """
    PARSE_ERROR          = -32700   # Malformed JSON received
    INVALID_REQUEST      = -32600   # Not a valid A2A request object
    METHOD_NOT_FOUND     = -32601   # skill/operation not in DSL or registry
    INVALID_PARAMS       = -32602   # Validation failure; include field errors in data
    SERVER_ERROR         = -32000   # General execution failure
    TIMEOUT              = -32001   # Execution exceeded timeout_ms
    SKILL_NOT_LOADED     = -32002   # Skill exists in registry but not currently loaded
    ADAPTER_UNAVAILABLE  = -32003   # Underlying adapter not reachable


class A2AMessage:
    """Static factory methods for constructing A2A 3.0 response envelopes."""

    JSONRPC: str = "3.0"

    @classmethod
    def success(
        cls,
        id: str,
        result: dict[str, Any],
        hints: dict[str, Any] | None = None,
        agent_card: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Construct a success response.

        Args:
            id:         request_id echoed from the request
            result:     {"success": bool, "status_code": str, "data": dict}
            hints:      context_hints to include in metadata (execution_path, protocol_quirks, etc.)
            agent_card: agent's current capability advertisement (included on success responses)
        """
        meta: dict[str, Any] = {"context_hints": hints or {}}
        if agent_card:
            meta["agent_card"] = agent_card
        return {
            "jsonrpc":  cls.JSONRPC,
            "id":       id,
            "result":   result,
            "metadata": meta,
        }

    @classmethod
    def error(
        cls,
        id: str,
        code: int,
        message: str,
        data: dict[str, Any] | None = None,
        hints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Construct an error response.

        Args:
            id:      request_id echoed from the request
            code:    A2AErrorCodes constant
            message: verbatim protocol error string — never sanitised or interpreted
            data:    optional supplemental data (skill, operation, status_code, field errors)
            hints:   context_hints for the metadata block
        """
        return {
            "jsonrpc": cls.JSONRPC,
            "id":      id,
            "error": {
                "code":    code,
                "message": message,
                "data":    data or {},
            },
            "metadata": {"context_hints": hints or {}},
        }



class A2AResponse:
    """Thin parser for incoming A2A 3.0 responses.

    Never throws on malformed input — returns None for missing fields.
    Handles both A2A 3.0 format (has "jsonrpc" key) and legacy flat dicts.

    Usage:
      if A2AResponse.is_success(body):
          data = A2AResponse.get_result(body)
          hints = A2AResponse.get_hints(body)
      elif A2AResponse.is_error(body):
          err = A2AResponse.get_error(body)
          code = err.get("code")
    """

    @staticmethod
    def is_a2a(response: dict) -> bool:
        """True if this looks like an A2A 3.0 message (has jsonrpc: "3.0")."""
        return response.get("jsonrpc") == "3.0"

    @staticmethod
    def is_success(response: dict) -> bool:
        """True if the response carries a result (not an error)."""
        return "result" in response and "error" not in response

    @staticmethod
    def is_error(response: dict) -> bool:
        """True if the response carries an error object."""
        return "error" in response

    @staticmethod
    def get_result(response: dict) -> dict[str, Any] | None:
        """Return the result object, or None if absent."""
        return response.get("result")

    @staticmethod
    def get_error(response: dict) -> dict[str, Any] | None:
        """Return the error object {code, message, data}, or None if absent."""
        return response.get("error")

    @staticmethod
    def get_hints(response: dict) -> dict[str, Any]:
        """Return context_hints from metadata. Always a dict, never None."""
        return response.get("metadata", {}).get("context_hints") or {}

    @staticmethod
    def get_agent_card(response: dict) -> dict[str, Any] | None:
        """Return agent_card from metadata, or None if absent."""
        return response.get("metadata", {}).get("agent_card")

    @staticmethod
    def get_id(response: dict) -> str | None:
        """Return the response id (echoed request_id)."""
        return response.get("id")
