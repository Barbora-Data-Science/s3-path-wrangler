import pytest

from s3_path_wrangler.paths import (
    InvalidBucketError,
    InvalidPathError,
    S3Path,
    UnknownBucketError,
)

RELATIVE_PATH = S3Path("some/relative/path")
ABSOLUTE_PATH = S3Path("s3://bucket/some/relative/path/file.txt")


@pytest.mark.parametrize(
    "path_parts,expected_path",
    [
        pytest.param(["folder"], "folder", id="only_folder"),
        pytest.param(["file.txt"], "file.txt", id="only_file"),
        pytest.param(["folder", "file.txt"], "folder/file.txt", id="folder_and_file"),
    ],
)
def test_when_s3_path_is_constructed_from_parts_then_relative_path_is_calculated_properly(
    path_parts, expected_path
):
    assert S3Path.from_parts(path_parts) == expected_path


@pytest.mark.parametrize(
    "path_parts,expected_path",
    [
        pytest.param(["bucket"], "s3://bucket", id="only_folder"),
        pytest.param(
            ["bucket", "file.txt"], "s3://bucket/file.txt", id="folder_and_file"
        ),
    ],
)
def test_when_s3_path_is_constructed_from_parts_then_absolute_path_is_calculated_properly(
    path_parts, expected_path
):
    assert S3Path.from_parts(path_parts, is_absolute=True) == expected_path


@pytest.mark.parametrize(
    "input_parts,expected_parts",
    [
        pytest.param(["folder"], ["folder"], id="only_folder"),
        pytest.param(["file.txt"], ["file.txt"], id="only_file"),
        pytest.param(
            ["folder", "file.txt"], ["folder", "file.txt"], id="folder_and_file"
        ),
    ],
)
def test_when_s3_path_is_constructed_from_parts_then_the_resulting_parts_are_the_same(
    input_parts, expected_parts
):
    assert S3Path.from_parts(input_parts).parts == expected_parts


@pytest.mark.parametrize(
    "input_parts",
    [
        pytest.param([""], id="empty"),
        pytest.param(["/"], id="slash"),
        pytest.param(["///"], id="multiple_slashes"),
        pytest.param([" "], id="whitespace"),
        pytest.param(["folder", ""], id="some_invalid"),
        pytest.param(["folder/"], id="with_trailing_slash"),
        pytest.param(["/folder"], id="with_prefix_slash"),
    ],
)
def test_when_s3_path_is_constructed_with_invalid_parts_then_validation_error_is_raised(
    input_parts,
):
    with pytest.raises(InvalidPathError):
        S3Path.from_parts(input_parts)


@pytest.mark.parametrize(
    "input_str,expected_parts",
    [
        pytest.param("s3://bucket", ["bucket"], id="bucket"),
        pytest.param("s3://bucket/", ["bucket"], id="bucket_with_trailing_slash"),
        pytest.param(
            "s3://bucket/file.txt", ["bucket", "file.txt"], id="bucket_with_file"
        ),
        pytest.param(
            "s3://bucket/folder", ["bucket", "folder"], id="bucket_with_folder"
        ),
        pytest.param(
            "s3://bucket/folder/",
            ["bucket", "folder"],
            id="bucket_with_folder_with_trailing_slash",
        ),
        pytest.param(
            "s3://bucket/folder/file.txt",
            ["bucket", "folder", "file.txt"],
            id="bucket_with_folder_with_file",
        ),
        pytest.param("folder", ["folder"], id="relative_folder"),
        pytest.param("folder/", ["folder"], id="relative_folder_with_trailing_slash"),
        pytest.param(
            "folder/file.txt", ["folder", "file.txt"], id="relative_folder_with_file"
        ),
    ],
)
def test_when_s3_path_is_created_from_path_then_parts_are_parsed_correctly(
    input_str, expected_parts
):
    assert S3Path(input_str).parts == expected_parts


@pytest.mark.parametrize(
    "input_str",
    [
        pytest.param(
            "s3://bucket^with_invalid*name/folder/file.txt", id="invalid_bucket"
        ),
        pytest.param("/folder/file.txt", id="relative_path_but_prefixed_with_slash"),
        pytest.param("s3://bucket/ /file.txt", id="folder_name_is_empty"),
    ],
)
def test_when_s3_path_is_created_from_invalid_path_then_validation_error_is_raised(
    input_str,
):
    with pytest.raises(ValueError):
        S3Path(input_str)


def test_when_s3_path_is_constructed_from_parts_then_it_is_relative():
    assert not RELATIVE_PATH.is_absolute


def test_when_s3_path_is_constructed_from_full_path_then_it_is_absolute():
    assert ABSOLUTE_PATH.is_absolute


def test_when_relative_path_has_multiple_parts_then_it_can_be_converted_to_absolute():
    assert RELATIVE_PATH.to_absolute().is_absolute


def test_when_first_part_of_relative_path_cannot_be_a_bucket_then_converting_to_absolute_raises_error():
    with pytest.raises(InvalidBucketError):
        S3Path("file.txt").to_absolute()


def test_when_absolute_path_is_converted_to_absolute_then_the_same_path_is_returned():
    assert ABSOLUTE_PATH.to_absolute() == ABSOLUTE_PATH


def test_when_a_valid_bucket_is_added_to_a_relative_path_then_it_is_prepended():
    assert RELATIVE_PATH.with_bucket("bucket") == "s3://bucket/" + str(RELATIVE_PATH)


