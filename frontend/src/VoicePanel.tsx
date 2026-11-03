import { useCallback, useEffect, useRef, useState } from 'react'
import { Room, RoomEvent, Track, type TranscriptionSegment } from 'livekit-client'
import { api, type LiveKitCredentials } from './api'

type TranscriptLine = { id: string; speaker: string; text: string; final: boolean }

export default function VoicePanel() {
  const roomRef = useRef<Room | null>(null)
  const audioElements = useRef<HTMLAudioElement[]>([])
  const [connecting, setConnecting] = useState(false)
  const [connected, setConnected] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [error, setError] = useState('')
  const [lines, setLines] = useState<TranscriptLine[]>([])

  const disconnect = useCallback(async () => {
    const room = roomRef.current
    roomRef.current = null
    if (room) await room.disconnect()
    setConnected(false)
    setSpeaking(false)
  }, [])

  useEffect(() => () => {
    void roomRef.current?.disconnect()
    audioElements.current.forEach(element => element.remove())
    audioElements.current = []
  }, [])

  const connect = async () => {
    setConnecting(true)
    setError('')
    setLines([])
    let room: Room | null = null
    try {
      const creds = await api<LiveKitCredentials>('/api/v1/livekit/token', { method: 'POST', body: '{}' })
      room = new Room({ adaptiveStream: true, dynacast: true })
      roomRef.current = room
      room.on(RoomEvent.Connected, () => setConnected(true))
      room.on(RoomEvent.Disconnected, () => {
        setConnected(false)
        setSpeaking(false)
        audioElements.current.forEach(element => element.remove())
        audioElements.current = []
      })
      room.on(RoomEvent.ActiveSpeakersChanged, speakers => {
        setSpeaking(speakers.some(speaker => speaker.isLocal))
      })
      room.on(RoomEvent.TranscriptionReceived, (segments: TranscriptionSegment[], participant) => {
        setLines(current => {
          const next = [...current]
          for (const segment of segments) {
            const item = {
              id: segment.id,
              speaker: participant?.identity === room?.localParticipant.identity ? 'You' : 'Receptionist',
              text: segment.text,
              final: segment.final,
            }
            const existing = next.findIndex(line => line.id === item.id)
            if (existing >= 0) next[existing] = item
            else next.push(item)
          }
          return next.slice(-30)
        })
      })
      room.on(RoomEvent.TrackSubscribed, (track, _publication, participant) => {
        if (track.kind === Track.Kind.Audio && participant.identity !== room?.localParticipant.identity) {
          const audio = track.attach()
          audio.autoplay = true
          audio.setAttribute('playsinline', 'true')
          document.body.appendChild(audio)
          audioElements.current.push(audio)
        }
      })
      await room.connect(creds.server_url, creds.participant_token)
      await room.localParticipant.setMicrophoneEnabled(true)
      setConnected(true)
    } catch (cause) {
      await room?.disconnect().catch(() => undefined)
      roomRef.current = null
      setError(cause instanceof Error ? cause.message : 'Could not connect to the voice receptionist.')
      setConnected(false)
    } finally {
      setConnecting(false)
    }
  }

  return (
    <section className="voice-card" aria-labelledby="voice-title">
      <div className="voice-heading">
        <div>
          <span className="eyebrow">SERENITY MEDICAL CLINIC</span>
          <h2 id="voice-title">Talk to our receptionist</h2>
          <p>Ask about the clinic or get help scheduling a visit.</p>
        </div>
        <span className={`live-pill ${connected ? 'is-live' : ''}`}><i />{connected ? 'Connected' : 'Ready when you are'}</span>
      </div>

      <div className={`voice-orb ${speaking ? 'is-speaking' : ''}`} aria-label={speaking ? 'Microphone active' : 'Voice connection'}>
        <span className="orb-ring ring-one" /><span className="orb-ring ring-two" />
        <span className="orb-core"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v6a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.93V22h2v-3.07A7 7 0 0 0 19 12Z" /></svg></span>
      </div>

      <div className="voice-actions">
        {connected ? <button className="button button-stop" onClick={() => void disconnect()}>End call</button> :
          <button className="button button-primary" disabled={connecting} onClick={() => void connect()}>{connecting ? <><span className="spinner" />Connecting…</> : 'Start a voice call'}</button>}
        <span className="privacy-note">Microphone access is requested by your browser</span>
      </div>

      {error && <div className="inline-error" role="alert">{error}</div>}
      <div className="transcript" aria-live="polite" aria-label="Live conversation transcript">
        {lines.length === 0 ? <p className="transcript-empty">Your conversation transcript will appear here.</p> : lines.map(line => (
          <p className={`transcript-line ${line.speaker === 'You' ? 'from-user' : ''}`} key={line.id}><strong>{line.speaker}</strong>{line.text}</p>
        ))}
      </div>
    </section>
  )
}
