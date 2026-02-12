import { useState } from 'react'

export default function SearchBar({ value, onChange, tag, onTagChange, tags = [] }) {
  const [local, setLocal] = useState(value || '')

  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 12 }}>
      <input
        aria-label="Hledat"
        placeholder="Hledat podle názvu nebo popisu"
        value={local}
        onChange={e => { setLocal(e.target.value); onChange(e.target.value) }}
        style={{ flex: 1, padding: '8px 10px', borderRadius: 6, border: '1px solid #ddd' }}
      />
      <select value={tag} onChange={e => onTagChange(e.target.value)} style={{ padding: '8px', borderRadius: 6, border: '1px solid #ddd' }}>
        <option value=''>Všechny tagy</option>
        {tags.map(t => <option key={t} value={t}>{t}</option>)}
      </select>
    </div>
  )
}
