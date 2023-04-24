import { connect } from 'nats.ws'
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

export interface NATSState {
  connection: any
}

const natsContext: Context<NATSState | undefined> = createContext(undefined)

export function NATSProvider({ children }: { children: ReactNode }) {
  const [connection, setConnection] = useState<any>(null)
  useEffect(() => {
    async function serverConnect() {
      const nc = await connect({
        servers: [process.env.NEXT_PUBLIC_NATS_WS],
      })
      setConnection(nc)
      console.log('connected')
    }
    if (!connection) serverConnect()
  }, [connection])

  return (
    <natsContext.Provider
      value={{
        connection,
      }}
    >
      {children}
    </natsContext.Provider>
  )
}

export function useNATS() {
  return useContext(natsContext)
}
