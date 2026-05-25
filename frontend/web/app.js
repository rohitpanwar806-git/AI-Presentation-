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
        callback: handleGoogleResponse,
        use_fedcm_for_prompt: false
      });
      // Render Google's official button (bypasses FedCM, uses popup)
      const container = document.getElementById('googleBtnContainer');
      if (container) {
        window.google.accounts.id.renderButton(container, {
          theme: 'filled_black',
          size: 'large',
          width: 360,
          text: 'continue_with',
          shape: 'pill'
        });
      }
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
    throw new Error(extractErrorMessage(data, 'Invalid email or password'));
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
    throw new Error(extractErrorMessage(data, 'Registration failed. Please try again.'));
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
    // Fallback: try prompt (in case rendered button isn't visible)
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
      body: JSON.stringify({ credential: response.credential })
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(data, 'Google sign-in failed'));
    }

    const data = await res.json();
    saveSession(data.access_token, data.user || {});
    closeAuth();
    showDashboard();
    showToast('Signed in with Google!', 'success');
  } catch (err) {
    showAuthError(err.message || String(err));
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
    uploadStatus.textContent = 'Upload complete! Choose your avatar next...';
    showToast(`"${file.name}" uploaded successfully!`, 'success');

    setTimeout(() => {
      progress.classList.remove('active');
      progressFill.style.width = '0%';
      openAvatarPanel();
    }, 1500);

    loadPresentations();
  } catch (err) {
    clearInterval(interval);
    progress.classList.remove('active');
    showToast(err.message || 'Upload failed', 'error');
  }
}

// ==================== PRESENTATIONS MANAGEMENT ====================
let presData = { presentations: [], summary: {}, currentFilter: 'all', editingId: null };

async function loadPresentations() {
  if (!state.token) return;

  try {
    const sort = document.getElementById('presSortSelect')?.value || 'newest';
    const res = await apiRequest(`/presentations/?sort=${sort}`);

    if (res.ok) {
      const data = await res.json();
      state.presentations = data.presentations || [];
      presData.presentations = state.presentations;
      presData.summary = data.summary || {};
      renderPresentations();
      renderPresentationsInDashboard();
    }
  } catch {
    // Silent fail
  }
}

function renderPresentationsInDashboard() {
  const container = document.getElementById('presentationsList');
  if (!container) return;

  if (!state.presentations.length) {
    container.innerHTML = '';
    return;
  }

  // Show latest 3 in dashboard
  const latest = state.presentations.slice(0, 3);
  const html = `
    <h3 class="dash-section-title" style="margin-top:48px;">Recent Presentations</h3>
    ${latest.map(p => `
      <div class="presentation-item" style="cursor:pointer;" onclick="openPresPanel()">
        <div class="presentation-info">
          <span class="presentation-icon">${getFileIcon(p.file_type)}</span>
          <div class="presentation-meta">
            <h4>${escapeHtml(p.title || p.filename || 'Untitled')}</h4>
            <span>${formatDate(p.created_at)} • ${p.file_type || 'Document'} • ${p.analytics?.views || 0} views</span>
          </div>
        </div>
        <div class="presentation-actions">
          <span class="pres-status-badge ${p.status}">${p.status}</span>
        </div>
      </div>
    `).join('')}
    ${state.presentations.length > 3 ? `<p style="text-align:center;margin-top:16px;"><button class="btn btn-ghost" onclick="openPresPanel()">View All (${state.presentations.length})</button></p>` : ''}
  `;
  container.innerHTML = html;
}

function renderPresentations() {
  // This renders in the full presentations panel
  renderPresStats();
  renderPresList();
}

function renderPresStats() {
  const container = document.getElementById('presStats');
  if (!container) return;
  const s = presData.summary;
  container.innerHTML = `
    <div class="stat-card"><div class="stat-value">${s.total_presentations || 0}</div><div class="stat-label">Total Presentations</div></div>
    <div class="stat-card"><div class="stat-value">${s.total_views || 0}</div><div class="stat-label">Total Views</div></div>
    <div class="stat-card"><div class="stat-value">${s.total_shares || 0}</div><div class="stat-label">Total Shares</div></div>
    <div class="stat-card"><div class="stat-value">${s.statuses?.published || 0}</div><div class="stat-label">Published</div></div>
  `;
}

