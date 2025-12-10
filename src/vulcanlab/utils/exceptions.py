"""Custom exceptions for vulcanlab utilities."""


class InvalidFilePathError(Exception):
    """Raised when a file path is NULL, empty, or invalid."""

    def __init__(self, message: str, work_id: int = None, field_name: str = None):
        self.work_id = work_id
        self.field_name = field_name
        super().__init__(message)
