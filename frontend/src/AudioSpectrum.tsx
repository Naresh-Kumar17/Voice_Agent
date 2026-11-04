import React, { useEffect, useRef } from 'react'

interface AudioSpectrumProps {
  active: boolean
  isSpeaking: boolean // true when either local mic or agent is speaking
  speakerLabel?: string // 'You' or 'Rachel' or 'Standby'
  barCount?: number
  className?: string
}

export const AudioSpectrum: React.FC<AudioSpectrumProps> = ({
  active,
  isSpeaking,
  speakerLabel = 'Standby',
  barCount = 24,
  className = '',
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const animFrameRef = useRef<number>(0)
  const phaseRef = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    const width = 280
    const height = 48
    canvas.width = width * dpr
    canvas.height = height * dpr
    ctx.scale(dpr, dpr)

    const bars: number[] = Array.from({ length: barCount }, () => 0.1)

    const render = () => {
      phaseRef.current += isSpeaking ? 0.08 : 0.02
      const phase = phaseRef.current

      ctx.clearRect(0, 0, width, height)

      const barWidth = 4
      const gap = (width - barCount * barWidth) / (barCount - 1)
      const centerY = height / 2

      for (let i = 0; i < barCount; i++) {
        const normalizedIdx = Math.abs(i - barCount / 2) / (barCount / 2)
        const envelope = 1 - Math.pow(normalizedIdx, 1.8) // Taper at edges

        // Target amplitude
        let target = 0.08
        if (active && isSpeaking) {
          const wave1 = Math.sin(phase + i * 0.45) * 0.5 + 0.5
          const wave2 = Math.cos(phase * 1.5 - i * 0.3) * 0.3 + 0.3
          target = (wave1 * 0.7 + wave2 * 0.3) * envelope * 0.95 + 0.1
        } else if (active) {
          target = (Math.sin(phase * 0.5 + i * 0.2) * 0.15 + 0.15) * envelope + 0.05
        }

        // Smooth current height
        bars[i] += (target - bars[i]) * 0.18
        const barHeight = Math.max(bars[i] * height * 0.85, 4)

        const x = i * (barWidth + gap)
        const y = centerY - barHeight / 2

        // Create iridescent gradient per bar
        const grad = ctx.createLinearGradient(x, y, x, y + barHeight)
        if (speakerLabel === 'You') {
          grad.addColorStop(0, '#6ee7b7')
          grad.addColorStop(1, '#059669')
        } else if (speakerLabel === 'Rachel') {
          grad.addColorStop(0, '#38bdf8')
          grad.addColorStop(0.5, '#818cf8')
          grad.addColorStop(1, '#c084fc')
        } else {
          grad.addColorStop(0, 'rgba(56, 189, 248, 0.4)')
          grad.addColorStop(1, 'rgba(99, 102, 241, 0.2)')
        }

        ctx.fillStyle = grad
        ctx.beginPath()
        // Rounded pill bars
        const r = barWidth / 2
        ctx.roundRect(x, y, barWidth, barHeight, r)
        ctx.fill()
      }

      animFrameRef.current = requestAnimationFrame(render)
    }

    render()

    return () => {
      cancelAnimationFrame(animFrameRef.current)
    }
  }, [active, isSpeaking, speakerLabel, barCount])

  return (
    <div className={`audio-spectrum-wrapper ${className}`}>
      <div className="spectrum-header">
        <span className="spectrum-badge">
          <i className={`spectrum-dot ${active ? 'active' : ''}`} />
          {speakerLabel === 'You' ? 'PATIENT SPEAKING' : speakerLabel === 'Rachel' ? 'RACHEL SPEAKING' : 'AUDIO SPECTRUM'}
        </span>
        <span className="spectrum-freq">{active ? '48 kHz • WebRTC HD' : 'Standby'}</span>
      </div>
      <canvas ref={canvasRef} style={{ width: 280, height: 48, display: 'block' }} />
    </div>
  )
}
export default AudioSpectrum

