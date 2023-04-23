import Head from 'next/head'

import AudioRecorder from '@/components/AudioRecorder'
import { AudioRecorderProvider } from '@/components/AudioRecorderContext'
console.log(process.env)
export default function Home() {
  return (
    <>
      <Head>
        <title>salman.io</title>
        <meta content="salman.io" name="description" />
        <meta content="width=device-width, initial-scale=1" name="viewport" />
        <link href="/favicon.ico" rel="icon" />
      </Head>
      <main>
        <AudioRecorderProvider>
          <AudioRecorder />
        </AudioRecorderProvider>
      </main>
    </>
  )
}
