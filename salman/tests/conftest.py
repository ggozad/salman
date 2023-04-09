import re
from pathlib import Path

import pytest

import salman


@pytest.fixture(scope="function")
def get_test_blobs(request):
    blobs = []
    test_data_folder = (
        Path(salman.__file__).parent.parent / "tests" / "test_data" / request.param
    )
    blob_files = [f for f in test_data_folder.glob("*.mp4")]
    blob_files.sort(key=lambda f: int(re.sub("\D", "", f.name)))

    for blob in sorted(blob_files):
        with open(blob, "rb") as f:
            blobs.append(f.read())
    return blobs
