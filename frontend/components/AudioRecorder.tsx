import { useAudioRecorder } from '@/components/AudioRecorderContext'

const AudioRecorder = () => {
  const {
    uuid,
    canRecord,
    requestPermission,
    startRecording,
    stopRecording,
    transcript,
    status,
    audioUrl,
  } = useAudioRecorder()

  return (
    <div>
      <h2>Audio Recorder</h2>
      <main>
        <div>
          {!canRecord ? (
            <button type="button" onClick={requestPermission}>
              Get Microphone
            </button>
          ) : null}
          {canRecord && status === 'inactive' ? (
            <button type="button" onClick={startRecording}>
              Start Recording
            </button>
          ) : null}
          {status === 'active' ? (
            <button
              type="button"
              onClick={() => {
                stopRecording()
              }}
            >
              Stop Recording
            </button>
          ) : null}
        </div>
        {audioUrl ? (
          <div>
            <audio controls src={audioUrl}></audio>
            <a download href={audioUrl}>
              Download Recording
            </a>
          </div>
        ) : null}
        <h3>Transcript {uuid}</h3>
        <p>{transcript}</p>
      </main>
    </div>
  )
}

export default AudioRecorder
