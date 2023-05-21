import asyncio
import tempfile
import wave

import whisper
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Input, Static

from salman.voice import MicRecorder


class PromptWidget(Static):
    id = "prompt"
    is_recording = False
    text = reactive("")
    blobs: list[bytes] = []

    def on_mount(self):
        self.whisper_model = whisper.load_model("base")

    async def _record(self):
        with MicRecorder() as recorder:
            async for blob, _ in recorder:
                self.blobs.append(blob)
                await asyncio.sleep(0.1)

    async def start(self):
        self.is_recording = True
        self.rtask = asyncio.create_task(self._record())

    async def stop(self):
        self.rtask.cancel()
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav")
            with wave.open(temp_file, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16384)
                wf.writeframes(b"".join(self.blobs))
            transcription = self.whisper_model.transcribe(temp_file.name)
            self.text = self.text + transcription.get("text")
            input = self.query_one("#promptInput")
            input.value = self.text
            self.is_recording = False
            self.blobs = []
        except Exception as e:
            print(e)

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
