import io
from json import dumps, loads

from pydub import AudioSegment

from salman.config import Config
from salman.nats import Session
from salman.voice.detection import VoiceDetector
from salman.voice.transcription import transcribe_segment

SUBJECTS = [
    "blobs.*.*",
    "segments.*.*",
    "transcripts.*.*",
    "recording.*.started",
    "recording.*.finished",
    "segmenting.*.finished",
    "transcribing.*.finished",
]
SEGMENTATION_QUEUE = "segmentation"
TRANSCRIPTION_QUEUE = "transcription"
CLEANUP_QUEUE = "cleanup"


async def segmentation_handler():
    """Process blobs posted and compute voice audio segments."""
    from salman.logging import segmentation_logger as logger

    logger.info("Segmentation handler started.")
    async with Session(url=Config.NATS_URL) as mgr:

        async def on_recording_started(msg):
            vd = VoiceDetector()
            recording_id = msg.data.decode()
            blob_bucket = await mgr.get_kv_bucket(f"blobs-{recording_id}")
            segment_bucket = await mgr.get_kv_bucket(f"segments-{recording_id}")
            segment_count = 0
            logger.info(f'Segmentation on recording "{recording_id}" started.')

            # Subscribe to subsequent blobs
            async def on_blob(msg):
                nonlocal segment_count
                await msg.ack()
                blob_entry = await blob_bucket.get(msg.subject)
                audio = AudioSegment.from_file(io.BytesIO(blob_entry.value))
                segments = vd.add_audio(audio)
                timeline = vd.timeline
                logger.info(
                    f"Segmenting on {msg.subject}, {len(segments)} segments found."
                )
                if segments:
                    for segment in segments:
                        await segment_bucket.put(
                            f"segments.{recording_id}.{segment_count}",
                            segment.export(format="wav").read(),
                        )
                        await mgr.publish(
                            f"segments.{recording_id}.{segment_count}",
                            dumps(timeline[segment_count].for_json()).encode(),
                        )
                        segment_count += 1

            blob_sub = await mgr.subscribe(
                Config.VOICE_STREAM, f"blobs.{recording_id}.*", cb=on_blob
            )
            await msg.ack()

            # Subscribe to end of recording
            async def on_recording_finished(msg):
                nonlocal segment_count
                await msg.ack()
                logger.info(f"Finalizing segmentation of recording {recording_id}.")
                segments = vd.finalize()
                timeline = vd.timeline
                logger.info(
                    f"Final segmenting on {msg.subject}, {len(segments)} segments found."
                )

                if segments:
                    for segment in segments:
                        await segment_bucket.put(
                            f"segments.{recording_id}.{segment_count}",
                            segment.export(format="wav").read(),
                        )
                        await mgr.publish(
                            f"segments.{recording_id}.{segment_count}",
                            dumps(timeline[segment_count].for_json()).encode(),
                        )
                await mgr.publish(
                    f"segmenting.{recording_id}.finished",
                    dumps(timeline.for_json()["content"]).encode(),
                )
                await blob_sub.unsubscribe()
                await end_sub.unsubscribe()

            end_sub = await mgr.subscribe(
                Config.VOICE_STREAM,
                f"recording.{recording_id}.finished",
                cb=on_recording_finished,
            )

        await mgr.subscribe(
            Config.VOICE_STREAM,
            "recording.*.started",
            cb=on_recording_started,
            queue=SEGMENTATION_QUEUE,
        )
        return await mgr.run_forever()


async def transcription_handler():
    from salman.logging import transcription_logger as logger

    logger.info("Transcription handler started.")

    async with Session(url=Config.NATS_URL) as mgr:

        async def on_recording_started(msg):
            recording_id = msg.data.decode()
            logger.info(f"Transcription on recording {recording_id} started")
            segment_bucket = await mgr.get_kv_bucket(f"segments-{recording_id}")
            transcript_count = 0
            total_segments = None

            # Subscribe to subsequent segments
            async def on_segment(msg):
                nonlocal transcript_count
                logger.info(f"Transcribing {msg.subject}.")
                segment_timeline = loads(msg.data.decode())
                segment_entry = await segment_bucket.get(msg.subject)
                wav = segment_entry.value
                segment_transcription = transcribe_segment(
                    AudioSegment.from_file(io.BytesIO(wav))
                )
                segment_timeline["text"] = segment_transcription["text"]
                segment_timeline["language"] = segment_transcription["language"]
                logger.info(segment_timeline)
                await mgr.publish(
                    f"transcripts.{recording_id}.{transcript_count}",
                    dumps(segment_timeline).encode(),
                )

                if (
                    total_segments is not None
                    and transcript_count == total_segments - 1
                ):
                    logger.info(
                        f"Finalizing transcription on recording {recording_id}."
                    )
                    await end_sub.unsubscribe()
                    await segment_sub.unsubscribe()
                    await mgr.publish(
                        f"transcribing.{recording_id}.finished",
                        recording_id.encode(),
                    )

                transcript_count += 1
                await msg.ack()

            segment_sub = await mgr.subscribe(
                Config.VOICE_STREAM, f"segments.{recording_id}.*", cb=on_segment
            )

            # Subscribe to end of recording
            async def on_segmenting_finished(msg):
                nonlocal total_segments
                segments = loads(msg.data.decode())
                total_segments = len(segments)

            end_sub = await mgr.subscribe(
                Config.VOICE_STREAM, "segmenting.*.finished", cb=on_segmenting_finished
            )
            await msg.ack()

        await mgr.subscribe(
            Config.VOICE_STREAM,
            "recording.*.started",
            cb=on_recording_started,
            queue=TRANSCRIPTION_QUEUE,
        )
        return await mgr.run_forever()


async def cleanup_handler():
    from salman.logging import cleanup_logger as logger

    logger.info("Cleanup handler started.")

    async with Session(url=Config.NATS_URL) as mgr:

        async def on_transcription_finished(msg):
            recording_id = msg.data.decode()
            await msg.ack()
            logger.info(f"Cleaning up recording {recording_id}.")
            await mgr.delete_kv_bucket(f"segments-{recording_id}")
            await mgr.delete_kv_bucket(f"blobs-{recording_id}")

        await mgr.subscribe(
            Config.VOICE_STREAM,
            "transcribing.*.finished",
            cb=on_transcription_finished,
            queue=CLEANUP_QUEUE,
        )
        return await mgr.run_forever()


async def post_blob(recording_id: str, index: int, blob: bytes):
    """Post a blob to the queue."""
    async with Session(url=Config.NATS_URL) as mgr:
        blob_bucket = await mgr.get_kv_bucket(f"blobs-{recording_id}")
        await blob_bucket.put(f"blobs.{recording_id}.{index}", blob)
        await mgr.publish(
            f"blobs.{recording_id}.{index}",
            dumps({"recording_id": recording_id, "index": index}).encode(),
            stream=Config.VOICE_STREAM,
        )


async def start_recording(id: str):
    async with Session(url=Config.NATS_URL) as mgr:
        await mgr.publish(
            f"recording.{id}.started",
            id.encode(),
            stream=Config.VOICE_STREAM,
        )


async def end_recording(id: str):
    async with Session(url=Config.NATS_URL) as mgr:
        await mgr.publish(
            f"recording.{id}.finished",
            id.encode(),
            stream=Config.VOICE_STREAM,
        )
