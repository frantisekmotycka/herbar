const path = require('path');
const fs = require('fs').promises;
const scraper = require('../server/scraper');

async function main() {
  const outDir = path.join(__dirname, '..', 'data');
  await fs.mkdir(outDir, { recursive: true });
  console.log('Fetching herb list from WikiFood...');
  const herbs = await scraper.fetchAllHerbs();
  const outFile = path.join(outDir, 'herbs.json');
  await fs.writeFile(outFile, JSON.stringify(herbs, null, 2), 'utf8');
  console.log(`Wrote ${herbs.length} records to ${outFile}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
