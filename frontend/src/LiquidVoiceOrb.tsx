import React, { useEffect, useRef } from 'react'

export type OrbState = 'idle' | 'connecting' | 'listening' | 'speaking' | 'thinking'

interface LiquidVoiceOrbProps {
  state: OrbState
  audioLevel?: number // 0.0 to 1.0 (reactive volume)
  size?: number
  className?: string
  onClick?: () => void
}

export const LiquidVoiceOrb: React.FC<LiquidVoiceOrbProps> = ({
  state,
  audioLevel = 0,
  size = 280,
  className = '',
  onClick,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const animFrameRef = useRef<number>(0)
  const timeRef = useRef<number>(0)
  const smoothedLevelRef = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // High-DPI support
    const dpr = window.devicePixelRatio || 1
    canvas.width = size * dpr
    canvas.height = size * dpr
    ctx.scale(dpr, dpr)

    // Particle system for floating fluid luminescence
    const particleCount = 28
    const particles = Array.from({ length: particleCount }, () => ({
      angle: Math.random() * Math.PI * 2,
      distance: 0.6 + Math.random() * 0.7,
      speed: (0.2 + Math.random() * 0.5) * (Math.random() > 0.5 ? 1 : -1),
      size: 1.5 + Math.random() * 2.5,
      alpha: 0.2 + Math.random() * 0.6,
      pulseSpeed: 1 + Math.random() * 2,
    }))

    const render = () => {
      timeRef.current += 0.016
      const t = timeRef.current

      // Smooth audio level
      const targetLevel = state === 'speaking' ? Math.max(audioLevel, 0.45 + Math.sin(t * 8) * 0.25)
                        : state === 'listening' ? Math.max(audioLevel, 0.35 + Math.sin(t * 12) * 0.2)
                        : state === 'thinking' ? 0.25 + Math.sin(t * 10) * 0.15
                        : 0.05 + Math.sin(t * 2) * 0.03
      smoothedLevelRef.current += (targetLevel - smoothedLevelRef.current) * 0.12
      const level = smoothedLevelRef.current

      ctx.clearRect(0, 0, size, size)

      const cx = size / 2
      const cy = size / 2
      const baseRadius = size * 0.3

      // 1. Ambient Outer Caustic Glow
      const ambientGlowRadius = baseRadius * (1.4 + level * 0.5)
      const glowGrad = ctx.createRadialGradient(cx, cy, baseRadius * 0.2, cx, cy, ambientGlowRadius)
      if (state === 'speaking') {
        glowGrad.addColorStop(0, 'rgba(6, 182, 212, 0.45)')
        glowGrad.addColorStop(0.5, 'rgba(168, 85, 247, 0.25)')
        glowGrad.addColorStop(1, 'rgba(6, 182, 212, 0)')
      } else if (state === 'listening') {
        glowGrad.addColorStop(0, 'rgba(16, 185, 129, 0.5)')
        glowGrad.addColorStop(0.5, 'rgba(6, 182, 212, 0.25)')
        glowGrad.addColorStop(1, 'rgba(16, 185, 129, 0)')
      } else if (state === 'connecting' || state === 'thinking') {
        glowGrad.addColorStop(0, 'rgba(236, 72, 153, 0.4)')
        glowGrad.addColorStop(0.5, 'rgba(139, 92, 246, 0.25)')
        glowGrad.addColorStop(1, 'rgba(99, 102, 241, 0)')
      } else {
        glowGrad.addColorStop(0, 'rgba(14, 165, 233, 0.25)')
        glowGrad.addColorStop(0.6, 'rgba(99, 102, 241, 0.12)')
        glowGrad.addColorStop(1, 'rgba(14, 165, 233, 0)')
      }

      ctx.save()
      ctx.fillStyle = glowGrad
      ctx.beginPath()
      ctx.arc(cx, cy, ambientGlowRadius, 0, Math.PI * 2)
      ctx.fill()
      ctx.restore()

      // 2. Outward Acoustic Pressure Rings (when active)
      if (state === 'speaking' || state === 'listening') {
        const ringCount = 2
        for (let r = 0; r < ringCount; r++) {
          const ringProgress = (t * 0.7 + r / ringCount) % 1
          const ringRadius = baseRadius * (1.1 + ringProgress * 0.8)
          const ringAlpha = (1 - ringProgress) * (0.35 + level * 0.4)
          ctx.save()
          ctx.strokeStyle = state === 'speaking'
            ? `rgba(56, 189, 248, ${ringAlpha})`
            : `rgba(52, 211, 153, ${ringAlpha})`
          ctx.lineWidth = 1.5
          ctx.beginPath()
          ctx.arc(cx, cy, ringRadius, 0, Math.PI * 2)
          ctx.stroke()
          ctx.restore()
        }
      }

      // 3. Floating Luminescent Orbital Sparks
      particles.forEach((p) => {
        p.angle += p.speed * 0.02 * (1 + level * 2)
        const pr = baseRadius * (p.distance + Math.sin(t * p.pulseSpeed) * 0.08)
        const px = cx + Math.cos(p.angle) * pr
        const py = cy + Math.sin(p.angle) * pr
        const pAlpha = p.alpha * (0.4 + level * 0.6)

        ctx.save()
        ctx.fillStyle = state === 'listening'
          ? `rgba(110, 231, 183, ${pAlpha})`
          : `rgba(186, 230, 253, ${pAlpha})`
        ctx.shadowColor = '#38bdf8'
        ctx.shadowBlur = 8
        ctx.beginPath()
        ctx.arc(px, py, p.size * (1 + level * 0.5), 0, Math.PI * 2)
        ctx.fill()
        ctx.restore()
      })

      // 4. Liquid Surface Harmonic Deformations (Metaball Fluid Body)
      const numPoints = 120
      const points: { x: number; y: number }[] = []
      const speedMult = state === 'connecting' || state === 'thinking' ? 3.0
                      : state === 'speaking' ? 2.2
                      : state === 'listening' ? 1.8
                      : 0.9

      const deformAmplitude = baseRadius * (0.07 + level * 0.22)

      for (let i = 0; i < numPoints; i++) {
        const angle = (i / numPoints) * Math.PI * 2
        // Organic multi-octave harmonic wave equation
        const wave1 = Math.sin(angle * 3 + t * speedMult) * deformAmplitude * 0.6
        const wave2 = Math.cos(angle * 5 - t * speedMult * 1.3) * deformAmplitude * 0.3
        const wave3 = Math.sin(angle * 2 + t * speedMult * 0.7) * deformAmplitude * 0.25
        const r = baseRadius + wave1 + wave2 + wave3

        points.push({
          x: cx + Math.cos(angle) * r,
          y: cy + Math.sin(angle) * r,
        })
      }

      // Draw Main Liquid Blob with Spline Smoothing
      ctx.save()
      ctx.beginPath()
      ctx.moveTo((points[0].x + points[numPoints - 1].x) / 2, (points[0].y + points[numPoints - 1].y) / 2)
      for (let i = 0; i < numPoints; i++) {
        const p1 = points[i]
        const p2 = points[(i + 1) % numPoints]
        const midX = (p1.x + p2.x) / 2
        const midY = (p1.y + p2.y) / 2
        ctx.quadraticCurveTo(p1.x, p1.y, midX, midY)
      }
      ctx.closePath()

      // Gradient Fill (Iridescent Chromatic Refraction)
      const grad = ctx.createLinearGradient(
        cx - baseRadius * 0.8,
        cy - baseRadius * 0.8,
        cx + baseRadius * 0.8,
        cy + baseRadius * 0.8
      )

      if (state === 'speaking') {
        grad.addColorStop(0, '#38bdf8')
        grad.addColorStop(0.35, '#06b6d4')
        grad.addColorStop(0.7, '#8b5cf6')
        grad.addColorStop(1, '#ec4899')
      } else if (state === 'listening') {
        grad.addColorStop(0, '#6ee7b7')
        grad.addColorStop(0.4, '#10b981')
        grad.addColorStop(0.75, '#06b6d4')
        grad.addColorStop(1, '#3b82f6')
      } else if (state === 'connecting' || state === 'thinking') {
        grad.addColorStop(0, '#f472b6')
        grad.addColorStop(0.4, '#a855f7')
        grad.addColorStop(0.75, '#6366f1')
        grad.addColorStop(1, '#06b6d4')
      } else {
        // Idle
        grad.addColorStop(0, '#38bdf8')
        grad.addColorStop(0.45, '#0284c7')
        grad.addColorStop(0.8, '#4f46e5')
        grad.addColorStop(1, '#1e1b4b')
      }

      ctx.fillStyle = grad
      ctx.shadowColor = state === 'listening' ? '#10b981' : '#06b6d4'
      ctx.shadowBlur = 25 + level * 30
      ctx.fill()

      // Edge Specular Rim Highlight
      ctx.lineWidth = 2 + level * 2
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)'
      ctx.stroke()
      ctx.restore()

      // 5. Liquid Inner Specular Light Glint
      const glintX = cx - baseRadius * 0.32 + Math.sin(t * speedMult * 0.5) * (baseRadius * 0.08)
      const glintY = cy - baseRadius * 0.35 + Math.cos(t * speedMult * 0.5) * (baseRadius * 0.08)
      const glintRadius = baseRadius * 0.38
      const glintGrad = ctx.createRadialGradient(glintX, glintY, 0, glintX, glintY, glintRadius)
      glintGrad.addColorStop(0, 'rgba(255, 255, 255, 0.65)')
      glintGrad.addColorStop(0.5, 'rgba(255, 255, 255, 0.15)')
      glintGrad.addColorStop(1, 'rgba(255, 255, 255, 0)')

      ctx.save()
      ctx.fillStyle = glintGrad
      ctx.beginPath()
      ctx.arc(glintX, glintY, glintRadius, 0, Math.PI * 2)
      ctx.fill()
      ctx.restore()

      // 6. Secondary Inner Core Pulsation
      const innerCoreRadius = baseRadius * (0.35 + Math.sin(t * 3) * 0.05 + level * 0.1)
      const innerGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, innerCoreRadius)
      innerGrad.addColorStop(0, 'rgba(255, 255, 255, 0.85)')
      innerGrad.addColorStop(0.4, 'rgba(224, 242, 254, 0.4)')
      innerGrad.addColorStop(1, 'rgba(255, 255, 255, 0)')

      ctx.save()
      ctx.fillStyle = innerGrad
      ctx.beginPath()
      ctx.arc(cx, cy, innerCoreRadius, 0, Math.PI * 2)
      ctx.fill()
      ctx.restore()

      animFrameRef.current = requestAnimationFrame(render)
    }

    render()

    return () => {
      cancelAnimationFrame(animFrameRef.current)
    }
  }, [state, audioLevel, size])

  return (
    <div
      className={`lumora-orb-container ${state} ${className}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      aria-label={`AI Voice Orb, current status: ${state}`}
      style={{ width: size, height: size, position: 'relative', cursor: onClick ? 'pointer' : 'default' }}
    >
      <canvas ref={canvasRef} style={{ width: size, height: size, display: 'block' }} />
      <div className="orb-center-badge">
        {state === 'connecting' && <span className="orb-status-text">CONNECTING…</span>}
        {state === 'thinking' && <span className="orb-status-text">THINKING…</span>}
        {state === 'speaking' && <span className="orb-status-text">SPEAKING</span>}
        {state === 'listening' && <span className="orb-status-text">LISTENING</span>}
        {state === 'idle' && <span className="orb-status-text">READY</span>}
      </div>
    </div>
  )
}
export default LiquidVoiceOrb

