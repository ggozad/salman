import io
from json import dumps

from pydub import AudioSegment

from salman.nats import NATSManager
from salman.voice.detection import VoiceDetector

STREAM = "voice"
SUBJECTS = [
    "blobs.*.*",
    "segments.*.*",
    "recording.*.started",
    "recording.*.finished",
    "segmenting.*.finished",
    "transcribing.*.finished",
]
QUEUE = "voice"


async def post_blob(recording_id: str, index: int, blob: bytes):
    """Post a blob to the queue."""
    mgr = await NATSManager.create()
    await mgr.add_stream(STREAM, SUBJECTS)
    blob_bucket = await mgr.get_kv_bucket(f"blobs-{recording_id}")
    await blob_bucket.put(f"blobs.{recording_id}.{index}", blob)
    await mgr.publish(
        f"blobs.{recording_id}.{index}",
        dumps({"recording_id": recording_id, "index": index}).encode(),
        stream=STREAM,
    )

    if index == 0:
        await mgr.publish(
            f"recording.{recording_id}.started",
            recording_id.encode(),
            stream=STREAM,
        )

    return await mgr.stop()


async def recording_handler():
    """Process blobs posted and compute voice audio segments."""
    mgr = await NATSManager.create()
    await mgr.add_stream(STREAM, SUBJECTS)

    async def on_recording_started(msg):
        vd = VoiceDetector()
        recording_id = msg.data.decode()
        blob_bucket = await mgr.get_kv_bucket(f"blobs-{recording_id}")
        segment_bucket = await mgr.get_kv_bucket(f"segments-{recording_id}")
        segment_count = 0
        # Add the first blob
        blob_entry = await blob_bucket.get(f"blobs.{recording_id}.0")
        audio = AudioSegment.from_file(io.BytesIO(blob_entry.value))
        vd.add_audio(audio)
        print(f"Processing on voice {recording_id} started")

        # Subscribe to subsequent blobs
        async def on_blob(msg):
            nonlocal segment_count
            await msg.ack()

            blob_entry = await blob_bucket.get(msg.subject)
            audio = AudioSegment.from_file(io.BytesIO(blob_entry.value))
            segments = vd.add_audio(audio)
            timeline = vd.timeline
            print(f"Processing on voice {recording_id}...")
            print(f"Found {len(segments)} segments.")
            if segments:
                for segment in segments:
                    await segment_bucket.put(
                        f"segments.{recording_id}.{segment_count}",
                        segment.export(format="wav").read(),
                    )
                    await mgr.publish(
                        f"segments.{recording_id}.{segment_count}",
                        dumps(
                            {
                                "start": timeline[segment_count].start,
                                "end": timeline[segment_count].end,
                            }
                        ).encode(),
                    )
                    segment_count += 1

        blob_sub = await mgr.subscribe(STREAM, f"blobs.{recording_id}.*", cb=on_blob)
        await msg.ack()

        # Subscribe to end of recording
        async def on_recording_finished(msg):
            nonlocal segment_count
            await msg.ack()
            print(f"Finalizing voice detection on recording {recording_id}.")
            segments = vd.finalize()
            timeline = vd.timeline
            print(f"Found {len(segments)} segments.")

            if segments:
                for segment in segments:
                    await segment_bucket.put(
                        f"segments.{recording_id}.{segment_count}",
                        segment.export(format="wav").read(),
                    )
                    await mgr.publish(
                        f"segments.{recording_id}.{segment_count}",
                        dumps(
                            {
                                "start": timeline[segment_count].start,
                                "end": timeline[segment_count].end,
                            }
                        ).encode(),
                    )
                    segment_count += 1
            print(f"Timeline: {timeline}")
            await mgr.publish(
                f"segmenting.{recording_id}.finished",
                recording_id.encode(),
            )
            await blob_sub.unsubscribe()
            await end_sub.unsubscribe()
            await mgr.delete_kv_bucket(f"blobs-{recording_id}")

        end_sub = await mgr.subscribe(
            STREAM, f"recording.{recording_id}.finished", cb=on_recording_finished
        )

    await mgr.subscribe(
        STREAM, "recording.*.started", cb=on_recording_started, queue=QUEUE
    )
    return await mgr.run_forever()


async def transcription_handler():
    mgr = await NATSManager.create()
    await mgr.add_stream(STREAM, SUBJECTS)

    async def on_recording_started(msg):
        recording_id = msg.data.decode()
        print(f"Transcription on voice {recording_id} started")
        pass

    await mgr.subscribe(
        STREAM, "recording.*.started", cb=on_recording_started, queue=QUEUE
    )
    return await mgr.run_forever()


async def end_recording(id: str):
    mgr = await NATSManager.create()
    await mgr.add_stream(STREAM, SUBJECTS)
    await mgr.publish(
        f"recording.{id}.finished",
        id.encode(),
        stream=STREAM,
    )
    return await mgr.stop()