def test_when_a_valid_bucket_is_added_to_a_relative_path_then_it_becomes_absolute():
    assert RELATIVE_PATH.with_bucket("bucket").is_absolute


def test_when_a_valid_bucket_is_added_to_an_absolute_path_then_it_replaces_then_old_one():
    assert (
        ABSOLUTE_PATH.with_bucket("new-bucket")
        == "s3://new-bucket/" + ABSOLUTE_PATH.key
    )


def test_when_an_invalid_bucket_is_added_to_a_path_then_error_is_raised():
    with pytest.raises(InvalidBucketError):
        RELATIVE_PATH.with_bucket("not$a%valid&bucket*name!")


def test_when_s3_path_is_relative_then_retrieving_bucket_raises_error():
    with pytest.raises(UnknownBucketError):
        _ = RELATIVE_PATH.bucket


def test_when_s3_path_is_absolute_then_bucket_can_be_retrieved():
    assert ABSOLUTE_PATH.bucket == "bucket"


def test_when_path_is_relative_then_retrieving_key_raises_error():
    with pytest.raises(UnknownBucketError):
        _ = RELATIVE_PATH.key


def test_when_path_is_absolute_then_key_can_be_retrieved():
    assert ABSOLUTE_PATH.key == "some/relative/path/file.txt"


def test_when_last_part_of_path_is_a_folder_then_name_can_be_retrieved():
    assert RELATIVE_PATH.name == "path"


def test_when_last_part_of_path_is_a_file_then_name_can_be_retrieved():
    assert ABSOLUTE_PATH.name == "file.txt"


def test_when_path_only_has_bucket_then_name_is_same_as_bucket():
    path = S3Path("s3://bucket/")
    assert path.name == path.bucket
    assert path.name == "bucket"


@pytest.mark.parametrize(
    "starting_path,expected_parent",
    [
        pytest.param(
            "s3://bucket/folder/file.txt", "s3://bucket/folder/", id="file_path"
        ),
        pytest.param("s3://bucket/folder/", "s3://bucket/", id="folder_path"),
        pytest.param("s3://bucket/", None, id="bucket"),
        pytest.param(
            "some/relative/folder/file.txt",
            "some/relative/folder/",
            id="relative_folder_path",
        ),
        pytest.param("file.txt", None, id="relative_file_path"),
    ],
)
def test_retrieving_parent_of_absolute_path(starting_path, expected_parent):
    assert S3Path(starting_path).parent == expected_parent


@pytest.mark.parametrize(
    "starting_path,path_to_add,expected_path",
    [
        pytest.param(
            "s3://bucket/folder",
            "file.txt",
            "s3://bucket/folder/file.txt",
            id="file_in_folder",
        ),
        pytest.param(
            "s3://bucket/folder",
            "/file.txt",
            "s3://bucket/folder/file.txt",
            id="file_with_prefix_slash_in_folder",
        ),
        pytest.param(
            "s3://bucket/folder",
            "folder2",
            "s3://bucket/folder/folder2",
            id="folder_in_folder",
        ),
        pytest.param(
            "s3://bucket/folder",
            "/folder2",
            "s3://bucket/folder/folder2",
            id="folder_with_prefix_slash_in_folder",
        ),
        pytest.param(
            "s3://bucket/folder",
            "folder2/",
            "s3://bucket/folder/folder2",
            id="folder_with_postfix_slash_in_folder",
        ),
        pytest.param(
            "s3://bucket/folder",
            "/folder2/",
            "s3://bucket/folder/folder2",
            id="folder_with_both_slashes_in_folder",
        ),
        pytest.param(
            "s3://bucket/folder",
            "folder2/file.txt",
            "s3://bucket/folder/folder2/file.txt",
            id="folder_with_file_in_folder",
        ),
        pytest.param(
            "s3://bucket/folder",
            "folder2/folder3/",
            "s3://bucket/folder/folder2/folder3",
            id="folder_with_folder_with_postfix_slash_in_folder",
        ),
        pytest.param(
            "s3://bucket/folder",
            "/folder2/folder3",
            "s3://bucket/folder/folder2/folder3",
            id="folder_with_folder_with_prefix_slash_in_folder",
        ),
    ],
)
def test_adding_extra_str_path_parts(starting_path, path_to_add, expected_path):
    assert S3Path(starting_path) / path_to_add == expected_path


@pytest.mark.parametrize(
    "starting_path,path_to_add,expected_path",
    [
        pytest.param(
            "s3://bucket/folder",
            "file.txt",
            "s3://bucket/folder/file.txt",
            id="file_in_folder",
        ),
        pytest.param(
            "s3://bucket/folder",
            "folder2",
            "s3://bucket/folder/folder2",
            id="folder_in_folder",
        ),
        pytest.param(
            "s3://bucket/folder",
            "folder2/file.txt",
            "s3://bucket/folder/folder2/file.txt",
            id="folder_with_file_in_folder",
        ),
    ],
)
def test_adding_extra_paths(starting_path, path_to_add, expected_path):
    assert S3Path(starting_path) / S3Path(path_to_add) == expected_path


def test_when_adding_an_absolute_path_to_another_path_then_error_is_raised():
    with pytest.raises(ValueError):
        ABSOLUTE_PATH / ABSOLUTE_PATH
