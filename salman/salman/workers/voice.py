import io
from json import dumps

from pydub import AudioSegment

from salman.nats import NATSManager
from salman.voice.detection import VoiceDetector

STREAM = "voice"
BUCKET = "voice"
SUBJECTS = ["blobs.*.*", "recording.*.started", "recording.*.finished"]
WORKER_QUEUE = "voice"


async def post_blob(recording_id: str, index: int, blob: bytes):
    """Post a blob to the queue."""
    mgr = await NATSManager().create()
    await mgr.add_stream(STREAM, SUBJECTS)
    kv = await mgr.get_kv_bucket(BUCKET)
    await kv.put(f"blobs.{recording_id}.{index}", blob)
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


async def conversation_handler():
    """Post a blob to the queue."""
    mgr = await NATSManager().create()
    await mgr.add_stream(STREAM, SUBJECTS)
    kv = await mgr.get_kv_bucket(BUCKET)

    async def on_conversation_started(msg):
        vd = VoiceDetector()
        id = msg.data.decode()

        # Add the first blob
        blob_entry = await kv.get(f"blobs.{id}.0")
        audio = AudioSegment.from_file(io.BytesIO(blob_entry.value))
        vd.add_audio(audio)
        print(f"Processing on voice {id} started")
        print(f"Timeline: {vd.timeline}")
        await msg.ack()

        # Subscribe to subsequent blobs
        async def on_blob(msg):
            blob_entry = await kv.get(msg.subject)
            audio = AudioSegment.from_file(io.BytesIO(blob_entry.value))
            vd.add_audio(audio)
            print(f"Processing on voice {id}...")
            print(f"Timeline: {vd.timeline}")
            await msg.ack()

        blob_sub = await mgr.subscribe(STREAM, f"blobs.{id}.*", cb=on_blob)

        # Subscribe to end of recording
        async def on_conversation_finished(msg):
            vd.finalize()
            print(f"Finalizing voice detection on recording {id}.")
            print(f"Timeline: {vd.timeline}")
            await msg.ack()
            await blob_sub.unsubscribe()
            await end_sub.unsubscribe()

        end_sub = await mgr.subscribe(
            STREAM, f"recording.{id}.finished", cb=on_conversation_finished
        )

    await mgr.subscribe(
        STREAM, "recording.*.started", cb=on_conversation_started, queue=WORKER_QUEUE
    )
    return await mgr.run_forever()


async def end_recording(id: str):
    mgr = await NATSManager().create()
    await mgr.add_stream(STREAM, SUBJECTS)
    await mgr.publish(
        f"recording.{id}.finished",
        id.encode(),
        stream=STREAM,
    )
    return await mgr.stop()
