# nStore

Treat files in python as files, no matter where they are.

Supports
* local files
* AWS S3.

Future support intended for:
* Google Cloud Storage
* Azure Blob Storage
* ftp
* http/s (read-only)

## Examples

```python
import nstore

with nstore.access("s3://my-bucket/some/file/far/away.txt", "r") as f:
    print(f.read())
```
will print the contents of `away.txt` as if it were a local file

---

Writing to files works too:
```python
with nstore.access("s3://my-bucket/another/file.txt", "w") as f:
    f.write("Some text in the file!")

with nstore.access("s3://my-bucket/another.file.txt", "r") as f:
    print(f.read())
```
will print
```
Some text in the file!
```

---

Files don't have to be remote:
```python
with nstore.access("rel/path/to/foo.json", "r") as f:
    print(f.read())
```
works exactly as though `nstore.access` were replaced by `open`. Specifying the protocol uri-style also works:

```python
with nstore.access("file://rel/path/to/foo.json", "r") as f:
    print(f.read())
```

---

Have a workflow in which files are repeatedly opened and closed for reading? Tell nStore it's OK to keep the file in the cache to prevent downloading it before each access:
```python
fname = "s3://my-bucket/bigfile.jpg"

with nstore.access(fname, "rb", usecache=True) as f:
    ... do some read operations ...

...


with nstore.access(fname, "rb", usecache=True) as f:
    ... do some more read operations using the cached version ...

# Let the cache know you're done with it now:
nstore.clean(fname)
```
