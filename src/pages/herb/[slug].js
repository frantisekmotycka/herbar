// `fs` and `path` are only needed server-side inside data-loading functions
import Image from 'next/image'
const { sanitizeHtml } = require('../../../lib/sanitizeHtml')

export default function HerbDetail({ herb }) {
  if (!herb) return <div style={{ padding: 20 }}>Bylinka nenalezena</div>
  const img = (herb.images && herb.images[0] && (herb.images[0].thumb_url || herb.images[0].file_url)) || null
  return (
    <main className="herb-detail" style={{ padding: 20, fontFamily: 'system-ui, Arial' }}>
      <p><a href="/">← Zpět na seznam</a></p>
      <div className="grid" style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 24, alignItems: 'start' }}>
        <div>
          <h1 style={{ marginTop: 0 }}>{herb.name}</h1>
          {herb.summary && <p style={{ marginTop: 6 }}>{herb.summary}</p>}

          {/* Ordered section rendering: show requested sections in order and fallbacks */}
          {(() => {
            const sections = herb.sections || {}
            const keys = Object.keys(sections)

            const target = ['Popis', 'Použití', 'Pěstování', 'Léčivé účinky', 'Složení', 'Sběr', 'Recepty']
            const used = new Set()
            const out = []

            const findKey = token => keys.find(k => k.toLowerCase().includes(token.toLowerCase()))

            for (const t of target) {
              const k = findKey(t)
              if (k && !used.has(k)) {
                used.add(k)
                out.push([t, sanitizeHtml(sections[k])])
              } else {
                out.push([t, null])
              }
            }

            // append remaining keys not already used
            for (const k of keys) {
              if (!used.has(k)) {
                used.add(k)
                out.push([k, sanitizeHtml(sections[k])])
              }
            }

            return (
              <div style={{ marginTop: 18 }}>
                {out.map(([title, content]) => (
                  <section key={title} style={{ marginBottom: 18 }}>
                    <h2 style={{ marginBottom: 6 }}>{title}</h2>
                    {content ? (
                      <div dangerouslySetInnerHTML={{ __html: content }} />
                    ) : (
                      <div style={{ fontStyle: 'italic', color: '#666' }}>
                        Informace pro tuto sekci zatím nejsou k dispozici. Pokud máte ověřený zdroj nebo poznatek,
                        pomozte projekt doplnit — můžete upravit data v repozitáři nebo nahlásit zdroj.
                      </div>
                    )}
                  </section>
                ))}
              </div>
            )
          })()}
        </div>

        <aside className="infobox" style={{ border: '1px solid #eee', padding: 12, borderRadius: 8 }}>
          <h3 style={{ marginTop: 0 }}>Informace</h3>
          {herb.name && <div><strong>Název:</strong> {herb.name}</div>}
          {herb.other_names && <div><strong>Další názvy:</strong> {(herb.other_names||[]).join(', ')}</div>}
          {herb.latin && <div><strong>Latinsky:</strong> {herb.latin}</div>}
            {img ? (
              <div style={{ width: 200, marginBottom: 8 }}>
                <img src={img} alt={herb.name} style={{ width: '100%', height: 'auto', borderRadius: 6 }} />
              </div>
            ) : null}
            {herb.wikipedia_url ? (
              <div style={{ marginTop: 8 }}><a href={herb.wikipedia_url} target="_blank" rel="noopener noreferrer">Wikipedie</a></div>
            ) : (
              <div style={{ marginTop: 8, color: '#888', fontSize: 13 }}>Wikipedie: nenalezena</div>
            )}
          {herb.source_url && <div style={{ marginTop: 8 }}><a href={herb.source_url} target="_blank" rel="noopener noreferrer">Zobrazit zdroj</a></div>}
          {herb.license && <div style={{ marginTop: 8, fontSize: 13, color: '#666' }}>Licence: {herb.license}</div>}
        </aside>
      </div>
    </main>
  )
}

export async function getStaticPaths() {
  const fs = require('fs')
  const path = require('path')
  const dataPath = path.join(process.cwd(), 'data', 'herbs.json')
  const raw = fs.readFileSync(dataPath, 'utf8')
  const herbs = JSON.parse(raw)
  const paths = herbs.map(h => ({ params: { slug: h.id } }))
  return { paths, fallback: false }
}

export async function getStaticProps({ params }) {
  const fs = require('fs')
  const path = require('path')
  const dataPath = path.join(process.cwd(), 'data', 'herbs.json')
  const raw = fs.readFileSync(dataPath, 'utf8')
  const herbs = JSON.parse(raw)
  const herb = herbs.find(h => h.id === params.slug) || null
  // attempt to find a Wikipedia page (cs then en)
  if (herb && !herb.wikipedia_url) {
    const tryUrls = []
    const nameCandidate = encodeURIComponent(herb.name.replace(/\s+/g, '_'))
    const idCandidate = encodeURIComponent(herb.id.replace(/\s+/g, '_'))
    tryUrls.push(`https://cs.wikipedia.org/wiki/${nameCandidate}`)
    if (idCandidate !== nameCandidate) tryUrls.push(`https://cs.wikipedia.org/wiki/${idCandidate}`)
    tryUrls.push(`https://en.wikipedia.org/wiki/${nameCandidate}`)

    for (const u of tryUrls) {
      try {
        const res = await fetch(u, { method: 'HEAD' })
        if (res && res.ok) {
          herb.wikipedia_url = u
          break
        }
      } catch (e) {
        // ignore network errors
      }
    }
  }

  return { props: { herb } }
}
