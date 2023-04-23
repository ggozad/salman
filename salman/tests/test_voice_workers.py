import asyncio
from json import loads

import pytest

from salman.config import Config
from salman.nats import NATSManager
from salman.workers.voice import (
    SUBJECTS,
    end_recording,
    post_blob,
    segmentation_handler,
    transcription_handler,
)


@pytest.mark.parametrize("get_test_blobs", ["conversations/1"], indirect=True)
@pytest.mark.asyncio
async def test_voice_detection_worker(get_test_blobs):
    mgr = await NATSManager.create(Config.NATS_URL)
    await mgr.add_stream("test_stream", SUBJECTS)
    segmentation_task = asyncio.create_task(segmentation_handler())
    transcription_task = asyncio.create_task(transcription_handler())

    segments = []
    transcripts = []

    async def on_segment(msg):
        segments.append(loads(msg.data.decode()))
        await msg.ack()

    async def on_transcript(msg):
        transcripts.append(loads(msg.data.decode()))
        await msg.ack()

    async def segmentation_done(msg):
        segmentation_task.cancel()

    async def transcription_done(msg):
        transcription_task.cancel()

    await mgr.subscribe("test_stream", "segments.test.*", on_segment)
    await mgr.subscribe("test_stream", "transcripts.test.*", on_transcript)
    await mgr.subscribe("test_stream", "segmenting.test.finished", segmentation_done)
    await mgr.subscribe("test_stream", "transcribing.test.finished", transcription_done)

    for i, blob in enumerate(get_test_blobs):
        await post_blob("test", i, blob)
        await asyncio.sleep(0.1)
    await end_recording("test")

    await segmentation_task

    assert len(segments) == 14
    assert round(segments[0]["start"], 3) == 0.278
    assert round(segments[0]["end"], 3) == 4.244
    assert round(segments[-1]["start"], 3) == 37.091
    assert round(segments[-1]["end"], 3) == 41.377

    await transcription_task
    assert len(transcripts) == len(segments)
    assert (
        transcripts[0].get("text")
        == " No, not suddenly. For a while she was translating movie subtitles."
    )
    assert transcripts[0].get("language") == "en"
    assert (
        transcripts[-1].get("text")
        == " I'll show it off to everybody and tell them I know somebody who knows somebody famous."
    )
    assert transcripts[-1].get("language") == "en"

    await asyncio.sleep(0.5)
    await mgr.stop()
