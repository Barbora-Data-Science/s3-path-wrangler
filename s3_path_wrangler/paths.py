import logging
import re
from typing import Iterable, List, Optional, Union

LOGGER = logging.getLogger(__name__)

DNS_NAME_REGEX = r"(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)"
S3_PATH_REGEX = r"^s3:\/\/(" + DNS_NAME_REGEX + r")\/(.+)$"


class InvalidPathError(ValueError):
    pass


class UnknownBucketError(ValueError):
    pass


class InvalidBucketError(ValueError):
    pass


class S3Path:
    _PREFIX = "s3://"

    def __init__(self, path: str):
        """Parses a string representation of an S3 path.

        Absolute paths should be specified with the prefix (s3://bucket-name/some/path/to/file.txt).
        Relative paths should not have a trailing slash (some/path/to/file.txt).
        Both kinds of paths can also refer to folders instead of files.
        They can be specified with with a trailing slash or without.

        Args:
            path: String representation of a relative or absolute S3 path.

        Raises:
            InvalidPathError: When the passed string is not a valid S3 path.
            InvalidBucketError: When the bucket of the absolute path does not have a valid name.
                https://docs.aws.amazon.com/AmazonS3/latest/dev/BucketRestrictions.html#bucketnamingrules
        """
        if path.startswith("/"):
            raise InvalidPathError(
                f"Path ({path}) cannot start with a slash. "
                f"If an absolute path is required, use the S3 prefix - 's3://bucket/...'"
            )
        if path.startswith(self._PREFIX):
            self._is_absolute = True
            path = path.lstrip(self._PREFIX)
        else:
            self._is_absolute = False
        parts = path.strip("/").split("/")
        S3Path._validate_parts(parts)
        if self._is_absolute:
            S3Path._validate_bucket(parts[0])
        self._parts = parts

    @classmethod
    def from_parts(cls, parts: Iterable[str], is_absolute: bool = False) -> "S3Path":
        """Constructs an S3 path from a collection of path parts.

        Args:
            parts: An ordered collection containing the path parts. These parts should not contain slashes.
            is_absolute: Whether to treat the first part as the S3 bucket and construct an absolute path.

        Returns:
            An S3 path representation similar to `pathlib.Path`.
        """
        part_list = list(parts)
        S3Path._validate_parts(part_list)
        path = ""
        if is_absolute:
            S3Path._validate_bucket(part_list[0])
            path = S3Path._PREFIX
        path = path + "/".join(part_list)
        return S3Path(path)

    @classmethod
    def _is_valid_part(cls, part: str) -> bool:
        """Checks if a single part of a path is valid.

        Args:
            part: Path part to check.

        Returns:
            True if the part is valid, False otherwise.
        """
        return bool(part) and not part.isspace() and "/" not in part

    @classmethod
    def _validate_parts(cls, parts: Iterable[str]) -> None:
        """Raises an exception if there are invalid parts.

        Args:
            parts: A collection of parts to check.
        """
        if not parts or any(not S3Path._is_valid_part(part) for part in parts):
            raise InvalidPathError(f"Some S3 path parts from {parts} are not valid")

    @classmethod
    def _validate_bucket(cls, bucket: str) -> None:
        """Raises an exception if the bucket name is invalid.

        Args:
            bucket: Name of the S3 bucket to validate.

        See Also:
            https://docs.aws.amazon.com/AmazonS3/latest/dev/BucketRestrictions.html#bucketnamingrules
        """
        if not re.fullmatch(DNS_NAME_REGEX, bucket):
            raise InvalidBucketError(f"{bucket} is not a valid bucket name")

    @property
    def parts(self) -> List[str]:
        """The parsed parts of the path.

        Returns:
            A list of path segments.
        """
        return self._parts

    @property
    def is_absolute(self) -> bool:
        """Is this an absolute path?

        Returns:
            True if the path is absolute, False otherwise.
        """
        return self._is_absolute

    def to_absolute(self) -> "S3Path":
        """Converts the path to an absolute one, assuming that the first part is the bucket.

        Does nothing is the path is already absolute.

        Returns:
            An S3Path instance which is absolute.
        """
        if self.is_absolute:
            return self
        return S3Path.from_parts(self.parts, is_absolute=True)

    def with_bucket(self, bucket: str) -> "S3Path":
        """Changes the bucket of the path.

        Note that since relative paths do not know anything about their bucket, this will set it for them,
            assuming that the relative path is from that bucket onwards. This means that this function will
            effectively convert the relative path to an absolute one.

        Args:
            bucket: Name of the S3 bucket.

        Returns:
            An absolute path with the bucket set.
        """
        stripped_bucket = bucket.strip("/")
        S3Path._validate_bucket(stripped_bucket)

        new_parts = self.parts.copy()
        if self.is_absolute:
            new_parts[0] = bucket
        else:
            new_parts.insert(0, stripped_bucket)
        return S3Path.from_parts(new_parts, is_absolute=True)

    @property
    def bucket(self) -> str:
        """The S3 bucket this path is in.

        Raises:
            UnknownBucketError: If this path is relative - such S3 paths are not bucket-aware.

        Returns:
            The name of the bucket the path resides in.
        """
        if not self.is_absolute:
            raise UnknownBucketError("Cannot compute the bucket of a relative path")
        return self.parts[0]

    @property
    def key(self) -> str:
        """The S3 key of this path.

        Raises:
            UnknownBucketError: If this path is relative. Since we don't know if a relative path starts from the
                bucket, we cannot be certain of what it's key is.

        Returns:
            The key of the S3 folder or file this path is referring to.
        """
        if self.is_absolute:
            return "/".join(self.parts[1:])
        raise UnknownBucketError(
            "Cannot compute the key, bucket of a relative path is not defined"
        )

    @property
    def name(self) -> str:
        """The name of the folder or file.

        Returns:
            The name (final segment) of the folder or file this path is referring to.
        """
        return self.parts[-1]

    @property
    def parent(self) -> Optional["S3Path"]:
        """The parent folder or bucket of this path.

        Returns:
            The path to the bucket if this path is directly within the bucket, the path of the parent folder if this
                path is deeper inside a bucket, or None if this path is referring to a bucket.
        """
        if len(self.parts) == 1:
            return None
        return S3Path.from_parts(self.parts[:-1], self.is_absolute)

    def __truediv__(self, other: Union[str, "S3Path"]):
        """Appends a path or path segment to this path.

        Args:
            other: Path to append.

        Returns:
            A new S3Path instance referring to the combined location.
        """
        if isinstance(other, str):
            path_str = other.lstrip("/")
            other_path = S3Path(path_str)
        elif other.is_absolute:
            raise ValueError(f"Cannot add an absolute path {other} to another path")
        else:
            other_path = other
        combined_parts = self.parts + other_path.parts
        return S3Path.from_parts(combined_parts, self.is_absolute)

    def __repr__(self) -> str:
        """Calculates the path's string representation.

        This will never create trailing slashes, which can be useful when comparing to strings.

        Returns:
            String representation of the path.
        """
        relative_representation = "/".join(self.parts)
        if self.is_absolute:
            return self._PREFIX + relative_representation
        return relative_representation

    def __eq__(self, other: Union[str, "S3Path"]) -> bool:
        """Checks if this is the same path as another one.

        Args:
            other: Other path (can be a string representation).

        Returns:
            True if both paths refer to the same location, False otherwise.
        """
        other_path = S3Path(other) if isinstance(other, str) else other
        return (
            self.parts == other_path.parts
            and self.is_absolute == other_path.is_absolute
        )
