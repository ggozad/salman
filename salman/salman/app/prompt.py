import asyncio
import json
import uuid

from pydub import AudioSegment
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Input, Static

from salman.config import Config
from salman.nats import Session
from salman.voice.recorder import MicRecorder
from salman.workers.voice import end_recording, post_blob, start_recording


class PromptWidget(Static):
    id = "prompt"
    uid = ""
    is_recording = False
    text = reactive("")

    async def on_mount(self) -> None:
        self.nats = Session(Config.NATS_URL)
        await self.nats.start()

    async def _record_and_transcribe(self):
        count = 0
        with MicRecorder() as recorder:
            async for blob, _ in recorder:
                audio_segment = AudioSegment(
                    blob, sample_width=2, channels=1, frame_rate=16384
                )
                await post_blob(
                    self.uid, count, audio_segment.export(format="mp4").read()
                )
                count += 1
                await asyncio.sleep(0.01)

    async def start(self):
        async def on_transcript(msg):
            text = json.loads(msg.data.decode()).get("text")
            self.text = self.text + text
            input = self.query_one("#promptInput")
            input.value = self.text

            await msg.ack()

        async def on_transcription_finished(self, msg):
            await self._trancript_sub.unsubscribe()
            await self._trancription_finished_sub.unsubscribe()
            await msg.ack()

        self.uid = uuid.uuid4().hex
        self._trancript_sub = await self.nats.subscribe(
            Config.VOICE_STREAM, f"transcripts.{self.uid}.*", on_transcript
        )
        self._trancription_finished_sub = await self.nats.subscribe(
            Config.VOICE_STREAM,
            f"transcribing.{self.uid}.finished",
            on_transcription_finished,
        )
        await start_recording(self.uid)

        self.rtask = asyncio.create_task(self._record_and_transcribe())
        self.is_recording = True

    async def stop(self):
        self.rtask.cancel()
        await end_recording(self.uid)
        self.is_recording = False

    @on(Button.Pressed, "#recordButton")
    async def toggle_recording(self) -> None:
        """Event handler called when a button is pressed."""
        if not self.is_recording:
            await self.start()
        else:
            await self.stop()
        btn = self.query_one("#recordButton")
        btn.label = "Stop" if self.is_recording else "Record"
        btn.variant = "error" if self.is_recording else "primary"

    def compose(self) -> ComposeResult:
        """Human prompt."""
        with Horizontal():
            yield Button(label="Record", id="recordButton", variant="primary")
            yield Input(
                placeholder="Your prompt here",
                id="promptInput",
            )