function renderPresList() {
  const container = document.getElementById('presListContainer');
  if (!container) return;

  let filtered = presData.presentations;
  if (presData.currentFilter !== 'all') {
    filtered = filtered.filter(p => p.status === presData.currentFilter);
  }

  if (!filtered.length) {
    container.innerHTML = `
      <div class="pres-empty">
        <div class="pres-empty-icon">📂</div>
        <h3>${presData.currentFilter === 'all' ? 'No presentations yet' : `No ${presData.currentFilter} presentations`}</h3>
        <p>Upload a document from the dashboard to create your first AI presentation.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(p => `
    <div class="pres-card" id="pres-card-${p.id}">
      <div class="pres-card-top">
        <div class="pres-card-info">
          <h4>${getFileIcon(p.file_type)} ${escapeHtml(p.title || p.filename)}</h4>
          <div class="pres-meta">
            <span>📅 ${formatDate(p.created_at)}</span>
            <span>📁 ${p.file_type}</span>
            <span>💾 ${formatFileSize(p.file_size)}</span>
            ${p.avatar_id ? '<span>🎭 Avatar set</span>' : ''}
            ${p.voice_id ? '<span>🗣️ Voice set</span>' : ''}
          </div>
          ${p.description ? `<div class="pres-desc">${escapeHtml(p.description)}</div>` : ''}
        </div>
        <span class="pres-status-badge ${p.status}">${p.status}</span>
      </div>
      <div class="pres-card-analytics">
        <div class="pres-analytic"><span class="analytic-icon">👁️</span> <strong>${p.analytics.views}</strong> views</div>
        <div class="pres-analytic"><span class="analytic-icon">👤</span> <strong>${p.analytics.unique_viewers}</strong> unique viewers</div>
        <div class="pres-analytic"><span class="analytic-icon">🔗</span> <strong>${p.analytics.shares}</strong> shares</div>
        <div class="pres-analytic"><span class="analytic-icon">✅</span> <strong>${p.analytics.completion_rate}%</strong> completion</div>
        ${p.analytics.last_viewed ? `<div class="pres-analytic"><span class="analytic-icon">🕐</span> Last viewed ${formatDate(p.analytics.last_viewed)}</div>` : ''}
      </div>
      <div class="pres-card-actions">
        <button class="pres-btn primary" onclick="viewPresentation('${p.id}')">▶ View</button>
        <button class="pres-btn" onclick="editPresentation('${p.id}')">✏️ Edit</button>
        <button class="pres-btn" onclick="sharePresentation('${p.id}')">🔗 Share</button>
        <button class="pres-btn danger" onclick="deletePresentation('${p.id}')">🗑️ Delete</button>
      </div>
      <div id="pres-edit-${p.id}"></div>
    </div>
  `).join('');
}

function openPresPanel() {
  document.getElementById('presPanel').classList.add('active');
  document.body.style.overflow = 'hidden';
  loadPresentations();
}

function closePresPanel() {
  document.getElementById('presPanel').classList.remove('active');
  document.body.style.overflow = '';
}

function filterPresentations(el, status) {
  document.querySelectorAll('#presFilters .filter-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  presData.currentFilter = status;
  document.getElementById('presListTitle').textContent = status === 'all' ? 'All Presentations' : `${status.charAt(0).toUpperCase() + status.slice(1)} Presentations`;
  renderPresList();
}

function sortPresentations() {
  loadPresentations();
}

async function viewPresentation(id) {
  // Record view and show toast
  try {
    await apiRequest(`/presentations/${id}/view`, { method: 'POST' });
    const p = presData.presentations.find(x => x.id === id);
    if (p) p.analytics.views++;
    renderPresList();
    showToast('Presentation opened — view recorded', 'success');
  } catch {
    showToast('Could not record view', 'error');
  }
}

function editPresentation(id) {
  const container = document.getElementById(`pres-edit-${id}`);
  const p = presData.presentations.find(x => x.id === id);
  if (!p) return;

  if (presData.editingId === id) {
    container.innerHTML = '';
    presData.editingId = null;
    return;
  }
  presData.editingId = id;

  container.innerHTML = `
    <div class="pres-edit-form">
      <label>Title</label>
      <input type="text" id="editTitle-${id}" value="${escapeHtml(p.title || '')}" placeholder="Presentation title">
      <label>Description</label>
      <textarea id="editDesc-${id}" placeholder="Add a description...">${escapeHtml(p.description || '')}</textarea>
      <label>Status</label>
      <select id="editStatus-${id}" class="pres-sort-select" style="width:100%;">
        <option value="uploaded" ${p.status === 'uploaded' ? 'selected' : ''}>Uploaded</option>
        <option value="processing" ${p.status === 'processing' ? 'selected' : ''}>Processing</option>
        <option value="ready" ${p.status === 'ready' ? 'selected' : ''}>Ready</option>
        <option value="published" ${p.status === 'published' ? 'selected' : ''}>Published</option>
      </select>
      <div class="pres-edit-actions">
        <button class="pres-btn primary" onclick="savePresentation('${id}')">Save Changes</button>
        <button class="pres-btn" onclick="editPresentation('${id}')">Cancel</button>
      </div>
    </div>
  `;
}

async function savePresentation(id) {
  const title = document.getElementById(`editTitle-${id}`).value.trim();
  const description = document.getElementById(`editDesc-${id}`).value.trim();
  const newStatus = document.getElementById(`editStatus-${id}`).value;

  try {
    const res = await apiRequest(`/presentations/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ title, description, status: newStatus })
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(data, 'Failed to update'));
    }

    const data = await res.json();
    // Update local state
    const idx = presData.presentations.findIndex(x => x.id === id);
    if (idx !== -1 && data.presentation) {
      presData.presentations[idx] = data.presentation;
      state.presentations = presData.presentations;
    }
    presData.editingId = null;
    renderPresList();
    renderPresentationsInDashboard();
    showToast('Presentation updated!', 'success');
  } catch (err) {
    showToast(err.message || 'Update failed', 'error');
  }
}

