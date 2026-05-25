#!/usr/bin/env node
/**
 * One-Click Firebase Deployment Script
 * For AI Presentation Avatar SaaS Platform
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const PROJECT_ID = 'project-987f80c5-14e3-450d-9b0';
const BACKEND_URL = 'https://presentation-api-558900038680.asia-south1.run.app';

console.log(`
╔════════════════════════════════════════════════════════════════╗
║     Firebase Hosting Deployment - AI Presentation Avatar       ║
║                  Cost-Optimized on GCP Credits                 ║
╚════════════════════════════════════════════════════════════════╝

📊 Deployment Configuration:
   Project ID: ${PROJECT_ID}
   Frontend Location: frontend/web/
   Backend URL: ${BACKEND_URL}
   Region: asia-south1 (Mumbai)
   Cost: FREE (within Firebase quota)

`);

// Step 1: Verify files
console.log('Step 1️⃣  Verifying frontend files...\n');
const requiredFiles = [
  'frontend/web/index.html',
  'frontend/web/app.js',
  'frontend/web/config.js'
];

let allFilesExist = true;
for (const file of requiredFiles) {
  if (fs.existsSync(file)) {
    console.log(`  ✅ ${file}`);
  } else {
    console.log(`  ❌ ${file} - NOT FOUND`);
    allFilesExist = false;
  }
}

if (!allFilesExist) {
  console.error('\n❌ Some frontend files are missing. Aborting.\n');
  process.exit(1);
}

// Step 2: Create configs
console.log('\nStep 2️⃣  Configuring Firebase...\n');

const firebaseJson = {
  hosting: {
    public: 'frontend/web',
    ignore: ['firebase.json', '.firebaserc', '**/.*', '**/node_modules/**'],
    cleanUrls: true,
    trailingSlash: false,
    rewrites: [{ source: '**', destination: '/index.html' }],
    headers: [
      {
        source: '**/*.@(js|css|gif|jpg|jpeg|png|svg|webp|woff|woff2)',
        headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000' }]
      },
      {
        source: '**/*.html',
        headers: [{ key: 'Cache-Control', value: 'public, max-age=3600, must-revalidate' }]
      }
    ]
  }
};

fs.writeFileSync('firebase.json', JSON.stringify(firebaseJson, null, 2));
console.log('  ✅ firebase.json created');

const firebaserc = { projects: { default: PROJECT_ID } };
fs.writeFileSync('.firebaserc', JSON.stringify(firebaserc, null, 2));
console.log('  ✅ .firebaserc created');

// Step 3: Deploy
console.log('\nStep 3️⃣  Deploying to Firebase Hosting...\n');
console.log('  This may take 1-2 minutes...\n');

const firebaseProcess = spawn('firebase', ['deploy', '--only', 'hosting', '--project', PROJECT_ID], {
  stdio: 'inherit',
  shell: true
});

firebaseProcess.on('close', (code) => {
  if (code === 0) {
    console.log(`
╔════════════════════════════════════════════════════════════════╗
║                  ✅ DEPLOYMENT SUCCESSFUL!                    ║
╚════════════════════════════════════════════════════════════════╝

🌐 Your frontend is now live at:
   https://${PROJECT_ID}.web.app

📋 Configuration Details:
   • Backend URL: ${BACKEND_URL}
   • Hosting: Firebase (Global CDN)
   • CORS: Configured for backend integration
   • Cache: Optimized for production

✨ What to test next:
   1. Visit: https://${PROJECT_ID}.web.app
   2. Check backend status indicator (should show "Connected")
   3. Click "Refresh Status" to test API endpoints
   4. Verify /health and / endpoints respond (green indicators)

💰 Cost Breakdown (Monthly):
   • Firebase Hosting: FREE (1GB storage, 10GB/mo bandwidth)
   • Cloud Run Backend: ~FREE (2M requests/mo free)
   • Cloud SQL Database: ~$15-20/mo (using GCP credits)
   • Total: Using your GCP credits (no additional charges)

📊 Monitor costs at:
   https://console.cloud.google.com/billing/project-${PROJECT_ID}

🔧 To update frontend:
   1. Edit files in frontend/web/
   2. Run: firebase deploy --only hosting

🆘 Troubleshooting:
   • Clear browser cache if not seeing updates
   • Check CORS in backend if connectivity fails
   • Verify Cloud Run service is running

`);
  } else {
    console.log(`
❌ Deployment failed with exit code ${code}

Possible solutions:
1. Authenticate Firebase CLI:
   firebase login

2. Or use service account (advanced):
   ${path.join(__dirname, 'FIREBASE_DEPLOYMENT_GUIDE.md')}

3. For manual deployment via Firebase Console:
   https://console.firebase.google.com

`);
    process.exit(1);
  }
});

firebaseProcess.on('error', (err) => {
  console.error('❌ Error spawning firebase command:', err.message);
  console.error('\nMake sure Firebase CLI is installed: npm install -g firebase-tools');
  process.exit(1);
});
