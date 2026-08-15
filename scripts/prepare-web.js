const fs = require('fs');
const path = require('path');

const root = process.cwd();
const www = path.join(root, 'www');
const templates = path.join(root, 'templates');
const staticDir = path.join(root, 'static');

function ensureDir(p){ if(!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true }); }

ensureDir(www);
ensureDir(path.join(www, 'static'));
ensureDir(path.join(www, 'static', 'icons'));

// Copy static files
function copyDir(src, dest){
  if(!fs.existsSync(src)) return;
  ensureDir(dest);
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for(const e of entries){
    const srcPath = path.join(src, e.name);
    const destPath = path.join(dest, e.name);
    if(e.isDirectory()) copyDir(srcPath, destPath);
    else fs.copyFileSync(srcPath, destPath);
  }
}

copyDir(staticDir, path.join(www, 'static'));

// Read index.html and rewrite absolute /static/ references to ./static/
const indexSrc = path.join(templates, 'index.html');
const indexDst = path.join(www, 'index.html');
if(fs.existsSync(indexSrc)){
  let html = fs.readFileSync(indexSrc, 'utf8');
  html = html.replace(/\s\/(static\/)/g, ' ./static/');
  // also replace href="/static/" occurrences
  html = html.replace(/="\/static\//g, '="./static/');
  fs.writeFileSync(indexDst, html, 'utf8');
}

console.log('Prepared web directory at', www);
