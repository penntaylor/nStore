class NstoreError(Exception):
    """Base exception for nStore
    """
    pass

class UnsupportedModeError(NstoreError):
    """Raised when attempting to access a file with an invalid mode.
    """
    def __init__(self, mode, allowed):
        self.mode = mode
        self.allowed = allowed

    def __str__(self):
        return f"Unsupported mode: {self.mode}; must be one of {self.allowed}"

class InvalidAccessError(NstoreError):
    """Raised when access to a file fails, including when trying to clean nStore's cache.
    """
    def __init__(self, path, msg):
        self.path = path
        self.msg = msg

    def __str__(self):
        return f"Cannot access {self.path}; details: {self.msg}"

class DeleteError(NstoreError):
    """Raised when a file deletion operation fails.
    """
    def __init__(self, path, msg):
        self.path = path
        self.msg = msg

    def __str__(self):
        return f"Error deleting {self.path}; details: {self.msg}"

class UnsupportedProtocolError(NstoreError):
    """Raised when attempting to operate on a file with an unkown protocol
    or whose protocol does not support that operation.
    """
    def __init__(self, protocol):
        self.protocol = protocol

    def __str__(self):
        return f"Unsupported protocol: {self.protocol}"
