import asyncio
import shutil
import tempfile
from pathlib import Path

import pytest
from watchfiles import Change

import salman
from salman.documents import watcher
from salman.documents.watcher import watch_for_documents


def copy_test_file(src: Path, dst: Path) -> None:
    shutil.copy2(f"{src.absolute()}", f"{dst.absolute()}")


@pytest.mark.asyncio
async def test_watch_for_documents():
    test_files_dir = Path(salman.__file__).parent.parent / "tests" / "test_documents"

    expected_filename = None
    expected_change = None
    done = False

    async def document_handler(path: str, change: str):
        assert Path(path).name == expected_filename
        assert change == expected_change
        if done:
            task.cancel()

    watcher.document_handler = document_handler
    with tempfile.TemporaryDirectory() as root:
        task = asyncio.create_task(watch_for_documents(Path(root)))

        # First add a file (md)
        expected_filename = "behaving.md"
        expected_change = Change.added
        done = True
        copy_test_file(test_files_dir / "behaving.md", Path(root) / "behaving.md")

        try:
            await task
        except asyncio.CancelledError:
            pass
