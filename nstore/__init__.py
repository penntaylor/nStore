from contextlib import contextmanager
import hashlib
import logging
import pathlib
import shutil
import tempfile

import boto3

# FIXME: Not handling compression yet

READMODES = ["r", "rb", "rt"]
WRITEMODES = ["w", "wb", "wt"]
APPENDMODES = ["a", "ab", "at"]

cacheDir = tempfile.TemporaryDirectory(prefix="nstore.")

@contextmanager
def access(path, mode="r", usecache=False, **args):
    """Opens local as well as remote files using a common interface. Read mode
       and write mode are mutually exclusive.

       To read and write to the same file, it is necessary to *access*
       it twice: once in read mode, close it, then open it back up in write
       mode. While slightly inconvenient for some uses, this greatly
       simplifies the logic (and bug surface) involved in keeping local and
       remote files syncronized.
    """
    supportedmodes = READMODES + WRITEMODES + APPENDMODES
    if mode not in supportedmodes:
        raise RuntimeError("Unsupported mode: {}; must be one of {}".
                               format(mode, supportedmodes))
    localpath, isCached = _localize(path, usecache, mode)

    # Hashing is wasted effort for readonly modes
    if isCached and mode in (WRITEMODES + APPENDMODES):
        hashbefore = _hashFile(localpath)

    with open(localpath, mode, **args) as f:
        yield f
    # Send file back to source if we altered it
    if isCached and (mode in WRITEMODES + APPENDMODES):
        hashafter = _hashFile(localpath)
        if hashafter != hashbefore:
            copy(localpath, path)
    if isCached and not usecache:
        clean(localpath)


def copy(srcpath, dstpath):
    """Copy a file from srcpath to dstpath, where either (or both) path may refer to
       a remote file.
    """
    srcprotocol, srcfpath = _decompose(srcpath)
    dstprotocol, dstfpath = _decompose(dstpath)

    if _isDupe(srcprotocol, srcfpath, dstprotocol, dstfpath):
        return None

    # When src is local, we just do whatever copy op is requested directly.
    # For all other src cases, we pull file down into a temporary local
    # file, then make a second copy operation to send it to dst.
    #
    # To add a new protocol handler, add a dstprotocol case in the first block
    # below, and a separate srcprotocol case in the following block.
    # This might benefit from being refactored into some sort of plugin architecture
    # eventually. Might be possible to handle things like S3 -> S3 without requiring
    # a local temporary.
    if srcprotocol == "file":
        if dstprotocol == "file":
            pathlib.Path(dstfpath).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(srcfpath, dstfpath)
        elif dstprotocol == "s3":
            bucket, key = _decomposeS3(dstfpath)
            s3 = boto3.resource("s3")
            s3.Object(bucket, key).upload_file(srcfpath)
    else:
        if dstfpath.startswith(cacheDir.name):
            tmpdstfpath = pathlib.Path(dstfpath)
        else:
            tmpdstfpath = pathlib.Path(cacheDir.name, dstfpath)
        tmpdstfpath.parent.mkdir(parents=True, exist_ok=True)

        if srcprotocol == "s3":
            bucket, key = _decomposeS3(srcfpath)
            s3 = boto3.resource("s3")
            s3.Object(bucket, key).download_file(str(tmpdstfpath))
            copy(tmpdstfpath, dstpath)
            if str(tmpdstfpath) != str(dstfpath):
                clean(tmpdstfpath)
        else:
            raise RuntimeError("Unsupported protocol: {}".format(dstprotocol))


def clean(path="*"):
    """Remove cached files matching globbing pattern in *path*.

       WARNING:
       This method tries to detect (and deny) attempts to remove files
       outside the cache, but it may not catch very carefully constructed
       glob patterns. Under no circumstance should unverified input from a
       user be passed directly to this method!
    """
    # Handle "correct" patterns as well as paths containing a protocol
    _, patt = _decompose(path)

    # Insert cachedir at head if it isn't there:
    if not patt.startswith(cacheDir.name):
        patt = pathlib.Path(cacheDir.name, patt)

    # Attempt to ensure we're really in the cachedir
    patt = pathlib.Path(patt).resolve()
    if not str(patt).startswith(cacheDir.name):
        raise RuntimeError("Attempted to clean file(s) outside of nStore's cache!")

    # Get pattern relative to cachedir so globbing will work
    patt = pathlib.Path(patt).relative_to(cacheDir.name)

    for f in pathlib.Path(cacheDir.name).glob(str(patt)):
        if f.is_file():
            f.unlink()
        elif f.is_dir():
            shutil.rmtree(f, ignore_errors=True)
        else:
            continue # symlinks can get us here, not sure what else


def delete(path):
    """Attempt to delete the canonical source file.
    """
    pass


# pathlike -> bool -> str -> (Path, bool)
def _localize(path, usecache, mode):
    # Remote files are added to a local cache. Already-local files are simply
    # handed back.
    # Returns a tuple containing
    # (path to the localized file, bool indicating whether file was placed in cache)
    protocol, fpath = _decompose(str(path))

    # Do not cache files that are already local
    if protocol == "file":
        return (pathlib.Path(fpath).resolve(), False)

    cachedpath = pathlib.Path(cacheDir.name, fpath)

    if (mode not in WRITEMODES) and not (usecache and cachedpath.exists()):
        copy(path, cachedpath)

    return (cachedpath, True)


def _isDupe(srcprotocol, srcfpath, dstprotocol, dstfpath):
    if (srcprotocol == dstprotocol) and (srcfpath == dstfpath):
        return True

    # Special handling for file protocol since there are multiple valid
    # ways to refer to the same file on disk
    if srcprotocol == dstprotocol == "file":
        sp = pathlib.Path(srcfpath).resolve()
        dp = pathlib.Path(dstfpath).resolve()
        if sp == dp:
            return None

    return False


def _decompose(path):
    # Decompose path into a protocol and an actual Path.
    # Paths are assumed to be in one of the following forms:
    # "a/local/file"
    # "protocol://a/remote/file"
    parts = str(path).split("://")
    if len(parts) == 1:
        parts.insert(0, "file")
    # normalize all protocols to lowercase to simplify selection
    parts[0] = parts[0].lower()
    return parts


def _decomposeS3(path):
    # Ensures we handle both "bucket/key" and "s3://bucket/key" variants
    _, paff = _decompose(path)
    parts = paff.split('/')
    bucket = parts[0]
    key = '/'.join(parts[1:])
    return (bucket, key)


# Using a modified version from SO to get the block iteration right:
# https://stackoverflow.com/a/44873382
# Hashing is expensive, but it is less expensive than unnecessary network traffic
# involving potentially large files.
def _hashFile(path):
    h = hashlib.sha256()
    try:
        with open(path, 'rb', buffering=0) as f:
            for b in iter(lambda : f.read(128*1024), b''):
                h.update(b)
    except FileNotFoundError:
        return "0"

    return h.hexdigest()
