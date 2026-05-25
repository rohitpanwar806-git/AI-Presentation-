#!/usr/bin/env node
/**
 * Firebase Hosting Deployment via REST API
 * Uses Google OAuth token for authentication
 */

const https = require('https');
const fs = require('fs');
const path = require('path');
const FormData = require('form-data');

const PROJECT_ID = 'project-987f80c5-14e3-450d-9b0';
const SITE_NAME = 'project-987f80c5-14e3-450d-9b0';
const TOKEN = process.argv[2] || '4/0AeoWuM-kQ-KLl32pEG4R9Y1kgEaP6y1wFbhOhIaLMZn-1OlVJD31S8-wAsiDTHtErCSMKw';

console.log(`
🚀 Firebase Hosting Deployment (REST API)
   Project: ${PROJECT_ID}
   Site: ${SITE_NAME}
   Token: ${TOKEN.substring(0, 10)}...
`);

// For simplicity, let's use the gcloud SDK which might already be authenticated
const { spawn } = require('child_process');

// Try to get gcloud access token
console.log('🔐 Getting access token from gcloud...\n');

const gcloudAuth = spawn('gcloud', ['auth', 'application-default', 'print-access-token'], {
  stdio: ['ignore', 'pipe', 'pipe'],
  shell: true
});

let accessToken = '';
let gcloudError = '';

gcloudAuth.stdout.on('data', (data) => {
  accessToken += data.toString().trim();
});

gcloudAuth.stderr.on('data', (data) => {
  gcloudError += data.toString();
});

gcloudAuth.on('close', (code) => {
  if (code !== 0 || !accessToken) {
    console.error('❌ Failed to get gcloud access token');
    console.error('   Try: gcloud auth application-default login');
    process.exit(1);
  }

  console.log('✅ Got access token from gcloud\n');
  deployWithToken(accessToken);
});

function deployWithToken(token) {
  console.log('📤 Deploying to Firebase Hosting...\n');

  const deployCmd = spawn('firebase', 
    ['deploy', '--only', 'hosting', '--project', PROJECT_ID],
    {
      stdio: 'inherit',
      shell: true,
      env: {
        ...process.env,
        GCLOUD_PROJECT: PROJECT_ID,
      }
    }
  );

  deployCmd.on('close', (code) => {
    if (code === 0) {
      console.log(`
✅ Deployment Successful!

🌐 Frontend URL: https://${SITE_NAME}.web.app
🔗 Backend: https://presentation-api-558900038680.asia-south1.run.app

✨ Your frontend is now live!
`);
    } else {
      console.error(`\n❌ Deployment failed with exit code ${code}`);
      process.exit(code);
    }
  });
}
