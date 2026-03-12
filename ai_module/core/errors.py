class AIModuleError(Exception):
    """Base exception for the AI module."""


class ValidationError(AIModuleError):
    """Raised when incoming domain data is invalid."""


class ProviderError(AIModuleError):
    """Raised when an external provider interaction fails."""


class SuggestionBuildError(AIModuleError):
    """Raised when suggestions cannot be constructed from analysis output."""

