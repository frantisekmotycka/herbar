const axios = require('axios');
const cheerio = require('cheerio');
const { getCrawlDelay } = require('./utils/robots-checker');
const { normalizeHeading } = require('./scraper-normalize');
const path = require('path');

const BASE = 'https://www.wikifood.cz';

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function resolveUrl(u) {
  if (!u) return null;
  if (u.startsWith('http')) return u;
  if (u.startsWith('//')) return 'https:' + u;
  return BASE + (u.startsWith('/') ? u : '/' + u);
}

async function fetchHtml(url) {
  const res = await axios.get(url, { headers: { 'User-Agent': 'herbar-scraper/0.1 (+https://example.org)' } });
  return res.data;
}

async function parseHerbPage(url) {
  const html = await fetchHtml(url);
  const $ = cheerio.load(html);
  const title = $('#firstHeading').text().trim();
  const firstP = $('#mw-content-text .mw-parser-output > p').not('.mw-empty-elt').first().text().trim();

  // images
  const imageAnchor = $('#mw-content-text .mw-parser-output a.image').first();
  const thumbImg = imageAnchor.find('img').first().attr('src') || null;
  const imagePageHref = imageAnchor.attr('href') ? resolveUrl(imageAnchor.attr('href')) : null;

  // sections
  const sections = {};
  $('#mw-content-text .mw-parser-output').find('h2, h3').each((i, el) => {
    const headline = $(el).find('.mw-headline').text().trim();
    if (!headline) return;
    const key = normalizeHeading(headline);
    let content = '';
    // collect until next h2/h3
    let node = $(el).next();
    while (node.length && !['h2','h3'].includes(node[0].name)) {
      content += (node.text() || '') + '\n';
      node = node.next();
    }
    sections[key] = content.trim();
  });

  return {
    source_url: url,
    name: title,
    summary: firstP || null,
    images: [{ page_url: imagePageHref, thumb_url: thumbImg ? resolveUrl(thumbImg) : null }],
    sections
  };
}

async function fetchFileOriginalUrl(filePageUrl) {
  if (!filePageUrl) return null;
  try {
    const html = await fetchHtml(filePageUrl);
    const $ = cheerio.load(html);
    // try to find original file link (href to /images/)
    const a = $('a[href*="/images/"]').first();
    if (a && a.attr('href')) return resolveUrl(a.attr('href'));
    // fallback: look for .fullImageLink
    const fb = $('.fullImageLink a').first();
    if (fb && fb.attr('href')) return resolveUrl(fb.attr('href'));
  } catch (e) {
    // ignore
  }
  return null;
}

async function fetchAllHerbs() {
  const categoryUrl = BASE + '/Kategorie:Bylinky';
  const delay = await getCrawlDelay(BASE);
  const html = await fetchHtml(categoryUrl);
  const $ = cheerio.load(html);

  // collect candidate links from content area
  const links = new Set();
  $('#mw-content-text .mw-parser-output a[href^="/"]').each((i, el) => {
    const href = $(el).attr('href');
    if (!href) return;
    // skip files and special namespaces
    if (href.includes(':')) return;
    // skip category index link to self
    if (href.startsWith('/Kategorie')) return;
    // simple heuristic: likely article pages have capitalized first char
    links.add(resolveUrl(href));
  });

  const linkList = Array.from(links).filter(u => u.startsWith(BASE + '/')).sort();
  const herbs = [];
  for (let i = 0; i < linkList.length; i++) {
    const pageUrl = linkList[i];
    try {
      console.log(`Fetching (${i+1}/${linkList.length}): ${pageUrl}`);
      const record = await parseHerbPage(pageUrl);
      // attempt to resolve image original
      if (record.images && record.images.length) {
        const filePage = record.images[0].page_url;
        const orig = await fetchFileOriginalUrl(filePage);
        record.images[0].file_url = orig;
      }
      // simple id slug
      record.id = pageUrl.split('/').pop();
      // set license placeholder (scraper should inspect footer or file pages for real license)
      record.license = 'CC BY-NC-SA 4.0 (source site)';
      herbs.push(record);
    } catch (e) {
      console.error('Error fetching', pageUrl, e.message);
    }
    await sleep(delay);
  }
  return herbs;
}

module.exports = { fetchAllHerbs };
