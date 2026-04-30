from app.review.rules import is_patch_reviewable, should_ignore_file


def test_should_ignore_lockfile() -> None:
    assert should_ignore_file("package-lock.json") is True


def test_should_ignore_node_modules_file() -> None:
    assert should_ignore_file("node_modules/react/index.js") is True


def test_should_ignore_binary_like_extension() -> None:
    assert should_ignore_file("assets/logo.png") is True


def test_should_not_ignore_normal_source_file() -> None:
    assert should_ignore_file("app/main.py") is False


def test_patch_reviewable_with_valid_patch() -> None:
    patch = "@@ -1,2 +1,4 @@\n-print('old')\n+print('new')\n"
    assert is_patch_reviewable(patch) is True


def test_patch_not_reviewable_when_none() -> None:
    assert is_patch_reviewable(None) is False


def test_patch_not_reviewable_when_too_large() -> None:
    patch = "a" * 13000
    assert is_patch_reviewable(patch, max_patch_chars=12000) is False
