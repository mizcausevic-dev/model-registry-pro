"""Registry-specific exceptions."""


class ModelNotFound(Exception):
    """Raised when looking up a model that isn't registered."""


class DuplicateModel(Exception):
    """Raised when registering a (name, version) that already exists."""


class InvalidTransition(Exception):
    """Raised when a stage transition is not allowed."""


class ApprovalNotFound(Exception):
    """Raised when looking up an approval id that doesn't exist."""


class PolicyDenied(Exception):
    """Raised when a promotion policy rejects a request."""
