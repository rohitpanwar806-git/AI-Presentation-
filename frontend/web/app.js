/**
 * PresenterAI — Frontend Application
 * Modern SPA for AI Presentation Avatar Platform
 */

// ==================== CONFIG ====================
const API_BASE = window.APP_CONFIG?.API_URL || 'https://presentation-api-558900038680.asia-south1.run.app';
const GOOGLE_CLIENT_ID = window.APP_CONFIG?.GOOGLE_CLIENT_ID || '';

// ==================== STATE ====================
let state = {
  user: null,
  token: null,
  currentTab: 'signin',
  presentations: [],
  isLoading: false
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initUploadZone();
  initGoogleAuth();
  checkExistingSession();
});

function initNavbar() {
  const navbar = document.getElementById('navbar');
  let lastScroll = 0;
  window.addEventListener('scroll', () => {
    const scrollY = window.scrollY;
    navbar.classList.toggle('scrolled', scrollY > 50);
    lastScroll = scrollY;
  }, { passive: true });
}

function initUploadZone() {
  const zone = document.getElementById('uploadZone');
  const input = document.getElementById('fileInput');
  if (!zone || !input) return;

  zone.addEventListener('click', (e) => {
    if (e.target !== input) input.click();
  });

  zone.addEventListener('dragover', (e) => {
    e.preventDefault();
    zone.classList.add('dragover');
  });

  zone.addEventListener('dragleave', () => {
    zone.classList.remove('dragover');
  });

  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  input.addEventListener('change', () => {
    if (input.files.length) {
      handleFileUpload(input.files[0]);
    }
  });
}

function initGoogleAuth() {
  if (!GOOGLE_CLIENT_ID) return;
  
  const script = document.createElement('script');
  script.src = 'https://accounts.google.com/gsi/client';
  script.async = true;
  script.defer = true;
  script.onload = () => {
    if (window.google) {
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleGoogleResponse
      });
    }
  };
  document.head.appendChild(script);
}

function checkExistingSession() {
  const token = localStorage.getItem('auth_token');
  const user = localStorage.getItem('auth_user');
  if (token && user) {
    try {
      state.token = token;
      state.user = JSON.parse(user);
      showDashboard();
    } catch {
      clearSession();
    }
  }
}

// ==================== AUTH ====================
function openAuth(tab = 'signin') {
  const modal = document.getElementById('authModal');
  modal.classList.add('active');
  switchTab(tab);
  document.body.style.overflow = 'hidden';
}

function closeAuth() {
  const modal = document.getElementById('authModal');
  modal.classList.remove('active');
  document.body.style.overflow = '';
  hideAuthMessages();
}

function switchTab(tab) {
  state.currentTab = tab;
  const tabSignin = document.getElementById('tabSignin');
  const tabSignup = document.getElementById('tabSignup');
  const signupFields = document.getElementById('signupFields');
  const verificationFields = document.getElementById('verificationFields');
  const title = document.getElementById('authTitle');
  const subtitle = document.getElementById('authSubtitle');
  const btnText = document.getElementById('authBtnText');

  hideAuthMessages();

  if (tab === 'signin') {
    tabSignin.classList.add('active');
    tabSignup.classList.remove('active');
    signupFields.style.display = 'none';
    verificationFields.style.display = 'none';
    title.textContent = 'Welcome back';
    subtitle.textContent = 'Sign in to your account to continue';
    btnText.textContent = 'Sign In';
  } else {
    tabSignin.classList.remove('active');
    tabSignup.classList.add('active');
    signupFields.style.display = 'block';
    verificationFields.style.display = 'none';
    title.textContent = 'Create your account';
    subtitle.textContent = 'Start creating AI presentations for free';
    btnText.textContent = 'Create Account';
  }
}

async function handleAuth(event) {
  event.preventDefault();
  if (state.isLoading) return;

  const email = document.getElementById('authEmail').value.trim();
  const password = document.getElementById('authPassword').value;

  if (!email || !password) {
    showAuthError('Please fill in all required fields');
    return;
  }

  if (password.length < 8) {
    showAuthError('Password must be at least 8 characters');
    return;
  }

  setAuthLoading(true);

  try {
    if (state.currentTab === 'signin') {
      await login(email, password);
    } else {
      await register(email, password);
    }
  } catch (err) {
    showAuthError(err.message || 'An unexpected error occurred');
  } finally {
    setAuthLoading(false);
  }
}