async function sharePresentation(id) {
  try {
    await apiRequest(`/presentations/${id}/share`, { method: 'POST' });
    const p = presData.presentations.find(x => x.id === id);
    if (p) p.analytics.shares++;
    renderPresList();
    // Copy a mock share link
    const shareUrl = `${window.location.origin}/view/${id}`;
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(shareUrl);
      showToast('Share link copied to clipboard!', 'success');
    } else {
      showToast('Share recorded! Link: ' + shareUrl, 'success');
    }
  } catch {
    showToast('Failed to share', 'error');
  }
}

async function deletePresentation(id) {
  if (!confirm('Are you sure you want to delete this presentation? This cannot be undone.')) return;

  try {
    const res = await apiRequest(`/presentations/${id}`, { method: 'DELETE' });

    if (res.ok) {
      presData.presentations = presData.presentations.filter(p => p.id !== id);
      state.presentations = presData.presentations;
      presData.summary.total_presentations = presData.presentations.length;
      renderPresentations();
      renderPresentationsInDashboard();
      showToast('Presentation deleted', 'success');
    } else {
      showToast('Failed to delete', 'error');
    }
  } catch {
    showToast('Failed to delete', 'error');
  }
}

function getFileIcon(type) {
  switch(type) {
    case 'PDF': return '📕';
    case 'PowerPoint': return '📙';
    case 'Word': return '📘';
    default: return '📄';
  }
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ==================== API HELPER ====================
function extractErrorMessage(data, fallback) {
  if (!data || !data.detail) return fallback;
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map(e => e.msg || e.message || JSON.stringify(e)).join('; ');
  }
  if (typeof data.detail === 'object') return data.detail.msg || data.detail.message || JSON.stringify(data.detail);
  return fallback;
}

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
  if (e.target.id === 'avatarPanel') closeAvatarPanel();
  if (e.target.id === 'voicePanel') closeVoicePanel();
  if (e.target.id === 'presPanel') closePresPanel();
});

// Close modal on Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeAuth();
    closeAvatarPanel();
    closeVoicePanel();
    closePresPanel();
  }
});

// ==================== AVATAR SELECTION ====================
let avatarData = { avatars: [], categories: [], selectedId: null };

function openAvatarPanel() {
  document.getElementById('avatarPanel').classList.add('active');
  document.body.style.overflow = 'hidden';
  loadAvatars();
}

