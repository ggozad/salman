import {
  Context,
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react'

const mimeType = 'audio/webm'
const loopInterval = 3000

export enum RecorderStatus {
  inactive = 'inactive',
  active = 'active',
}

export interface AudioRecorderState {
  uuid: string
  canRecord: boolean
  status: RecorderStatus
  audioUrl: string
  transcript: string
  requestPermission: () => Promise<void>
  startRecording: () => void
  stopRecording: () => void
}

const recorderContext: Context<AudioRecorderState | undefined> =
  createContext(undefined)

export function AudioRecorderProvider({ children }: { children: ReactNode }) {
  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const [canRecord, setCanRecord] = useState(false)
  const [status, setStatus] = useState<RecorderStatus>(RecorderStatus.inactive)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [audioChunks, setAudioChunks] = useState<Blob[]>([])
  const [audioUrl, setAudioUrl] = useState<string>('')
  const [transcript, setTranscript] = useState<string>('')
  const loopTimeout = useRef<NodeJS.Timeout | null>(null)
  const audioChunksRef = useRef([])
  const uuid = useRef('')

  console.log(audioChunks)

  useEffect(() => {
    audioChunksRef.current = audioChunks
  }, [audioChunks])

  const requestPermission = useCallback(async () => {
    if ('MediaRecorder' in window) {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: true,
          video: false,
        })
        setCanRecord(true)
        setStream(mediaStream)
      } catch (err) {
        console.error(err) //@ts-ignore
      }
    } else {
      console.error('The MediaRecorder API is not supported in your browser.')
    }
  }, [])

  useEffect(() => {
    if (canRecord) return
    requestPermission()
  }, [canRecord, requestPermission])

  useEffect(() => {
    if (audioChunks.length === 0) return

    const chunk = new Blob([audioChunks[audioChunks.length - 1]], {
      type: mimeType,
    })
  }, [audioChunks])

  const stopRecording = useCallback(() => {
    setStatus(RecorderStatus.inactive)
    if (mediaRecorder.current === null) return
    mediaRecorder.current.stop()
    clearTimeout(loopTimeout.current)
  }, [])

  const startRecording = useCallback(() => {
    setStatus(RecorderStatus.active)
    setAudioChunks([])
    uuid.current = Math.random().toString(36).substring(2, 15)
    if (stream === null) return
    const media = new MediaRecorder(stream)

    mediaRecorder.current = media
    mediaRecorder.current.start()

    mediaRecorder.current.ondataavailable = (event) => {
      if (!event.data) return
      if (event.data.size === 0) return
      setAudioChunks([...audioChunksRef.current, event.data])
    }

    const loop = () => {
      mediaRecorder.current.stop()
      mediaRecorder.current.onstop = () => {
        mediaRecorder.current.start()
      }
      loopTimeout.current = setTimeout(loop, loopInterval)
    }
    loopTimeout.current = setTimeout(loop, loopInterval)
  }, [stream])

  return (
    <recorderContext.Provider
      value={{
        uuid: uuid.current,
        canRecord,
        status,
        audioUrl,
        transcript,
        requestPermission,
        startRecording,
        stopRecording,
      }}
    >
      {children}
    </recorderContext.Provider>
  )
}

export function useAudioRecorder() {
  return useContext(recorderContext)
}
