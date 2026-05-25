#!/usr/bin/env node
/**
 * Firebase Deployment Helper
 * Completes authentication and deploys frontend
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

const PROJECT_ID = 'project-987f80c5-14e3-450d-9b0';
const AUTH_CODE = process.argv[2];

console.log(`
╔════════════════════════════════════════════════════════════════╗
║            Firebase Hosting Deployment Helper                  ║
║              AI Presentation Avatar SaaS Platform              ║
╚════════════════════════════════════════════════════════════════╝
`);

// Verify required files exist
console.log('📋 Checking files...\n');
const requiredFiles = [
  'frontend/web/index.html',
  'frontend/web/app.js',
  'frontend/web/config.js',
  'firebase.json',
  '.firebaserc'
];

for (const file of requiredFiles) {
  if (!fs.existsSync(file)) {
    console.error(`❌ Missing: ${file}`);
    process.exit(1);
  }
  console.log(`✅ ${file}`);
}

console.log(`
\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ Quick Deploy Options:

1. firebase login
   Then: firebase deploy --only hosting --project ${PROJECT_ID}

2. Use service account (most secure):
   gcloud iam service-accounts create firebase-deployer ...
   (See TOKEN_DEPLOYMENT_GUIDE.md for full commands)

3. Web Console:
   https://console.firebase.google.com/
   Upload frontend/web/ folder manually

4. Automated (if gcloud authenticated):
   gcloud auth login
   firebase deploy --only hosting --project ${PROJECT_ID}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Your Authorization Code: ${AUTH_CODE || 'Not provided'}

If you have an auth code, you can:
1. Run: firebase login
2. Paste the code when prompted
3. Then run: firebase deploy --only hosting --project ${PROJECT_ID}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ After deployment, access at:
   https://${PROJECT_ID}.web.app

📊 Frontend size: 23.5 KB (within Firebase free tier: 1 GB)

For detailed instructions, see: TOKEN_DEPLOYMENT_GUIDE.md
`);

// Try to detect if firebase is authenticated
console.log('🔍 Checking Firebase CLI authentication...\n');

try {
  const result = execSync('firebase list --project ' + PROJECT_ID, {
    stdio: 'pipe',
    timeout: 5000
  }).toString();
  
  if (result.includes(PROJECT_ID)) {
    console.log('✅ Firebase CLI is authenticated!\n');
    console.log('🚀 Deploying now...\n');
    
    try {
      execSync(`firebase deploy --only hosting --project ${PROJECT_ID}`, {
        stdio: 'inherit'
      });
      
      console.log(`
✨ Deployment Complete!
🌐 URL: https://${PROJECT_ID}.web.app
🔗 Backend: https://presentation-api-558900038680.asia-south1.run.app
      `);
    } catch (e) {
      console.error('❌ Deployment failed. Try: firebase deploy --only hosting --project ' + PROJECT_ID);
      process.exit(1);
    }
  }
} catch (e) {
  console.log('⚠️  Firebase CLI not authenticated\n');
  console.log('Run one of these commands:\n');
  console.log(`1. firebase login`);
  console.log(`   Then: firebase deploy --only hosting --project ${PROJECT_ID}\n`);
  console.log(`2. gcloud auth login`);
  console.log(`   Then: firebase deploy --only hosting --project ${PROJECT_ID}\n`);
  console.log(`3. Use service account (see TOKEN_DEPLOYMENT_GUIDE.md)\n`);
  process.exit(0);
}