function closeAvatarPanel() {
  document.getElementById('avatarPanel').classList.remove('active');
  document.body.style.overflow = '';
}

async function loadAvatars() {
  const grid = document.getElementById('avatarGrid');
  grid.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-secondary);">Loading avatars...</div>';

  try {
    const res = await apiRequest('/avatars/');
    if (!res.ok) throw new Error('Failed to load avatars');
    const data = await res.json();
    avatarData.avatars = data.avatars || [];
    avatarData.categories = data.categories || [];
    renderAvatarFilters();
    renderAvatarGrid(avatarData.avatars);
  } catch (err) {
    grid.innerHTML = `<div style="text-align:center;padding:40px;color:#ff6b6b;">Failed to load avatars: ${escapeHtml(err.message)}</div>`;
  }
}

function renderAvatarFilters() {
  const container = document.getElementById('avatarFilters');
  container.innerHTML = avatarData.categories.map(cat =>
    `<button class="filter-chip ${cat.id === 'all' ? 'active' : ''}" data-category="${cat.id}" onclick="selectAvatarCategory(this, '${cat.id}')">
      ${cat.icon} ${cat.name} (${cat.count})
    </button>`
  ).join('');
}

function selectAvatarCategory(el, category) {
  document.querySelectorAll('#avatarFilters .filter-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  filterAvatars();
}

function filterAvatars() {
  const search = document.getElementById('avatarSearch').value.toLowerCase();
  const activeCategory = document.querySelector('#avatarFilters .filter-chip.active')?.dataset.category || 'all';

  let filtered = avatarData.avatars;
  if (activeCategory && activeCategory !== 'all') {
    filtered = filtered.filter(a => a.category === activeCategory);
  }
  if (search) {
    filtered = filtered.filter(a =>
      a.name.toLowerCase().includes(search) ||
      a.description.toLowerCase().includes(search) ||
      a.category.toLowerCase().includes(search)
    );
  }
  renderAvatarGrid(filtered);
}

function renderAvatarGrid(avatars) {
  const grid = document.getElementById('avatarGrid');
  if (!avatars.length) {
    grid.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-secondary);">No avatars match your filters</div>';
    return;
  }
  grid.innerHTML = avatars.map(a => `
    <div class="avatar-card ${avatarData.selectedId === a.id ? 'selected' : ''}" onclick="selectAvatar('${a.id}')">
      <img src="${a.thumbnail}" alt="${escapeHtml(a.name)}" loading="lazy">
      <div class="avatar-name">${escapeHtml(a.name)}</div>
      <div class="avatar-desc">${escapeHtml(a.description)}</div>
      <span class="avatar-badge">${a.category}</span>
    </div>
  `).join('');
}

function selectAvatar(id) {
  avatarData.selectedId = id;
  const avatar = avatarData.avatars.find(a => a.id === id);
  document.getElementById('avatarSelectionInfo').innerHTML = `Selected: <strong>${escapeHtml(avatar?.name || '')}</strong>`;
  document.getElementById('avatarConfirmBtn').disabled = false;
  // Re-render to show selection state
  const search = document.getElementById('avatarSearch').value.toLowerCase();
  const activeCategory = document.querySelector('#avatarFilters .filter-chip.active')?.dataset.category || 'all';
  let filtered = avatarData.avatars;
  if (activeCategory && activeCategory !== 'all') filtered = filtered.filter(a => a.category === activeCategory);
  if (search) filtered = filtered.filter(a => a.name.toLowerCase().includes(search) || a.description.toLowerCase().includes(search));
  renderAvatarGrid(filtered);
}

function confirmAvatarSelection() {
  if (!avatarData.selectedId) return;
  const avatar = avatarData.avatars.find(a => a.id === avatarData.selectedId);
  closeAvatarPanel();
  showToast(`Avatar "${avatar.name}" selected!`, 'success');
  // Open voice panel next
  setTimeout(() => openVoicePanel(), 400);
}

// ==================== VOICE SELECTION ====================
let voiceData = { voices: [], languages: [], selectedId: null };

function openVoicePanel() {
  document.getElementById('voicePanel').classList.add('active');
  document.body.style.overflow = 'hidden';
  loadVoices();
}

function closeVoicePanel() {
  document.getElementById('voicePanel').classList.remove('active');
  document.body.style.overflow = '';
}

