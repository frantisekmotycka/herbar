import Link from 'next/link'

export default function HerbCard({ herb }) {
  const img = (herb.images && herb.images[0] && (herb.images[0].thumb_url || herb.images[0].file_url)) || null
  return (
    <Link href={`/herb/${encodeURIComponent(herb.id)}`}>
      <article style={{ border: '1px solid #eee', padding: 12, borderRadius: 8, textDecoration: 'none', color: 'inherit', cursor: 'pointer' }}>
        <div style={{ height: 120, background: '#fafafa', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 8, overflow: 'hidden', borderRadius: 6 }}>
          {img ? <img src={img} alt={herb.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : <div style={{ color: '#999' }}>No image</div>}
        </div>
        <h3 style={{ margin: '6px 0' }}>{herb.name}</h3>
        <p style={{ margin: 0, color: '#555', fontSize: 14 }}>{herb.summary || ''}</p>
      </article>
    </Link>
  )
}
