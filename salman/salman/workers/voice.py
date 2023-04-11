from json import dumps

from salman.nats import NATSManager

STREAM = "voice"
BUCKET = "voice"


async def post_blob(recording_id: str, index: int, blob: bytes):
    """Post a blob to the queue."""
    mgr = await NATSManager().create()
    await mgr.add_stream(STREAM, ["blobs.*.*"])
    kv = await mgr.get_kv_bucket(BUCKET)
    await kv.put(f"blob.{recording_id}.{index}", blob)
    ack = await mgr.publish(
        f"blobs.{recording_id}.{index}",
        dumps({"recording_id": recording_id, "index": index}).encode(),
        stream=STREAM,
    )
    return ack
