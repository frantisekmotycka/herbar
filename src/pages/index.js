import Link from 'next/link'
import { useState, useMemo } from 'react'
import HerbCard from '../../components/HerbCard'
import SearchBar from '../../components/SearchBar'

export default function Home({ herbs }) {
  const [query, setQuery] = useState('')
  const [tag, setTag] = useState('')

  const availableTags = useMemo(() => {
    const s = new Set()
    herbs.forEach(h => (h.tags || []).forEach(t => s.add(t)))
    return Array.from(s).sort()
  }, [herbs])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return herbs.filter(h => {
      if (tag) {
        const tags = (h.tags || [])
        if (!tags.includes(tag)) return false
      }
      if (!q) return true
      const hay = (h.name + ' ' + (h.summary||'')).toLowerCase()
      return hay.includes(q)
    })
  }, [herbs, query, tag])

  return (
    <main style={{ padding: 20, fontFamily: 'system-ui, Arial' }}>
      <h1>Herbář — seznam bylinek</h1>

      <p style={{ maxWidth: 800, lineHeight: 1.5, color: '#333' }}>
        Tento jednoduchý herbář shromažďuje základní informace o běžných bylinkách: názvy, krátké shrnutí,
        použití a odkazy na zdroje. Data jsou sbírána z veřejně dostupných zdrojů a mohou obsahovat
        neúplné nebo chybějící položky — pokud máte doplňující informace nebo lepší zdroje, přispějte prosím.
      </p>

      <p style={{ maxWidth: 800, lineHeight: 1.5, color: '#333' }}>
        Použijte vyhledávací pole níže pro rychlé filtrování podle názvu nebo klíčového slova. Kliknutím na konkrétní
        položku zobrazíte detail s popisem, informacemi o použití a odkazy na Wikipedii či původní zdroj.
      </p>

      <SearchBar value={query} onChange={setQuery} tag={tag} onTagChange={setTag} tags={availableTags} />

      <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: 16 }}>
        {filtered.map(h => (
          <HerbCard key={h.id} herb={h} />
        ))}
      </div>
      <footer style={{ marginTop: 28, borderTop: '1px solid #eee', paddingTop: 12, color: '#555' }}>
        <div style={{ maxWidth: 900 }}>
          <strong>O projektu:</strong> Tento projekt je jednoduchý referenční herbář. Více informací najdete v
          souboru README nebo v repozitáři projektu.
        </div>
      </footer>
    </main>
  )
}

export async function getStaticProps() {
  const fs = require('fs')
  const path = require('path')
  const dataPath = path.join(process.cwd(), 'data', 'herbs.json')
  const raw = fs.readFileSync(dataPath, 'utf8')
  const herbs = JSON.parse(raw)
  return { props: { herbs } }
}
