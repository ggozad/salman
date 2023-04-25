import { Subscription } from 'nats.ws'
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

import { useNATS } from '@/components/NATSContext'

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
  transcripts: any[]
  requestPermission: () => Promise<void>
  startRecording: () => void
  stopRecording: () => void
}

const recorderContext: Context<AudioRecorderState | undefined> =
  createContext(undefined)

export function AudioRecorderProvider({ children }: { children: ReactNode }) {
  const { codec, jetstream, publish, subscribe } = useNATS()
  const [transcriptSub, setTranscriptSub] = useState<Subscription | null>(null)
  const [transcriptionFinishedSub, setTranscriptionFinishedSub] =
    useState<Subscription | null>(null)

  const [transcripts, setTranscripts] = useState([])

  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const [canRecord, setCanRecord] = useState(false)
  const [status, setStatus] = useState<RecorderStatus>(RecorderStatus.inactive)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [audioChunks, setAudioChunks] = useState<Blob[]>([])
  const loopTimeout = useRef<NodeJS.Timeout | null>(null)

  const audioChunksRef = useRef([])
  const uuid = useRef('')

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
    const effect = async () => {
      if (audioChunks.length === 0) return
      const recording_id = uuid.current
      const index = audioChunks.length - 1
      const chunk = new Blob([audioChunks[index]], {
        type: mimeType,
      })

      const buffer = await chunk.arrayBuffer()
      const arr = new Uint8Array(buffer)
      const kvStore = await jetstream.views.kv(`blobs-${uuid.current}`)
      await kvStore.put(`blobs.${recording_id}.${index}`, arr)
      await publish(
        `blobs.${recording_id}.${index}`,
        codec.encode(JSON.stringify({ recording_id, index }))
      )
    }
    effect()
  }, [audioChunks, codec, jetstream, publish, transcriptSub])

  useEffect(() => {
    const fetch = async () => {
      if (transcriptSub !== null) {
        let transcripts = []
        for await (const m of transcriptSub) {
          const transcript = codec.decode(m.data)
          transcripts.push(JSON.parse(transcript))
        }
        setTranscripts(transcripts)
      }
    }
    fetch()
  }, [transcriptSub, codec])

  useEffect(() => {
    const fetch = async () => {
      if (transcriptionFinishedSub !== null) {
        for await (const m of transcriptionFinishedSub) {
          transcriptionFinishedSub.unsubscribe()
          transcriptSub.unsubscribe()
          setTranscriptSub(null)
          setTranscriptionFinishedSub(null)
        }
      }
    }
    fetch()
  }, [transcriptSub, transcriptionFinishedSub, codec])

  const stopRecording = useCallback(() => {
    setStatus(RecorderStatus.inactive)
    if (mediaRecorder.current === null) return
    mediaRecorder.current.stop()
    clearTimeout(loopTimeout.current)
    setTimeout(() => {
      publish(`recording.${uuid.current}.finished`, codec.encode(uuid.current))
    }, 1000)
  }, [codec, publish])

  const startRecording = useCallback(() => {
    uuid.current = Math.random().toString(36).substring(2, 15)
    let sub = subscribe(`transcripts.${uuid.current}.*`)
    setTranscriptSub(sub)
    sub = subscribe(`transcribing.${uuid.current}.finished`)
    setTranscriptionFinishedSub(sub)
    publish(`recording.${uuid.current}.started`, codec.encode(uuid.current))

    setStatus(RecorderStatus.active)
    setAudioChunks([])
    setTranscripts([])

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
  }, [stream, subscribe, codec, publish])

  return (
    <recorderContext.Provider
      value={{
        uuid: uuid.current,
        canRecord,
        status,
        transcripts,
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
