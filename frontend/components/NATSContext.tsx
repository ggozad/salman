import {
  Codec,
  NatsConnection,
  PublishOptions,
  StringCodec,
  Subscription,
  SubscriptionOptions,
  connect,
} from 'nats.ws'
import {
  Context,
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'

export interface NATSState {
  connection: NatsConnection | null
  connect: () => Promise<void>
  disconnect: () => Promise<void>
  publish: (subject: string, msg?: Uint8Array, options?: PublishOptions) => void
  subscribe: (subject: string, options?: SubscriptionOptions) => Subscription
  codec: Codec<string>
}

const natsContext: Context<NATSState | undefined> = createContext(undefined)

const codec = StringCodec()

export function NATSProvider({ children }: { children: ReactNode }) {
  const [connection, setConnection] = useState<NatsConnection | null>(null)

  const serverDisconnect = useCallback(async () => {}, [])

  const serverConnect = useCallback(async () => {
    return await connect({
      servers: [process.env.NEXT_PUBLIC_NATS_WS],
    }).then((nc) => {
      setConnection(nc)
    })
  }, [])

  const publish = useCallback(
    (subject: string, msg?: Uint8Array, options?: PublishOptions) => {
      connection.publish(subject, msg, options)
    },
    [connection]
  )
  const subscribe = useCallback(
    (subject: string, options?: SubscriptionOptions) =>
      connection.subscribe(subject, options),
    [connection]
  )

  useEffect(() => {
    if (!connection) {
      serverConnect()
    }
  }, [connection, serverConnect])

  return (
    <natsContext.Provider
      value={{
        connection,
        connect: serverConnect,
        disconnect: serverDisconnect,
        publish,
        subscribe,
        codec,
      }}
    >
      {children}
    </natsContext.Provider>
  )
}

export function useNATS() {
  return useContext(natsContext)
}
