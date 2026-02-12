const axios = require('axios');

async function getCrawlDelay(baseUrl) {
  try {
    const res = await axios.get(baseUrl + '/robots.txt', { timeout: 5000 });
    const txt = res.data;
    const m = txt.match(/Crawl-delay:\s*(\d+)/i);
    if (m) return parseInt(m[1], 10) * 1000;
  } catch (e) {
    // ignore
  }
  return 2000; // default 2s
}

module.exports = { getCrawlDelay };
