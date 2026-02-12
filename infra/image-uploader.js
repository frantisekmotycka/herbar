// Placeholder: small utility to upload images to a CDN or to local public/images
// Implement provider-specific upload (S3, Cloudflare Images, etc.) as needed.
const fs = require('fs').promises;
const path = require('path');
async function saveLocal(buffer, filename) {
  const outDir = path.join(__dirname, '..', 'public', 'images');
  await fs.mkdir(outDir, { recursive: true });
  const outPath = path.join(outDir, filename);
  await fs.writeFile(outPath, buffer);
  return `/images/${filename}`;
}

module.exports = { saveLocal };