async function login(email, password) {
  const res = await apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Invalid email or password');
  }

  const data = await res.json();
  saveSession(data.access_token, data.user || { email });
  closeAuth();
  showDashboard();
  showToast('Welcome back!', 'success');
}

async function register(email, password) {
  const firstName = document.getElementById('firstName').value.trim();
  const lastName = document.getElementById('lastName').value.trim();
  const gender = document.getElementById('gender').value;

  if (!firstName || !lastName) {
    throw new Error('Please enter your first and last name');
  }

  const res = await apiRequest('/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      email,
      password,
      first_name: firstName,
      last_name: lastName,
      gender: gender || 'other'
    })
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Registration failed. Please try again.');
  }

  const data = await res.json();
  
  if (data.access_token) {
    saveSession(data.access_token, data.user || { email, first_name: firstName });
    closeAuth();
    showDashboard();
    showToast('Account created successfully!', 'success');
  } else {
    // Email verification needed
    showAuthSuccess('Verification code sent to your email. Check your inbox.');
    document.getElementById('verificationFields').style.display = 'block';
    document.getElementById('authBtnText').textContent = 'Verify & Sign In';
    state.currentTab = 'verify';
  }
}

async function signInWithGoogle() {
  if (window.google) {
    window.google.accounts.id.prompt();
  } else {
    showToast('Google Sign-In is not available', 'error');
  }
}

async function handleGoogleResponse(response) {
  if (!response.credential) return;

  setAuthLoading(true);
  try {
    const res = await apiRequest('/auth/google', {
      method: 'POST',
      body: JSON.stringify({ token: response.credential })
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Google sign-in failed');
    }

    const data = await res.json();
    saveSession(data.access_token, data.user || {});
    closeAuth();
    showDashboard();
    showToast('Signed in with Google!', 'success');
  } catch (err) {
    showAuthError(err.message);
  } finally {
    setAuthLoading(false);
  }
}

function logout() {
  clearSession();
  showLanding();
  showToast('Signed out successfully', 'success');
}

// ==================== SESSION MANAGEMENT ====================
function saveSession(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem('auth_token', token);
  localStorage.setItem('auth_user', JSON.stringify(user));
}

function clearSession() {
  state.token = null;
  state.user = null;
  state.presentations = [];
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
}

// ==================== VIEW MANAGEMENT ====================
function showDashboard() {
  document.getElementById('landing').classList.add('hidden');
  document.getElementById('dashboard').classList.add('active');
  
  // Update nav
  document.getElementById('navLinks').style.display = 'none';
  document.getElementById('navActions').innerHTML = `
    <span style="font-size:13px;color:var(--text-secondary);">${state.user?.email || ''}</span>
    <button class="btn btn-ghost" onclick="logout()">Sign Out</button>
  `;

  // Update welcome
  const name = state.user?.first_name || state.user?.email?.split('@')[0] || 'User';
  document.getElementById('userName').textContent = name;

  // Load presentations
  loadPresentations();
}

function showLanding() {
  document.getElementById('landing').classList.remove('hidden');
  document.getElementById('dashboard').classList.remove('active');
  document.getElementById('navLinks').style.display = '';
  document.getElementById('navActions').innerHTML = `
    <button class="btn btn-ghost" onclick="openAuth('signin')">Log In</button>
    <button class="btn btn-primary" onclick="openAuth('signup')">Get Started Free</button>
  `;
}

// ==================== FILE UPLOAD ====================
async function handleFileUpload(file) {
  const validTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ];

  const ext = file.name.split('.').pop().toLowerCase();
  const validExts = ['pdf', 'pptx', 'docx'];

  if (!validExts.includes(ext) && !validTypes.includes(file.type)) {
    showToast('Please upload a PDF, PPTX, or DOCX file', 'error');
    return;
  }

  if (file.size > 50 * 1024 * 1024) {
    showToast('File size exceeds 50MB limit', 'error');
    return;
  }

  const progress = document.getElementById('uploadProgress');
  const progressFill = document.getElementById('progressFill');
  const uploadStatus = document.getElementById('uploadStatus');

  progress.classList.add('active');
  progressFill.style.width = '0%';
  uploadStatus.textContent = 'Uploading...';

  // Simulate progress
  let pct = 0;
  const interval = setInterval(() => {
    pct = Math.min(pct + Math.random() * 15, 90);
    progressFill.style.width = pct + '%';
  }, 200);

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch(`${API_BASE}/presentations/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${state.token}`
      },
      body: formData
    });

    clearInterval(interval);

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Upload failed');
    }

    progressFill.style.width = '100%';
    uploadStatus.textContent = 'Upload complete!';
    showToast(`"${file.name}" uploaded successfully!`, 'success');

    setTimeout(() => {
      progress.classList.remove('active');
      progressFill.style.width = '0%';
    }, 2000);

    loadPresentations();
  } catch (err) {
    clearInterval(interval);
    progress.classList.remove('active');
    showToast(err.message || 'Upload failed', 'error');
  }
}

