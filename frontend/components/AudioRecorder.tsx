import { stat } from 'fs'

import { MicrophoneIcon } from '@heroicons/react/24/outline'
import { useEffect, useState } from 'react'

import { useAudioRecorder } from '@/components/AudioRecorderContext'

const AudioRecorder = () => {
  const {
    uuid,
    canRecord,
    requestPermission,
    startRecording,
    stopRecording,
    transcripts,
    status,
  } = useAudioRecorder()

  let clickAction: any = requestPermission
  let micClass = ''
  if (canRecord) {
    clickAction = status === 'active' ? stopRecording : startRecording
    micClass =
      status === 'inactive' ? 'bg-green-300' : 'bg-red-300 animate-pulse'
  }

  return (
    <div>
      <MicrophoneIcon
        className={`h-24 w-24 rounded-full ${micClass} p-2`}
        onClick={clickAction}
      />
      <h3>Transcript {uuid}</h3>
      <p>{JSON.stringify(transcripts)}</p>
    </div>
  )
}

export default AudioRecorder
