from __future__ import annotations

from app.schemas.review import ReviewableFile, ReviewChunk


def split_patch_into_chunks(patch: str, max_chunk_chars: int = 3000) -> list[str]:
    lines = patch.splitlines(keepends=True)

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_size = 0

    for line in lines:
        line_length = len(line)

        if current_chunk and current_size + line_length > max_chunk_chars:
            chunks.append("".join(current_chunk))
            current_chunk = [line]
            current_size = line_length
        else:
            current_chunk.append(line)
            current_size += line_length

    if current_chunk:
        chunks.append("".join(current_chunk))

    return chunks


def build_review_chunks(
    files: list[ReviewableFile],
    max_chunk_chars: int = 3000,
) -> list[ReviewChunk]:
    all_chunks: list[ReviewChunk] = []

    for file in files:
        patch_chunks = split_patch_into_chunks(
            file.patch,
            max_chunk_chars=max_chunk_chars,
        )

        total_chunks = len(patch_chunks)

        for idx, patch_chunk in enumerate(patch_chunks, start=1):
            all_chunks.append(
                ReviewChunk(
                    chunk_id=f"{file.filename}::chunk-{idx}",
                    filename=file.filename,
                    chunk_index=idx,
                    total_chunks=total_chunks,
                    patch=patch_chunk,
                    additions=file.additions,
                    deletions=file.deletions,
                    changes=file.changes,
                    status=file.status,
                    blob_url=file.blob_url,
                    raw_url=file.raw_url,
                )
            )

    return all_chunks
