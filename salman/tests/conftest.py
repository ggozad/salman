import re
from pathlib import Path

import nats
import pytest
import pytest_asyncio

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


@pytest_asyncio.fixture(autouse=True)
async def cleanup_streams():
    nc = await nats.connect("nats://localhost:4222")
    js = nc.jetstream()
    await js.delete_stream("test_stream")

    yield

    await js.delete_stream("test_stream")
    await nc.close()
