import { useState } from 'react'
import Dashboard from './Dashboard'
import VoicePanel from './VoicePanel'

type Page = 'voice' | 'evaluations'

export default function App() {
  const [page, setPage] = useState<Page>('voice')

  return (
    <div className="app-shell">
      {/* Top Banner for Clinical Safety */}
      <div className="emergency-banner" role="complementary">
        <span className="banner-content">
          <strong className="badge-alert">CLINICAL NOTICE</strong>
          If you are experiencing acute chest pain, shortness of breath, or a medical emergency, please dial <strong>911</strong> immediately.
        </span>
      </div>

      {/* Main Topbar */}
      <header className="topbar">
        <a className="brand" href="#home" onClick={(e) => { e.preventDefault(); setPage('voice') }} aria-label="Serenity Clinic home">
          <div className="brand-mark">
            <svg viewBox="0 0 32 32" aria-hidden="true">
              <path d="M14 5h4v9h9v4h-9v9h-4v-9H5v-4h9z" />
            </svg>
          </div>
          <div>
            <strong>Serenity</strong>
            <small>MEDICAL CLINIC • LUMORA AI</small>
          </div>
        </a>

        {/* Navigation Switcher */}
        <nav className="nav-tabs" aria-label="Main navigation">
          <button
            className={page === 'voice' ? 'active' : ''}
            onClick={() => setPage('voice')}
            id="tab-voice"
          >
            ✦ Voice Receptionist
          </button>
          <button
            className={page === 'evaluations' ? 'active' : ''}
            onClick={() => setPage('evaluations')}
            id="tab-evals"
          >
            📊 Evaluation & Analytics
          </button>
        </nav>

        {/* System & Pipeline Status Badges */}
        <div className="topbar-right">
          <div className="pipeline-pill" title="LiveKit WebRTC + Google Gemini + Deepgram Nova-2 + ElevenLabs Bella">
            <span className="status-dot online" />
            <span>AI Voice Cloud Live</span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main>
        <div className="page-intro">
          <div>
            <span className="eyebrow">
              <span className="eyebrow-dot" />
              {page === 'voice' ? 'AUTONOMOUS CLINIC RECEPTIONIST' : 'EVALUATION ENGINE & METRICS'}
            </span>
            <h1>
              {page === 'voice'
                ? 'Talk with Rachel, your AI Receptionist.'
                : 'Autonomous Benchmark & Quality Suite.'}
            </h1>
            <p>
              {page === 'voice'
                ? 'Speak naturally to check doctor schedules, book or reschedule appointments, and get instant answers about clinic services.'
                : 'Deterministic multi-turn simulated patient evaluations scoring task outcomes, safety guardrails, and tool execution.'}
            </p>
          </div>
        </div>

        {page === 'voice' ? <VoicePanel /> : <Dashboard />}
      </main>

      {/* Footer */}
      <footer>
        <div className="footer-left">
          <span>© 2026 Serenity Medical Clinic. All rights reserved.</span>
          <span className="footer-sep">•</span>
          <span>HIPAA & Privacy Guardrails Active</span>
        </div>
        <div className="footer-right">
          <span className="footer-tech">Engineered with LiveKit WebRTC, Gemini, Deepgram & ElevenLabs</span>
        </div>
      </footer>
    </div>
  )
}
