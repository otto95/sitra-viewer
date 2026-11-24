import { useEffect, useState } from 'react'
import './App.css'

type ApiState = 'checking' | 'connected' | 'unavailable'

function App() {
  const [apiState, setApiState] = useState<ApiState>('checking')

  useEffect(() => {
    fetch('/api/health')
      .then((response) => {
        if (!response.ok) throw new Error('API unavailable')
        return response.json()
      })
      .then(() => setApiState('connected'))
      .catch(() => setApiState('unavailable'))
  }, [])

  const statusLabel = {
    checking: 'Checking connection',
    connected: 'API connected',
    unavailable: 'API unavailable',
  }[apiState]

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="SITRA home">
          <span className="brand-mark" aria-hidden="true">S</span>
          <span className="brand-name">SITRA<span> / </span>VIEWER</span>
        </a>
        <span className="topbar-note">NATIONAL ARCHIVES · RECORD GROUP 218</span>
      </header>

      <section className="intro" aria-labelledby="page-title">
        <p className="eyebrow">SITUATION REPORT ARMY <span>·</span> NAID 604416</p>
        <h1 id="page-title">Ground combat operations<br />in Vietnam, 1966–1973</h1>
        <p className="intro-copy">
          A focused explorer for the National Archives’ Situation Report Army records.
        </p>

        <div className="foundation-card">
          <div className="archive-stamp" aria-hidden="true">RG<br />218</div>
          <div className="foundation-copy">
            <p className="card-label">Project foundation</p>
            <h2>Building the archive explorer</h2>
            <p>Search, map, timeline, and record connections are coming in the next phases.</p>
          </div>
          <div className={`api-status api-status--${apiState}`} role="status" aria-live="polite">
            <span className="status-dot" />
            {statusLabel}
          </div>
        </div>
      </section>

      <footer className="page-footer">
        <span>DATA SOURCE <strong>U.S. National Archives</strong></span>
        <span>COLLECTION DATES <strong>1966—1973</strong></span>
      </footer>
    </main>
  )
}

export default App
