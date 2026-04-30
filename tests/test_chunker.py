from app.review.chunker import build_review_chunks, split_patch_into_chunks
from app.schemas.review import ReviewableFile


def test_split_patch_into_chunks_returns_single_chunk_for_small_patch() -> None:
    patch = "@@ -1 +1 @@\n-print('old')\n+print('new')\n"
    chunks = split_patch_into_chunks(patch, max_chunk_chars=3000)

    assert len(chunks) == 1
    assert chunks[0] == patch


def test_split_patch_into_chunks_returns_multiple_chunks_for_large_patch() -> None:
    patch = "".join([f"+line {i}\n" for i in range(1000)])
    chunks = split_patch_into_chunks(patch, max_chunk_chars=500)

    assert len(chunks) > 1


def test_build_review_chunks_creates_chunk_metadata() -> None:
    files = [
        ReviewableFile(
            filename="app/main.py",
            status="modified",
            additions=10,
            deletions=2,
            changes=12,
            patch="".join([f"+line {i}\n" for i in range(300)]),
            blob_url="https://github.com/example/repo/blob/main/app/main.py",
            raw_url="https://raw.githubusercontent.com/example/repo/main/app/main.py",
        )
    ]

    chunks = build_review_chunks(files, max_chunk_chars=500)

    assert len(chunks) > 1
    assert chunks[0].filename == "app/main.py"
    assert chunks[0].chunk_index == 1
    assert chunks[0].total_chunks == len(chunks)
