from typing import List

class NstoreError(Exception):
    """Base exception for nStore
    """
    pass

class UnsupportedModeError(NstoreError):
    """Raised when attempting to access a file with an invalid mode.
    """
    def __init__(self, mode: str, allowed: List[str]):
        self.mode = mode
        self.allowed = allowed

    def __str__(self) -> str:
        return f"Unsupported mode: {self.mode}; must be one of {self.allowed}"

class InvalidAccessError(NstoreError):
    """Raised when access to a file fails, including when trying to clean nStore's cache.
    """
    def __init__(self, path: str, msg: str) -> None:
        self.path = path
        self.msg = msg

    def __str__(self) -> str:
        return f"Cannot access {self.path}; details: {self.msg}"

class DeleteError(NstoreError):
    """Raised when a file deletion operation fails.
    """
    def __init__(self, path: str, msg: str) -> None:
        self.path = path
        self.msg = msg

    def __str__(self) -> str:
        return f"Error deleting {self.path}; details: {self.msg}"

class UnsupportedProtocolError(NstoreError):
    """Raised when attempting to operate on a file with an unkown protocol
    or whose protocol does not support that operation.
    """
    def __init__(self, protocol: str) -> None:
        self.protocol = protocol

    def __str__(self) -> str:
        return f"Unsupported protocol: {self.protocol}"

class S3Error(NstoreError):
    """Raised when the S3 client encounters an error
    """
    def __init__(self, path: str, msg: str) -> None:
        self.path = path
        self.msg = msg

    def __str__(self) -> str:
        return f"{self.path}: {self.msg}"
