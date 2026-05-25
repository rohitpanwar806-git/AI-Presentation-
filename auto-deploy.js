#!/usr/bin/env node
const https = require('https');
const fs = require('fs');
const path = require('path');

const PROJECT_ID = 'project-987f80c5-14e3-450d-9b0';
const SITE_ID = 'project-987f80c5-14e3-450d-9b0';

console.log('🚀 Firebase Hosting Deployment via REST API\n');

// List files to deploy
const webDir = 'frontend/web';
const files = fs.readdirSync(webDir);

console.log('📁 Files to deploy:');
files.forEach(f => {
  const filePath = path.join(webDir, f);
  const size = fs.statSync(filePath).size;
  console.log(`   ${f} (${size} bytes)`);
});

console.log(`\n✅ Total files: ${files.length}`);
console.log('⚠️  NOTE: Firebase authentication required.\n');

console.log('To complete deployment, you MUST run in terminal:');
console.log('1. Clear env: $env:PYTHONHOME=""');
console.log('2. Login: firebase login');
console.log('3. Deploy: firebase deploy --only hosting --project ' + PROJECT_ID);
console.log('\nThen verify at: https://' + SITE_ID + '.web.app');

process.exit(0);
