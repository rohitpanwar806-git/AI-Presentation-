#!/usr/bin/env node
/**
 * Deploy to Firebase Hosting using Node.js
 * Bypasses PowerShell/Python issues
 */

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const PROJECT_ID = 'project-987f80c5-14e3-450d-9b0';
const BACKEND_URL = 'https://presentation-api-558900038680.asia-south1.run.app';

console.log('🚀 Firebase Hosting Deployment');
console.log(`📁 Project: ${PROJECT_ID}`);
console.log(`🔗 Backend: ${BACKEND_URL}\n`);

// Verify frontend files exist
const requiredFiles = [
  'frontend/web/index.html',
  'frontend/web/app.js',
  'frontend/web/config.js'
];

for (const file of requiredFiles) {
  if (!fs.existsSync(file)) {
    console.error(`❌ Missing file: ${file}`);
    process.exit(1);
  }
}

console.log('✅ Frontend files verified\n');

// Create or update firebase.json
const firebaseConfig = {
  hosting: {
    public: 'frontend/web',
    ignore: ['firebase.json', '.firebaserc', '**/.*', '**/node_modules/**'],
    cleanUrls: true,
    trailingSlash: false,
    rewrites: [
      {
        source: '**',
        destination: '/index.html'
      }
    ],
    headers: [
      {
        source: '**/*.@(js|css|gif|jpg|jpeg|png|svg|webp|woff|woff2)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000'
          }
        ]
      },
      {
        source: '**/*.html',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=3600, must-revalidate'
          }
        ]
      }
    ]
  }
};

fs.writeFileSync('firebase.json', JSON.stringify(firebaseConfig, null, 2));
console.log('✅ firebase.json configured\n');

// Create or update .firebaserc
const firebaserc = {
  projects: {
    default: PROJECT_ID
  }
};

fs.writeFileSync('.firebaserc', JSON.stringify(firebaserc, null, 2));
console.log('✅ .firebaserc configured\n');

// Run deployment
console.log('📤 Deploying to Firebase Hosting...\n');

exec(`firebase deploy --only hosting --project ${PROJECT_ID}`, (error, stdout, stderr) => {
  if (error) {
    console.error('❌ Deployment failed:');
    console.error(stderr || error.message);
    
    if (stderr.includes('authenticate')) {
      console.error('\n⚠️  Authentication required. Run: firebase login');
    }
    
    process.exit(1);
  }
  
  console.log(stdout);
  
  console.log('\n✅ Frontend deployed successfully!\n');
  console.log('📱 Access your frontend at:');
  console.log(`   https://${PROJECT_ID}.web.app\n`);
  console.log('🔗 Backend URL configured:');
  console.log(`   ${BACKEND_URL}\n`);
});
