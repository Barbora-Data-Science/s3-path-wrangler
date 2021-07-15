[![Formatter](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Build Status](https://github.com/Barbora-Data-Science/s3-path-wrangler/actions/workflows/main.yml/badge.svg)](https://github.com/Barbora-Data-Science/s3-path-wrangler/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/Barbora-Data-Science/s3-path-wrangler/branch/main/graph/badge.svg?token=MJSSVCSFJV)](https://codecov.io/gh/Barbora-Data-Science/s3-path-wrangler)
[![PyPI version](https://badge.fury.io/py/s3-path-wrangler.svg)](https://pypi.org/project/s3-path-wrangler/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/s3-path-wrangler)](https://pypi.org/project/s3-path-wrangler/)


# Description
Provides S3 path manipulation, similar to PurePath in pathlib. 
S3Path is _only_ meant for path manipulation and does not implement any methods which interact with S3 itself.
Avoiding S3 interaction means that a user can use their own boto3 session and are not forced to use the default one.

For S3Path implementations that do path manipulation _and_ interaction, see 
[s3path](https://github.com/liormizr/s3path) instead.

# Installation

This is a pure python package, so it can be installed with `pip install s3-path-wrangler` 
or any other dependency manager.

# Usage

This library provides a single (meant to be) immutable class - `S3Path`.
Class features:

```python
from s3_path_wrangler.paths import S3Path

# various options for creating path objects
full_path = S3Path("s3://your-bucket/some/path/file.json")
from_list = S3Path.from_parts(["your-bucket", "some", "path", "file.json"], is_absolute=True)
relative = S3Path("some/path/")
relative_from_list = S3Path.from_parts(["some", "path"]) # or is_absolute=False

# convenient attributes
assert full_path.parts == ["your-bucket", "some", "path", "file.json"]
assert full_path.is_absolute == True
assert full_path.bucket == "your-bucket"
assert full_path.key == "some/path/file.json"
assert full_path.name == "file.json"
assert full_path.parent == S3Path("s3://your-bucket/some/path")

# paths are comparable to strings (directories will not have trailing slashes)
assert S3Path.from_parts(["some", "path"]) == "some/path"

# paths can be manipulated via '/'
assert relative / "file.json" == S3Path("some/path/file.json")
```

# Development

This library uses the [poetry](https://python-poetry.org/) package manager, which has to be installed before installing
other dependencies. Afterwards, run `poetry install` to create a virtualenv and install all dependencies.

[Black](https://github.com/psf/black) is used (and enforced via workflows) to format all code. Poetry will install it
automatically, but running it is up to the user. To format the entire project, run `black .`.

To run tests, either activate the virtualenv via `poetry shell` and run `pytest ./tests`,
or simply run `poetry run pytest ./tests`.

# Contributing

This project uses the Apache 2.0 license and is maintained by the data science team @ Barbora. All contribution are 
welcome in the form of PRs or raised issues.
