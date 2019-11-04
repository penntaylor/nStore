from contextlib import contextmanager
import gzip
import mimetypes
import pathlib


@contextmanager
def crackOpen(path, mode="r", **args):
    """Context manager to handle opening plain files or gzipped files
       with minimal ceremony; use it as you would `open` with the caveat
       that read mode and write mode should be treated separately, and
       file seeking and truncating may not work.
       For gzipped files, text mode will be used unless binary mode
       is explicitly requested using the 'b' suffix to mode
    """
    p = pathlib.Path(path)
    _, encoding = mimetypes.guess_type(p.name)
    if encoding == "gzip":
        if not mode.endswith("b"):
            mode += "t"  # Force text mode if binary not requested
        with gzip.open(path, mode, **args) as f:
            yield f
    else:
        with open(path, mode, **args) as f:
            yield f