async function loadVoices() {
  const grid = document.getElementById('voiceGrid');
  grid.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-secondary);">Loading voices...</div>';

  try {
    const [voicesRes, langsRes] = await Promise.all([
      apiRequest('/voices/'),
      apiRequest('/voices/languages')
    ]);

    if (!voicesRes.ok) throw new Error('Failed to load voices');
    const vData = await voicesRes.json();
    voiceData.voices = vData.voices || [];

    if (langsRes.ok) {
      const lData = await langsRes.json();
      voiceData.languages = lData.languages || [];
      populateLanguageFilter();
    }

    renderVoiceGrid(voiceData.voices);
  } catch (err) {
    grid.innerHTML = `<div style="text-align:center;padding:40px;color:#ff6b6b;">Failed to load voices: ${escapeHtml(err.message)}</div>`;
  }
}

function populateLanguageFilter() {
  const select = document.getElementById('voiceLangFilter');
  select.innerHTML = '<option value="">All Languages (' + voiceData.languages.length + ')</option>';
  voiceData.languages.forEach(lang => {
    select.innerHTML += `<option value="${lang.code}">${lang.name}</option>`;
  });
}

function filterVoices() {
  const search = document.getElementById('voiceSearch').value.toLowerCase();
  const lang = document.getElementById('voiceLangFilter').value;
  const gender = document.getElementById('voiceGenderFilter').value;
  const provider = document.getElementById('voiceProviderFilter').value;

  let filtered = voiceData.voices;
  if (lang) filtered = filtered.filter(v => v.language === lang);
  if (gender) filtered = filtered.filter(v => v.gender === gender);
  if (provider) filtered = filtered.filter(v => v.provider === provider);
  if (search) {
    filtered = filtered.filter(v =>
      v.name.toLowerCase().includes(search) ||
      v.language_name.toLowerCase().includes(search) ||
      v.description.toLowerCase().includes(search) ||
      v.style.toLowerCase().includes(search)
    );
  }
  renderVoiceGrid(filtered);
}

function renderVoiceGrid(voices) {
  const grid = document.getElementById('voiceGrid');
  if (!voices.length) {
    grid.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-secondary);">No voices match your filters</div>';
    return;
  }
  grid.innerHTML = voices.map(v => `
    <div class="voice-card ${voiceData.selectedId === v.id ? 'selected' : ''}" onclick="selectVoice('${v.id}')">
      <div class="voice-icon">${v.gender === 'female' ? '👩' : '👨'}</div>
      <div class="voice-info">
        <div class="voice-name">${escapeHtml(v.name)}</div>
        <div class="voice-meta">${escapeHtml(v.language_name)} • ${v.accent} • ${v.provider}</div>
        <div class="voice-desc">${escapeHtml(v.description)}</div>
        <div class="voice-tags">
          <span class="voice-tag">${v.style}</span>
          <span class="voice-tag">${v.gender}</span>
        </div>
      </div>
    </div>
  `).join('');
}

function selectVoice(id) {
  voiceData.selectedId = id;
  const voice = voiceData.voices.find(v => v.id === id);
  document.getElementById('voiceSelectionInfo').innerHTML = `Selected: <strong>${escapeHtml(voice?.name || '')} (${voice?.language_name || ''})</strong>`;
  document.getElementById('voiceConfirmBtn').disabled = false;
  filterVoices(); // re-render to show selection
}

function confirmVoiceSelection() {
  if (!voiceData.selectedId) return;
  const voice = voiceData.voices.find(v => v.id === voiceData.selectedId);
  closeVoicePanel();
  showToast(`Voice "${voice.name}" selected! Your presentation is ready to generate.`, 'success');
}

// ==================== DASHBOARD CARD CLICK HANDLERS ====================
document.addEventListener('DOMContentLoaded', () => {
  const cardAvatars = document.getElementById('cardAvatars');
  const cardVoices = document.getElementById('cardVoices');
  const cardPresentations = document.getElementById('cardPresentations');
  if (cardAvatars) cardAvatars.addEventListener('click', openAvatarPanel);
  if (cardVoices) cardVoices.addEventListener('click', openVoicePanel);
  if (cardPresentations) cardPresentations.addEventListener('click', openPresPanel);
});
