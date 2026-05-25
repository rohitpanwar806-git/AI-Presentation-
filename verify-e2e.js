#!/usr/bin/env node
/**
 * End-to-End Verification
 * Tests frontend → backend connectivity without Firebase deployment
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const BACKEND_URL = 'https://presentation-api-558900038680.asia-south1.run.app';
const FRONTEND_PORT = 8765;

console.log('🧪 End-to-End Verification Test');
console.log('================================\n');

// Step 1: Verify frontend files
console.log('📁 Step 1: Verifying frontend files...');
const files = ['frontend/web/index.html', 'frontend/web/app.js', 'frontend/web/config.js'];
let filesOk = true;
for (const file of files) {
  if (fs.existsSync(file)) {
    const size = fs.statSync(file).size;
    console.log(`   ✅ ${file} (${size} bytes)`);
  } else {
    console.log(`   ❌ ${file} NOT FOUND`);
    filesOk = false;
  }
}

if (!filesOk) {
  console.error('\n❌ Frontend files missing!\n');
  process.exit(1);
}

// Step 2: Test backend connectivity
console.log('\n🔗 Step 2: Testing backend API...');

function testBackendEndpoint(endpoint) {
  return new Promise((resolve) => {
    const url = new URL(BACKEND_URL + endpoint);
    const isHttps = url.protocol === 'https:';
    const https = require('https');
    
    const options = {
      hostname: url.hostname,
      port: 443,
      path: url.pathname,
      method: 'GET',
      timeout: 15000
    };
    
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          success: res.statusCode === 200,
          data: data ? JSON.parse(data) : null
        });
      });
    });
    
    req.on('error', (error) => {
      resolve({
        status: 0,
        success: false,
        error: error.message
      });
    });
    
    req.on('timeout', () => {
      req.destroy();
      resolve({
        status: 0,
        success: false,
        error: 'Request timeout'
      });
    });
    
    req.end();
  });
}

(async () => {
  // Test /health
  const healthResult = await testBackendEndpoint('/health');
  if (healthResult.success) {
    console.log(`   ✅ GET /health → ${healthResult.status}`);
    console.log(`      Response: ${JSON.stringify(healthResult.data)}`);
  } else {
    console.log(`   ❌ GET /health → ${healthResult.error || 'Error'}`);
  }
  
  // Test root endpoint
  const infoResult = await testBackendEndpoint('/');
  if (infoResult.success) {
    console.log(`   ✅ GET / → ${infoResult.status}`);
    console.log(`      Response: ${JSON.stringify(infoResult.data)}`);
  } else {
    console.log(`   ❌ GET / → ${infoResult.error || 'Error'}`);
  }
  
  // Step 3: Start local frontend server
  console.log('\n🌐 Step 3: Starting local frontend server...');
  
  const server = http.createServer((req, res) => {
    let filePath = path.join(__dirname, 'frontend/web', req.url === '/' ? 'index.html' : req.url);
    
    fs.readFile(filePath, (err, data) => {
      if (err) {
        res.writeHead(404);
        res.end('Not Found');
        return;
      }
      
      const ext = path.extname(filePath);
      const contentType = {
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.css': 'text/css',
        '.json': 'application/json'
      }[ext] || 'text/plain';
      
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(data);
    });
  });
  
  server.listen(FRONTEND_PORT, () => {
    console.log(`   ✅ Frontend running on http://localhost:${FRONTEND_PORT}`);
    console.log(`\n✨ Testing end-to-end connectivity...\n`);
    
    // Display summary
    console.log('📊 Configuration Summary:');
    console.log(`   Frontend: http://localhost:${FRONTEND_PORT}`);
    console.log(`   Backend: ${BACKEND_URL}`);
    console.log(`\n🔍 Test Results:`);
    console.log(`   • Frontend files: ✅ All ready`);
    console.log(`   • Backend /health: ${healthResult.success ? '✅ Connected' : '❌ Disconnected'}`);
    console.log(`   • Backend /info: ${infoResult.success ? '✅ Connected' : '❌ Disconnected'}`);
    console.log(`\n📝 Next Steps:`);
    console.log(`   1. Open browser: http://localhost:${FRONTEND_PORT}`);
    console.log(`   2. Check "Backend: Connected" status indicator`);
    console.log(`   3. Verify health check endpoints show green`);
    console.log(`   4. Click "Refresh Status" to re-test`);
    console.log(`\n🚀 To Deploy to Firebase Hosting:`);
    console.log(`   1. Run: firebase login`);
    console.log(`   2. Run: firebase deploy --only hosting --project project-987f80c5-14e3-450d-9b0`);
    console.log(`   3. Access: https://project-987f80c5-14e3-450d-9b0.web.app`);
    console.log(`\nPress Ctrl+C to stop the server.\n`);
  });
  
  // Cleanup on exit
  process.on('SIGINT', () => {
    console.log('\n\n🛑 Server stopped.');
    server.close();
    process.exit(0);
  });
})();
