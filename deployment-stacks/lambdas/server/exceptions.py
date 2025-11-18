"""Custom exceptions for the API module."""


class InvalidRuntimeError(Exception):
    """Raised when an invalid agent runtime is specified."""


class AgentInvocationError(Exception):
    """Raised when there is an error invoking the agent runtime."""


class UnexpectedAgentResponseError(Exception):
    """Raised when the agent runtime returns an unexpected response."""
