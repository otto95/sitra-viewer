import { useEffect, useState } from 'react'
import { CircleMarker, MapContainer, TileLayer, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './App.css'

type RecordNode = {
  recordId: string
  reportDate?: string
  reportTypeLabel?: string
  reportType?: string
  latitude?: number
  longitude?: number
  sourceUtm?: string
  sourceMgrs?: string
  mgrsGzd?: string
  [key: string]: unknown
}
type SearchResponse = { items: { record: RecordNode; score: number }[]; total: number; offset: number; limit: number }
type RelatedItem = { record: RecordNode; status: 'possible' | 'definite'; origin: string; evidence: string[]; linkId?: string }
type Details = { record: RecordNode; fixedSets: Record<string, unknown>[]; periodicSets: Record<string, unknown>[] }
const PAGE_SIZE = 100

function dateLabel(value?: string) {
  if (!value) return 'Date not recorded'
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`))
}
function titleFor(record: RecordNode) {
  return String(record.reportTypeLabel || record.reportType || 'Situation report')
}

function App() {
  const [query, setQuery] = useState('')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [offset, setOffset] = useState(0)
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<RecordNode | null>(null)
  const [details, setDetails] = useState<Details | null>(null)
  const [related, setRelated] = useState<RelatedItem[]>([])
  const [detailBusy, setDetailBusy] = useState(false)
  const [promoting, setPromoting] = useState<string | null>(null)
  const openRecord = (record: RecordNode) => { setDetailBusy(true); setSelected(record) }

  useEffect(() => {
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      setBusy(true)
      setError('')
      const params = new URLSearchParams({ offset: String(offset), limit: String(PAGE_SIZE) })
      if (query.trim()) params.set('q', query.trim())
      if (from) params.set('from', from)
      if (to) params.set('to', to)
      fetch(`/api/records?${params}`, { signal: controller.signal })
        .then((response) => { if (!response.ok) throw new Error('Search could not be completed. Check the dates and try again.'); return response.json() as Promise<SearchResponse> })
        .then(setResults)
        .catch((reason: unknown) => { if (!(reason instanceof DOMException && reason.name === 'AbortError')) setError(reason instanceof Error ? reason.message : 'The archive could not be reached.') })
        .finally(() => { if (!controller.signal.aborted) setBusy(false) })
    }, 220)
    return () => { window.clearTimeout(timer); controller.abort() }
  }, [query, from, to, offset])

  const selectedRecordId = selected?.recordId
  useEffect(() => {
    if (!selectedRecordId) return
    const controller = new AbortController()
    Promise.all([
      fetch(`/api/records/${encodeURIComponent(selectedRecordId)}`, { signal: controller.signal }).then((response) => { if (!response.ok) throw new Error('Record details unavailable'); return response.json() as Promise<Details> }),
      fetch(`/api/records/${encodeURIComponent(selectedRecordId)}/related`, { signal: controller.signal }).then((response) => { if (!response.ok) throw new Error('Record connections unavailable'); return response.json() as Promise<{ items: RelatedItem[] }> }),
    ]).then(([recordDetails, recordLinks]) => { setDetails(recordDetails); setRelated(recordLinks.items) })
      .catch((reason: unknown) => { if (!(reason instanceof DOMException && reason.name === 'AbortError')) setError(reason instanceof Error ? reason.message : 'Record details unavailable.') })
      .finally(() => { if (!controller.signal.aborted) setDetailBusy(false) })
    return () => controller.abort()
  }, [selectedRecordId])

  const items = results?.items.map((item) => item.record) ?? []
  const located = items.filter((item) => typeof item.latitude === 'number' && typeof item.longitude === 'number')
  const dated = items.filter((item) => Boolean(item.reportDate)).sort((a, b) => (a.reportDate ?? '').localeCompare(b.reportDate ?? ''))
  const promotion = async (item: RelatedItem) => {
    if (!item.linkId) return
    setPromoting(item.linkId)
    try {
      const response = await fetch(`/api/links/${encodeURIComponent(item.linkId)}/promote`, { method: 'POST' })
      if (!response.ok) throw new Error('Could not update this connection.')
      setRelated((current) => current.map((link) => link.linkId === item.linkId ? { ...link, status: 'definite' } : link))
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not update this connection.') }
    finally { setPromoting(null) }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="SITRA Viewer home"><span className="brand-mark">S</span><span className="brand-name">SITRA <i>/</i> VIEWER</span></a>
        <div className="collection-tag"><span className="live-dot" /> NATIONAL ARCHIVES <b>·</b> RECORD GROUP 218</div>
      </header>

      <section className="workspace">
        <div className="intro-row">
          <div><p className="eyebrow">SITUATION REPORT ARMY <span>·</span> NAID 604416</p><h1>Ground operations,<br className="title-break" /> seen in the record.</h1></div>
          <p className="intro-note">Explore Army situation reports from<br />Vietnam, 1966–1973.</p>
        </div>

        <section className="search-panel" aria-label="Search and filter records">
          <label className="search-field"><span className="search-icon" aria-hidden="true">⌕</span><span className="sr-only">Search archive records</span><input value={query} onChange={(event) => { setOffset(0); setQuery(event.target.value) }} placeholder="Search units, places, operations, or report text" /></label>
          <div className="date-filter"><span className="filter-label">MESSAGE DATE</span><label><span className="sr-only">From date</span><input type="date" value={from} min="1965-01-01" max="1973-12-31" onChange={(event) => { setOffset(0); setFrom(event.target.value) }} /></label><span className="date-dash">—</span><label><span className="sr-only">To date</span><input type="date" value={to} min="1965-01-01" max="1973-12-31" onChange={(event) => { setOffset(0); setTo(event.target.value) }} /></label></div>
          {(query || from || to) && <button className="clear-button" onClick={() => { setQuery(''); setFrom(''); setTo(''); setOffset(0) }}>Clear</button>}
        </section>

        <div className="results-heading"><div><span className="section-kicker">ARCHIVE EXPLORER</span><h2>Records <span className="result-count">{busy ? '…' : (results?.total ?? 0).toLocaleString()}</span></h2></div><span className="page-indicator">{results && results.total > 0 ? `${offset + 1}–${Math.min(offset + PAGE_SIZE, results.total)} of ${results.total.toLocaleString()}` : 'MESSAGE DATE · 1966–1973'}</span></div>
        {error && <div className="notice error-notice" role="alert">{error}</div>}
        {busy && !results ? <div className="loading-state" role="status">Opening the archive index…</div> : null}
        {!busy && results?.total === 0 && <div className="empty-state"><span className="empty-mark">∅</span><h3>No reports match these filters</h3><p>Try a broader search or a wider date range.</p></div>}

        {(results && results.total > 0) && <>
          <div className="overview-grid">
            <section className="panel map-panel" aria-labelledby="map-title"><div className="panel-heading"><div><span className="section-kicker">GEOGRAPHY</span><h3 id="map-title">Field locations</h3></div><span className="panel-count">{located.length} LOCATED</span></div>
              <div className="map-frame"><MapContainer center={[16.7, 106.5]} zoom={5} scrollWheelZoom={false} className="archive-map"><TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                {located.map((record) => <MapPin key={record.recordId} record={record} onSelect={() => openRecord(record)} />)}
              </MapContainer>
                {located.length === 0 && <div className="map-empty">No mapped coordinates in this result page</div>}
              </div><div className="map-legend"><span><i /> Report location</span><span>Map shows records on this page</span></div>
            </section>
            <section className="panel timeline-panel" aria-labelledby="timeline-title"><div className="panel-heading"><div><span className="section-kicker">CHRONOLOGY</span><h3 id="timeline-title">Message dates</h3></div><span className="panel-count">{dated.length} DATED</span></div>
              {dated.length ? <div className="timeline-plot"><div className="timeline-axis"><span>{dated[0].reportDate?.slice(0, 4)}</span><span>{dated[Math.floor(dated.length / 2)].reportDate?.slice(0, 4)}</span><span>{dated[dated.length - 1].reportDate?.slice(0, 4)}</span></div><div className="timeline-track" aria-label="Records plotted by message date">{dated.map((record, index) => <button key={record.recordId} className={`timeline-point${selected?.recordId === record.recordId ? ' is-selected' : ''}`} style={{ left: `${dated.length === 1 ? 50 : (index / (dated.length - 1)) * 100}%`, top: `${22 + ((index * 37) % 47)}%` }} aria-label={`${dateLabel(record.reportDate)} — ${record.recordId}`} onClick={() => openRecord(record)}><span className="timeline-tooltip">{dateLabel(record.reportDate)}<br />{record.recordId}</span></button>)}</div><div className="timeline-rule" /><p className="timeline-hint">Select a point to inspect its record</p></div> : <div className="timeline-empty">No message dates in this result page</div>}
            </section>
          </div>

          <section className="records-section" aria-labelledby="records-title"><div className="list-heading"><div><span className="section-kicker">MATCHING ARCHIVAL ITEMS</span><h3 id="records-title">Record index</h3></div><span className="sort-note">ORDERED BY MESSAGE DATE</span></div>
            <div className="record-list">{items.map((record, index) => <button className={`record-row${selected?.recordId === record.recordId ? ' is-active' : ''}`} key={record.recordId} onClick={() => openRecord(record)}><span className="row-number">{String(offset + index + 1).padStart(3, '0')}</span><span className="record-main"><span className="record-title">{titleFor(record)}</span><span className="record-id">{record.recordId}</span></span><span className="record-date">{dateLabel(record.reportDate)}</span><span className="record-place">{String(record.prvc1Label || record.prvc1 || record.sourceMgrs || (record.latitude ? `${Number(record.latitude).toFixed(2)}°, ${Number(record.longitude).toFixed(2)}°` : 'Location not mapped'))}</span><span className="row-arrow" aria-hidden="true">↗</span></button>)}</div>
            <div className="pagination"><span>{results?.total.toLocaleString()} records in current search</span><div><button disabled={offset === 0 || busy} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>← Previous</button><button disabled={offset + PAGE_SIZE >= (results?.total ?? 0) || busy} onClick={() => setOffset(offset + PAGE_SIZE)}>Next →</button></div></div>
          </section>
        </>}
        <footer className="page-footer"><span>DATA SOURCE <strong>U.S. NATIONAL ARCHIVES</strong></span><span>COLLECTION DATES <strong>1966—1973</strong></span><span>SITRA <strong>RECORD GROUP 218</strong></span></footer>
      </section>

      {selected && <div className="drawer-scrim" onClick={() => setSelected(null)}><aside className="detail-drawer" aria-label="Record details" onClick={(event) => event.stopPropagation()}><div className="drawer-top"><span className="section-kicker">ARCHIVAL RECORD</span><button className="close-button" onClick={() => setSelected(null)} aria-label="Close record details">×</button></div><p className="drawer-date">{dateLabel(selected.reportDate)}</p><h2 className="drawer-title">{titleFor(selected)}</h2><p className="drawer-id">{selected.recordId}</p>
        {detailBusy ? <div className="drawer-loading">Loading record and connections…</div> : <>
          <div className="detail-facts"><Fact label="Message date" value={dateLabel(details?.record.reportDate ?? selected.reportDate)} /><Fact label="Grid reference" value={String(details?.record.sourceMgrs || selected.sourceMgrs || details?.record.sourceUtm || selected.sourceUtm || 'Not recorded')} /><Fact label="Report type" value={titleFor(details?.record ?? selected)} /></div>
          <div className="network-heading"><div><span className="section-kicker">ASSOCIATIONS</span><h3>Connected records</h3></div><span className="panel-count">{related.length} LINKS</span></div>
          <NetworkGraph current={selected} links={related} onSelect={openRecord} />
          {related.length === 0 ? <p className="no-links">No associated records are recorded for this item.</p> : <div className="related-list">{related.map((item) => <div className="related-row" key={item.record.recordId}><button className="related-name" onClick={() => openRecord(item.record)}><span>{item.record.recordId}</span><small>{dateLabel(item.record.reportDate)}</small></button><div className="related-status"><span className={`status-chip status-chip--${item.status}`}>{item.status === 'possible' ? 'Possible link' : 'Definite link'}</span>{item.status === 'possible' && item.linkId && <button className="promote-button" disabled={promoting === item.linkId} onClick={() => void promotion(item)}>{promoting === item.linkId ? 'Saving…' : 'Confirm link'}</button>}</div><p className="evidence-copy">{item.evidence.map((value) => value.replaceAll('_', ' ')).join(' · ')}</p></div>)}</div>}
          <div className="drawer-footnote">Possible links are inferred from shared source metadata. Confirming a link marks it definite.</div>
        </>}</aside></div>}
    </main>
  )
}

function MapPin({ record, onSelect }: { record: RecordNode; onSelect: () => void }) {
  return <CircleMarker center={[record.latitude as number, record.longitude as number]} radius={7} pathOptions={{ color: '#f3f0e6', weight: 2, fillColor: '#556b2f', fillOpacity: 0.95 }} eventHandlers={{ click: onSelect }}><Tooltip>{record.recordId}<br />{dateLabel(record.reportDate)}</Tooltip></CircleMarker>
}
function Fact({ label, value }: { label: string; value: string }) { return <div className="fact"><span>{label}</span><strong>{value}</strong></div> }
function NetworkGraph({ current, links, onSelect }: { current: RecordNode; links: RelatedItem[]; onSelect: (record: RecordNode) => void }) {
  const displayed = links.slice(0, 8)
  const cx = 170; const cy = 118
  return <div className="network-graph"><svg viewBox="0 0 340 236" role="img" aria-label={`${current.recordId}: ${links.length} connected records, ${links.filter((link) => link.status === 'possible').length} possible links`}>
    {displayed.map((link, index) => { const angle = (-Math.PI / 2) + (index / Math.max(displayed.length, 1)) * Math.PI * 2; const x = cx + Math.cos(angle) * 112; const y = cy + Math.sin(angle) * 76; return <g key={link.record.recordId}><line x1={cx} y1={cy} x2={x} y2={y} className={`graph-edge graph-edge--${link.status}`} /><circle cx={x} cy={y} r="19" className={`graph-node graph-node--${link.status}`} role="button" tabIndex={0} aria-label={`${link.status} link to ${link.record.recordId}`} onClick={() => onSelect(link.record)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') onSelect(link.record) }} /><text x={x} y={y + 34} textAnchor="middle" className="graph-label">{link.record.recordId.split(':').at(-1)}</text></g> })}
    <circle cx={cx} cy={cy} r="27" className="graph-center" /><text x={cx} y={cy + 4} textAnchor="middle" className="graph-center-label">THIS</text>
  </svg><div className="graph-legend"><span><i className="legend-definite" /> Definite</span><span><i className="legend-possible" /> Possible</span>{links.length > 8 && <span>+ {links.length - 8} more below</span>}</div></div>
}

export default App
