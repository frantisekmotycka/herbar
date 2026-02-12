// Minimal server-safe HTML sanitizer.
// Removes script/style/iframe/object/embed tags and strips on* attributes and javascript: URIs.
// Not a full replacement for a robust library, but safe for our scraped content.
function stripTags(html, tags) {
  for (const t of tags) {
    const re = new RegExp(`<${t}[^>]*>[\s\S]*?<\/${t}>`, 'gi')
    html = html.replace(re, '')
  }
  return html
}

function stripAttrs(html) {
  // remove on* attributes (onclick, onerror, etc.)
  html = html.replace(/\son[a-z]+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi, '')
  // remove javascript: URIs in href/src
  html = html.replace(/(href|src)\s*=\s*(["'])\s*javascript:[^\2]*\2/gi, '$1=$2#$2')
  return html
}

function sanitizeHtml(input) {
  if (!input) return ''
  let s = String(input)
  // strip dangerous tags first
  s = stripTags(s, ['script', 'style', 'iframe', 'object', 'embed'])
  // remove event attributes and javascript: URIs
  s = stripAttrs(s)
  // collapse excessive whitespace
  s = s.replace(/\s{2,}/g, ' ')
  return s
}

module.exports = { sanitizeHtml }
