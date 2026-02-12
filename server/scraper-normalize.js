const diacritics = require('he').decode;

const mapping = {
  'zdravotní přínosy': 'zdravotni_prinosy',
  'zdravotni přínosy': 'zdravotni_prinosy',
  'skladování': 'skladovani',
  'skladovani': 'skladovani',
  'kde a kdy sbírat': 'kde_kdy_sbirat',
  'kde kdy sbírat': 'kde_kdy_sbirat',
  'použití v kuchyni': 'pouziti_v_kuchyni',
  'použiti v kuchyni': 'pouziti_v_kuchyni',
  'použití': 'pouziti_v_kuchyni',
  'masti': 'masti'
};

function normalizeHeading(text) {
  if (!text) return '';
  let t = text.toLowerCase();
  t = t.normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
  t = t.replace(/[\s\u00A0]+/g, ' ').trim();
  if (mapping[t]) return mapping[t];
  // fallback: convert to snake case ascii
  return t.replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
}

module.exports = { normalizeHeading };
