import { useState } from 'react'
import Dashboard from './Dashboard'
import VoicePanel from './VoicePanel'

type Page = 'voice' | 'evaluations'

export default function App() {
  const [page, setPage] = useState<Page>('voice')
  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#home" onClick={() => setPage('voice')} aria-label="Serenity Clinic home">
          <span className="brand-mark"><svg viewBox="0 0 32 32" aria-hidden="true"><path d="M14 5h4v9h9v4h-9v9h-4v-9H5v-4h9z" /></svg></span>
          <span><strong>Serenity</strong><small>MEDICAL CLINIC</small></span>
        </a>
        <nav className="nav-tabs" aria-label="Main navigation">
          <button className={page === 'voice' ? 'active' : ''} onClick={() => setPage('voice')}>Receptionist</button>
          <button className={page === 'evaluations' ? 'active' : ''} onClick={() => setPage('evaluations')}>Evaluations</button>
        </nav>
        <div className="clinic-status"><span className="status-dot online" />Clinic services</div>
      </header>
      <main>
        <div className="page-intro"><div><span className="eyebrow">YOUR CARE STARTS HERE</span><h1>{page === 'voice' ? 'How can we help today?' : 'A clearer view of agent quality.'}</h1><p>{page === 'voice' ? 'A simple way to get answers and arrange your next visit.' : 'Track task completion, tool use, and safety across patient scenarios.'}</p></div><div className="intro-art" aria-hidden="true"><span className="art-circle circle-back" /><span className="art-circle circle-front"><svg viewBox="0 0 80 80"><path d="M37 14h6v20h20v6H43v20h-6V40H17v-6h20z" /></svg></span></div></div>
        {page === 'voice' ? <VoicePanel /> : <Dashboard />}
      </main>
      <footer><span>© Serenity Medical Clinic</span><span>For emergencies, call 911</span></footer>
    </div>
  )
}