// ==================== PRESENTATIONS ====================
async function loadPresentations() {
  if (!state.token) return;

  try {
    const res = await apiRequest('/presentations/', {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });

    if (res.ok) {
      const data = await res.json();
      state.presentations = Array.isArray(data) ? data : (data.presentations || []);
      renderPresentations();
    }
  } catch {
    // Silent fail - presentations list is optional
  }
}

function renderPresentations() {
  const container = document.getElementById('presentationsList');
  if (!container) return;

  if (!state.presentations.length) {
    container.innerHTML = '';
    return;
  }

  const html = `
    <h3 class="dash-section-title" style="margin-top:48px;">Your Presentations</h3>
    ${state.presentations.map(p => `
      <div class="presentation-item">
        <div class="presentation-info">
          <span class="presentation-icon">📄</span>
          <div class="presentation-meta">
            <h4>${escapeHtml(p.filename || p.title || 'Untitled')}</h4>
            <span>${formatDate(p.created_at || p.uploaded_at)} • ${p.file_type || 'Document'}</span>
          </div>
        </div>
        <div class="presentation-actions">
          <button class="btn btn-ghost" style="padding:6px 12px;font-size:12px;" onclick="deletePresentation('${p.id}')">Delete</button>
        </div>
      </div>
    `).join('')}
  `;

  container.innerHTML = html;
}

async function deletePresentation(id) {
  if (!confirm('Delete this presentation?')) return;

  try {
    const res = await apiRequest(`/presentations/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });

    if (res.ok) {
      showToast('Presentation deleted', 'success');
      loadPresentations();
    } else {
      showToast('Failed to delete', 'error');
    }
  } catch {
    showToast('Failed to delete', 'error');
  }
}

// ==================== API HELPER ====================
async function apiRequest(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };

  if (state.token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }

  // Don't set Content-Type for FormData
  if (options.body instanceof FormData) {
    delete headers['Content-Type'];
  }

  return fetch(url, { ...options, headers });
}

// ==================== UI HELPERS ====================
function setAuthLoading(loading) {
  state.isLoading = loading;
  const btn = document.getElementById('authSubmitBtn');
  const spinner = document.getElementById('authSpinner');
  const text = document.getElementById('authBtnText');
  
  if (loading) {
    btn.disabled = true;
    btn.style.opacity = '0.7';
    spinner.classList.add('active');
    text.style.opacity = '0.5';
  } else {
    btn.disabled = false;
    btn.style.opacity = '1';
    spinner.classList.remove('active');
    text.style.opacity = '1';
  }
}

function showAuthError(msg) {
  const el = document.getElementById('authError');
  el.textContent = msg;
  el.classList.add('show');
}

function showAuthSuccess(msg) {
  const el = document.getElementById('authSuccess');
  el.textContent = msg;
  el.classList.add('show');
}

function hideAuthMessages() {
  document.getElementById('authError').classList.remove('show');
  document.getElementById('authSuccess').classList.remove('show');
}

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast ${type} show`;
  setTimeout(() => { toast.classList.remove('show'); }, 4000);
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function formatDate(dateStr) {
  if (!dateStr) return 'Just now';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return 'Recently';
  }
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
  if (e.target.id === 'authModal') closeAuth();
});

// Close modal on Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeAuth();
});
