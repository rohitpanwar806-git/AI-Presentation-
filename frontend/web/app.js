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

// ==================== TTS ENGINE (Web Speech API) ====================
const tts = {
  synth: window.speechSynthesis,
  voices: [],
  currentUtterance: null,
  isNarrating: false,

  init() {
    if (!this.synth) return;
    this.voices = this.synth.getVoices();
    if (this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = () => { this.voices = this.synth.getVoices(); };
    }
  },

  findVoice(langCode, gender) {
    const lang = (langCode || 'en-US').replace('_', '-');
    let candidates = this.voices.filter(v => v.lang.startsWith(lang.split('-')[0]));
    // Prefer exact locale match
    const exact = this.voices.filter(v => v.lang.toLowerCase() === lang.toLowerCase());
    if (exact.length) candidates = exact;

    // Prioritize premium/neural voices (non-local = cloud-based, usually higher quality)
    const premiumKeywords = ['online', 'natural', 'neural', 'premium', 'enhanced'];
    const premium = candidates.filter(v => !v.localService || premiumKeywords.some(k => v.name.toLowerCase().includes(k)));
    if (premium.length) candidates = premium;

    // Filter by gender heuristic
    if (gender && candidates.length > 1) {
      const femaleHints = ['female', 'woman', 'zira', 'hazel', 'susan', 'karen', 'samantha', 'victoria', 'fiona', 'jenny', 'aria', 'sara', 'elsa', 'clara', 'emma', 'eva'];
      const maleHints = ['male', 'man', 'david', 'mark', 'james', 'daniel', 'george', 'alex', 'guy', 'ryan', 'eric', 'brian', 'roger'];
      const hints = gender === 'female' ? femaleHints : maleHints;
      const genderMatch = candidates.filter(v => hints.some(h => v.name.toLowerCase().includes(h)));
      if (genderMatch.length) candidates = genderMatch;
    }

    // Among remaining, prefer Microsoft or Google voices (usually better quality)
    const preferred = candidates.filter(v => /microsoft|google/i.test(v.name));
    if (preferred.length) return preferred[0];

    return candidates[0] || this.voices.find(v => v.lang.startsWith('en')) || this.voices[0];
  },

  speak(text, langCode, gender, rate = 0.95, onEnd) {
    if (!this.synth || !text) return;
    this.stop();
    const utterance = new SpeechSynthesisUtterance(text);
    const voice = this.findVoice(langCode, gender);
    if (voice) utterance.voice = voice;
    utterance.rate = rate;
    utterance.pitch = 1.02;
    utterance.volume = 1.0;
    if (onEnd) utterance.onend = onEnd;
    utterance.onerror = () => { if (onEnd) onEnd(); };
    this.currentUtterance = utterance;
    this.synth.speak(utterance);
  },

  stop() {
    if (this.synth) this.synth.cancel();
    this.currentUtterance = null;
  },

  preview(text, langCode, gender) {
    this.speak(text, langCode, gender, 0.95);
  }
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
  tts.init();
  initNavbar();
  initUploadZone();
  initGoogleAuth();

  // Check if this is a shared presentation URL
  const params = new URLSearchParams(window.location.search);
  const sharedToken = params.get('shared');
  if (sharedToken) {
    openSharedViewer(sharedToken);
  } else {
    checkExistingSession();
  }
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
  document.getElementById('helpCentre')?.classList.remove('active');
  document.getElementById('accountSettings')?.classList.remove('active');
  
  // Update nav with profile dropdown
  document.getElementById('navLinks').style.display = 'none';
  const name = state.user?.first_name || state.user?.email?.split('@')[0] || 'User';
  const avatar = state.user?.avatar_url || `https://api.dicebear.com/9.x/avataaars/svg?seed=${encodeURIComponent(name)}&backgroundColor=b6e3f4`;
  const isAdmin = state.user?.is_admin;
  document.getElementById('navActions').innerHTML = `
    <div class="profile-dropdown" id="profileDropdown">
      <button class="profile-trigger" onclick="toggleProfileMenu()">
        <img src="${avatar}" alt="${name}" class="profile-avatar">
        <span class="profile-name">${name}</span>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M3 5L6 8L9 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
      </button>
      <div class="profile-menu" id="profileMenu">
        <div class="profile-menu-header">
          <img src="${avatar}" alt="${name}" class="profile-menu-avatar">
          <div><strong>${name}</strong><br><span style="font-size:11px;color:#94a3b8">${state.user?.email || ''}</span></div>
        </div>
        <div class="profile-menu-divider"></div>
        <button onclick="showDashboard();closeProfileMenu()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg> Dashboard</button>
        <button onclick="openAccountSettings();closeProfileMenu()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15 1.65 1.65 0 003 14.08V14a2 2 0 014 0v.09c0 .66.38 1.26 1 1.51z"/></svg> Account Settings</button>
        <button onclick="openHelpCentre();closeProfileMenu()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><circle cx="12" cy="17" r="0.5"/></svg> Help Centre</button>
        ${isAdmin ? '<button onclick="openAdminPanel();closeProfileMenu()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg> Admin Panel</button>' : ''}
        <div class="profile-menu-divider"></div>
        <button onclick="logout();closeProfileMenu()" class="profile-menu-danger"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg> Sign Out</button>
      </div>
    </div>
  `;

  // Update welcome
  document.getElementById('userName').textContent = name;

  // Load presentations
  loadPresentations();
}

function showLanding() {
  document.getElementById('landing').classList.remove('hidden');
  document.getElementById('dashboard').classList.remove('active');
  document.getElementById('helpCentre')?.classList.remove('active');
  document.getElementById('accountSettings')?.classList.remove('active');
  document.getElementById('navLinks').style.display = '';
  document.getElementById('navActions').innerHTML = `
    <button class="btn btn-ghost" onclick="openAuth('signin')">Log In</button>
    <button class="btn btn-primary" onclick="openAuth('signup')">Get Started Free</button>
  `;
}

function toggleProfileMenu() {
  document.getElementById('profileMenu')?.classList.toggle('open');
}
function closeProfileMenu() {
  document.getElementById('profileMenu')?.classList.remove('open');
}
// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
  if (!e.target.closest('.profile-dropdown')) closeProfileMenu();
});

// ==================== HELP CENTRE ====================
async function openHelpCentre() {
  document.getElementById('landing').classList.add('hidden');
  document.getElementById('dashboard').classList.remove('active');
  document.getElementById('accountSettings')?.classList.remove('active');
  document.getElementById('helpCentre').classList.add('active');
  loadMyTickets();
}

async function loadMyTickets() {
  try {
    const resp = await apiCall('/auth/support/tickets');
    const tickets = resp.items || [];
    const container = document.getElementById('ticketsList');
    if (!tickets.length) {
      container.innerHTML = '<p style="color:#94a3b8;text-align:center;padding:40px">No tickets yet. Submit one if you need help!</p>';
      return;
    }
    container.innerHTML = tickets.map(t => `
      <div class="ticket-card ticket-${t.status}">
        <div class="ticket-header">
          <span class="ticket-category">${t.category}</span>
          <span class="ticket-status status-${t.status}">${t.status}</span>
        </div>
        <h4>${t.subject}</h4>
        <p>${t.description}</p>
        ${t.admin_reply ? `<div class="ticket-reply"><strong>Admin Reply:</strong> ${t.admin_reply}</div>` : ''}
        <span class="ticket-date">${new Date(t.created_at).toLocaleDateString()}</span>
      </div>
    `).join('');
  } catch(e) { console.error('Failed to load tickets', e); }
}

async function submitTicket(e) {
  e.preventDefault();
  const form = e.target;
  const subject = form.querySelector('[name=subject]').value.trim();
  const category = form.querySelector('[name=category]').value;
  const description = form.querySelector('[name=description]').value.trim();
  if (!subject || !description) return showToast('Please fill all fields', 'error');
  try {
    await apiCall('/auth/support/tickets', 'POST', { subject, category, description });
    showToast('Ticket submitted! We\'ll get back to you soon.', 'success');
    form.reset();
    loadMyTickets();
  } catch(e) { showToast(e.message || 'Failed to submit ticket', 'error'); }
}

// ==================== ACCOUNT SETTINGS ====================
async function openAccountSettings() {
  document.getElementById('landing').classList.add('hidden');
  document.getElementById('dashboard').classList.remove('active');
  document.getElementById('helpCentre')?.classList.remove('active');
  document.getElementById('accountSettings').classList.add('active');
  populateAccountSettings();
}

function populateAccountSettings() {
  const u = state.user || {};
  document.getElementById('settingsFirstName').value = u.first_name || '';
  document.getElementById('settingsLastName').value = u.last_name || '';
  document.getElementById('settingsEmail').value = u.email || '';
  document.getElementById('settingsGender').value = u.gender || '';
  document.getElementById('settingsBio').value = u.bio || '';
  // Show/hide password section based on login provider
  const pwSection = document.getElementById('passwordSection');
  if (u.login_provider === 'google') {
    pwSection.style.display = 'none';
  } else {
    pwSection.style.display = '';
  }
}

async function saveProfile(e) {
  e.preventDefault();
  try {
    const resp = await apiCall('/auth/profile', 'PUT', {
      first_name: document.getElementById('settingsFirstName').value.trim(),
      last_name: document.getElementById('settingsLastName').value.trim(),
      gender: document.getElementById('settingsGender').value.trim(),
      bio: document.getElementById('settingsBio').value.trim(),
    });
    state.user = { ...state.user, ...resp };
    showToast('Profile updated!', 'success');
    showDashboard(); // refresh navbar
    openAccountSettings(); // re-open settings
  } catch(e) { showToast(e.message || 'Failed to update profile', 'error'); }
}

async function changePassword(e) {
  e.preventDefault();
  const current = document.getElementById('currentPassword').value;
  const newPw = document.getElementById('newPassword').value;
  const confirm = document.getElementById('confirmPassword').value;
  if (newPw !== confirm) return showToast('Passwords do not match', 'error');
  if (newPw.length < 8) return showToast('Password must be at least 8 characters', 'error');
  try {
    await apiCall('/auth/change-password', 'POST', { current_password: current, new_password: newPw });
    showToast('Password changed successfully!', 'success');
    document.getElementById('currentPassword').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('confirmPassword').value = '';
  } catch(e) { showToast(e.message || 'Failed to change password', 'error'); }
}

async function changeEmail(e) {
  e.preventDefault();
  const newEmail = document.getElementById('newEmail').value.trim();
  const password = document.getElementById('emailChangePassword').value;
  if (!newEmail || !password) return showToast('Fill all fields', 'error');
  try {
    const resp = await apiCall('/auth/change-email', 'POST', { new_email: newEmail, password });
    state.user = { ...state.user, ...resp.user };
    showToast('Email updated!', 'success');
    document.getElementById('settingsEmail').value = newEmail;
    document.getElementById('newEmail').value = '';
    document.getElementById('emailChangePassword').value = '';
  } catch(e) { showToast(e.message || 'Failed to change email', 'error'); }
}

// ==================== ADMIN PANEL ====================
async function openAdminPanel() {
  document.getElementById('landing').classList.add('hidden');
  document.getElementById('dashboard').classList.remove('active');
  document.getElementById('helpCentre')?.classList.remove('active');
  document.getElementById('accountSettings')?.classList.remove('active');
  document.getElementById('adminPanel').classList.add('active');
  loadAdminUsers();
  loadAdminTickets();
}

async function loadAdminUsers() {
  try {
    const resp = await apiCall('/auth/admin/users');
    document.getElementById('adminUserCount').textContent = resp.total || 0;
    document.getElementById('adminVerifiedCount').textContent = resp.verified || 0;
    const container = document.getElementById('adminUsersList');
    container.innerHTML = (resp.items || []).map(u => `
      <tr>
        <td>${u.name}</td>
        <td>${u.email}</td>
        <td><span class="badge ${u.is_verified ? 'badge-success' : 'badge-warning'}">${u.is_verified ? 'Verified' : 'Pending'}</span></td>
        <td>${u.is_admin ? '⭐ Admin' : 'User'}</td>
        <td>${new Date(u.created_at).toLocaleDateString()}</td>
      </tr>
    `).join('');
  } catch(e) { console.error('Admin users load failed', e); }
}

async function loadAdminTickets() {
  try {
    const resp = await apiCall('/auth/admin/tickets');
    document.getElementById('adminTicketCount').textContent = resp.total || 0;
    document.getElementById('adminOpenTickets').textContent = resp.open || 0;
    const container = document.getElementById('adminTicketsList');
    container.innerHTML = (resp.items || []).map(t => `
      <div class="admin-ticket">
        <div class="admin-ticket-header">
          <span class="ticket-category">${t.category}</span>
          <span class="ticket-status status-${t.status}">${t.status}</span>
          <span class="ticket-date">${new Date(t.created_at).toLocaleDateString()}</span>
        </div>
        <h4>${t.subject}</h4>
        <p style="color:#94a3b8;font-size:12px">From: ${t.user_email}</p>
        <p>${t.description}</p>
        ${t.admin_reply ? `<div class="ticket-reply"><strong>Your Reply:</strong> ${t.admin_reply}</div>` : ''}
        ${t.status === 'open' ? `
          <form onsubmit="replyToTicket(event, ${t.id})" class="ticket-reply-form">
            <textarea name="reply" placeholder="Type your reply..." required></textarea>
            <button type="submit" class="btn btn-primary btn-sm">Reply & Resolve</button>
          </form>
        ` : ''}
      </div>
    `).join('') || '<p style="color:#94a3b8;text-align:center">No tickets</p>';
  } catch(e) { console.error('Admin tickets load failed', e); }
}

async function replyToTicket(e, ticketId) {
  e.preventDefault();
  const reply = e.target.querySelector('[name=reply]').value.trim();
  if (!reply) return;
  try {
    await apiCall(`/auth/admin/tickets/${ticketId}/reply`, 'POST', { reply, status: 'resolved' });
    showToast('Ticket resolved!', 'success');
    loadAdminTickets();
  } catch(e) { showToast(e.message || 'Failed to reply', 'error'); }
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
  // Record view
  try { await apiRequest(`/presentations/${id}/view`, { method: 'POST' }); } catch {}
  const p = presData.presentations.find(x => x.id === id);
  if (p) {
    p.analytics.views++;
    renderPresList();
  }
  openViewer(p);
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

// ==================== PRESENTATION VIEWER ====================
let viewer = {
  presentation: null,
  slides: [],
  currentSlide: 0,
  isPlaying: false,
  timer: null,
  elapsed: 0,
  slideInterval: 8, // seconds per slide
  avatarInfo: null,
  voiceInfo: null,
};

function generateSlides(presentation) {
  const title = presentation.title || presentation.filename || 'Untitled';
  const fileType = presentation.file_type || 'Document';
  const created = formatDate(presentation.created_at);

  return [
    {
      title: title,
      body: `${fileType} Presentation`,
      bullets: null,
      type: 'title'
    },
    {
      title: 'Presentation Overview',
      body: 'This AI-generated presentation covers the key topics from your uploaded document.',
      bullets: [
        'Content extracted and analyzed by AI',
        'Presented by your selected avatar',
        'Natural voice narration',
        `Created on ${created}`
      ],
      type: 'content'
    },
    {
      title: 'Key Highlights',
      body: null,
      bullets: [
        'AI-powered content analysis and structuring',
        'Professional avatar with natural gestures',
        'Multi-language voice synthesis',
        'Engagement tracking and analytics',
        'Shareable presentation link'
      ],
      type: 'content'
    },
    {
      title: 'Content Summary',
      body: `Your ${fileType.toLowerCase()} "${title}" has been processed and formatted into a professional presentation. The AI presenter delivers your content with natural speech patterns and professional delivery.`,
      bullets: null,
      type: 'content'
    },
    {
      title: 'Next Steps',
      body: null,
      bullets: [
        'Customize avatar appearance and style',
        'Choose from 80+ natural voices',
        'Add custom branding elements',
        'Share via link or embed code',
        'Track viewer engagement analytics'
      ],
      type: 'content'
    },
    {
      title: 'Thank You',
      body: `Presented by AI • Powered by PresenterAI`,
      bullets: null,
      type: 'title'
    }
  ];
}

function openViewer(presentation) {
  if (!presentation) return;
  viewer.presentation = presentation;
  // Use generated slides if available, otherwise generate placeholders
  viewer.slides = (presentation.slides && presentation.slides.length) ? presentation.slides : generateSlides(presentation);
  viewer.currentSlide = 0;
  viewer.elapsed = 0;
  viewer.isPlaying = false;

  // Reset Q&A
  qaState.chatHistory = [];
  const qaMessages = document.getElementById('qaMessages');
  qaMessages.innerHTML = '<div class="qa-msg assistant">Hi! I\'m your AI tutor for this presentation. Ask me anything about the content — I\'ll explain it clearly.</div>';
  document.getElementById('viewerQA').classList.remove('active');

  // Resolve avatar
  const avatarId = presentation.avatar_id;
  if (avatarId && avatarData.avatars.length) {
    viewer.avatarInfo = avatarData.avatars.find(a => a.id === avatarId) || null;
  }
  if (!viewer.avatarInfo) {
    // Use a default avatar
    viewer.avatarInfo = {
      name: 'AI Presenter',
      thumbnail: 'https://api.dicebear.com/9.x/avataaars/svg?seed=AIPresenter&backgroundColor=b6e3f4&top=shortFlat&mouth=smile'
    };
  }

  // Set up UI
  document.getElementById('viewerTitle').childNodes[0].textContent = presentation.title || presentation.filename;
  document.getElementById('viewerMeta').textContent = `${presentation.file_type} • ${formatFileSize(presentation.file_size)}`;
  document.getElementById('pipAvatarImg').src = viewer.avatarInfo.thumbnail;
  document.getElementById('pipAvatarName').textContent = viewer.avatarInfo.name;

  const totalTime = viewer.slides.length * viewer.slideInterval;
  document.getElementById('viewerTimeTotal').textContent = formatTime(totalTime);
  document.getElementById('viewerTimeElapsed').textContent = '0:00';
  document.getElementById('viewerProgressFill').style.width = '0%';

  renderSlide();
  document.getElementById('presentationViewer').classList.add('active');
  document.body.style.overflow = 'hidden';

  // Show play prompt for first interaction (Web Speech API requires user gesture)
  if (presentation._shared) {
    _showPlayPrompt();
  } else {
    // For authenticated users opening their own presentations, try auto-play
    setTimeout(() => togglePlayPause(), 500);
  }
}

function _showPlayPrompt() {
  let prompt = document.getElementById('playPromptOverlay');
  if (!prompt) {
    prompt = document.createElement('div');
    prompt.id = 'playPromptOverlay';
    prompt.style.cssText = 'position:fixed;inset:0;z-index:4000;background:rgba(10,10,30,0.85);display:flex;align-items:center;justify-content:center;flex-direction:column;cursor:pointer;';
    prompt.innerHTML = `
      <div style="font-size:72px;margin-bottom:20px;animation:pulse 1.5s infinite;">▶</div>
      <h2 style="color:#fff;margin-bottom:8px;font-family:system-ui;">Click to Start Presentation</h2>
      <p style="color:#94a3b8;font-family:system-ui;">Your AI teacher is ready to present</p>
    `;
    prompt.onclick = () => {
      prompt.remove();
      tts.init(); // Re-init voices on user gesture
      togglePlayPause();
    };
    document.body.appendChild(prompt);
  }
}

function closeViewer() {
  pausePlayback();
  tts.stop();
  document.getElementById('presentationViewer').classList.remove('active');
  document.body.style.overflow = '';

  // If shared viewer, redirect to homepage
  if (viewer.presentation?._shared) {
    window.location.href = window.location.origin;
    return;
  }
  viewer.presentation = null;
}

function renderSlide() {
  const slide = viewer.slides[viewer.currentSlide];
  if (!slide) return;

  const total = viewer.slides.length;
  const num = viewer.currentSlide + 1;

  document.getElementById('slideNumber').textContent = `${num} / ${total}`;
  document.getElementById('slideNavInfo').textContent = `Slide ${num} of ${total}`;

  const titleEl = document.getElementById('slideTitle');
  const bodyEl = document.getElementById('slideBody');
  const contentEl = document.getElementById('slideContent');

  titleEl.textContent = slide.title;

  // Build body content
  let bodyHtml = '';
  if (slide.body) {
    bodyHtml += `<p>${escapeHtml(slide.body)}</p>`;
  }
  if (slide.bullets) {
    bodyHtml += '<ul>' + slide.bullets.map(b => `<li>${escapeHtml(b)}</li>`).join('') + '</ul>';
  }
  bodyEl.innerHTML = bodyHtml;

  // Animate slide in
  contentEl.style.animation = 'none';
  contentEl.offsetHeight; // force reflow
  contentEl.style.animation = 'fadeInUp 0.5s ease';

  // Narrate slide if playing
  if (viewer.isPlaying) {
    narrateSlide(slide);
  }
}

function narrateSlide(slide) {
  tts.stop();
  // Use custom script if available, otherwise build from slide content
  const scripts = viewer.presentation?.scripts;
  let narration = '';
  if (scripts && scripts[viewer.currentSlide]) {
    narration = scripts[viewer.currentSlide].narration || '';
  }
  if (!narration) {
    // Build a natural, conversational narration from slide content
    const slideIndex = viewer.currentSlide;
    const totalSlides = viewer.slides.length;
    let prefix = '';
    if (slideIndex === 0) prefix = "Welcome! Let me present to you: ";
    else if (slideIndex === totalSlides - 1) prefix = "To wrap up, ";
    else if (slideIndex === 1) prefix = "Let's start with ";
    else prefix = "";

    narration = prefix + slide.title + '. ';
    if (slide.body) narration += slide.body + ' ';
    if (slide.bullets && slide.bullets.length) {
      narration += slide.bullets.join('. ') + '.';
    }
  }

  // Show captions
  showCaption(narration);

  // Get voice settings from the selected voice
  const selectedVoice = voiceData.voices.find(v => v.id === voiceData.selectedId);
  const lang = selectedVoice?.language || 'en-US';
  const gender = selectedVoice?.gender || 'female';

  tts.speak(narration, lang, gender, 0.95, () => { hideCaption(); });
}

function showCaption(text) {
  let el = document.getElementById('viewerCaptions');
  if (!el) return;
  // Show text with typing effect (truncate long text)
  const display = text.length > 200 ? text.substring(0, 200) + '...' : text;
  el.textContent = display;
  el.classList.add('active');
}

function hideCaption() {
  let el = document.getElementById('viewerCaptions');
  if (el) el.classList.remove('active');
}

function togglePlayPause() {
  if (viewer.isPlaying) {
    pausePlayback();
  } else {
    startPlayback();
  }
}

function startPlayback() {
  viewer.isPlaying = true;
  document.getElementById('playPauseBtn').textContent = '⏸';
  document.getElementById('pipStatus').innerHTML = '<span class="pip-speaking-dot"></span> Speaking';
  document.getElementById('soundWaves').classList.remove('paused');

  // Ensure TTS voices are loaded (may need user gesture context)
  if (tts.synth && tts.voices.length === 0) {
    tts.voices = tts.synth.getVoices();
  }

  // Narrate current slide when starting
  const slide = viewer.slides[viewer.currentSlide];
  if (slide) narrateSlide(slide);

  viewer.timer = setInterval(() => {
    viewer.elapsed++;
    const totalTime = viewer.slides.length * viewer.slideInterval;
    const progress = (viewer.elapsed / totalTime) * 100;

    document.getElementById('viewerProgressFill').style.width = Math.min(progress, 100) + '%';
    document.getElementById('viewerTimeElapsed').textContent = formatTime(viewer.elapsed);

    // Advance slide
    const targetSlide = Math.floor(viewer.elapsed / viewer.slideInterval);
    if (targetSlide !== viewer.currentSlide && targetSlide < viewer.slides.length) {
      viewer.currentSlide = targetSlide;
      renderSlide();
    }

    // End
    if (viewer.elapsed >= totalTime) {
      pausePlayback();
      document.getElementById('pipStatus').innerHTML = '✅ Finished';
      document.getElementById('soundWaves').classList.add('paused');
    }
  }, 1000);
}

function pausePlayback() {
  viewer.isPlaying = false;
  if (viewer.timer) clearInterval(viewer.timer);
  viewer.timer = null;
  tts.stop();
  document.getElementById('playPauseBtn').textContent = '▶';
  const statusEl = document.getElementById('pipStatus');
  if (statusEl && !statusEl.textContent.includes('Finished')) {
    statusEl.innerHTML = '⏸ Paused';
  }
  document.getElementById('soundWaves').classList.add('paused');
}

function nextSlide() {
  if (viewer.currentSlide < viewer.slides.length - 1) {
    tts.stop();
    viewer.currentSlide++;
    viewer.elapsed = viewer.currentSlide * viewer.slideInterval;
    renderSlide();
    updateProgress();
  }
}

function prevSlide() {
  if (viewer.currentSlide > 0) {
    tts.stop();
    viewer.currentSlide--;
    viewer.elapsed = viewer.currentSlide * viewer.slideInterval;
    renderSlide();
    updateProgress();
  }
}

function seekViewer(event) {
  const bar = document.getElementById('viewerProgress');
  const rect = bar.getBoundingClientRect();
  const pct = (event.clientX - rect.left) / rect.width;
  const totalTime = viewer.slides.length * viewer.slideInterval;
  viewer.elapsed = Math.floor(pct * totalTime);
  viewer.currentSlide = Math.min(Math.floor(viewer.elapsed / viewer.slideInterval), viewer.slides.length - 1);
  renderSlide();
  updateProgress();
}

function updateProgress() {
  const totalTime = viewer.slides.length * viewer.slideInterval;
  const progress = (viewer.elapsed / totalTime) * 100;
  document.getElementById('viewerProgressFill').style.width = Math.min(progress, 100) + '%';
  document.getElementById('viewerTimeElapsed').textContent = formatTime(viewer.elapsed);
}

function toggleViewerFullscreen() {
  const el = document.getElementById('presentationViewer');
  if (!document.fullscreenElement) {
    el.requestFullscreen?.() || el.webkitRequestFullscreen?.();
  } else {
    document.exitFullscreen?.() || document.webkitExitFullscreen?.();
  }
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

// ==================== GENERATE PANEL ====================
let generateState = {
  presentationId: null,
  isGenerating: false,
  mode: 'generate', // 'generate' or 'present_deck'
};

function setGenerateMode(mode) {
  generateState.mode = mode;
  document.getElementById('modeGenerate').classList.toggle('active', mode === 'generate');
  document.getElementById('modeDeck').classList.toggle('active', mode === 'present_deck');
}

function openGeneratePanel() {
  const panel = document.getElementById('generatePanel');
  panel.classList.add('active');
  document.body.style.overflow = 'hidden';

  // Get the latest uploaded presentation
  const latestPres = presData.presentations[0];
  if (latestPres) {
    generateState.presentationId = latestPres.id;
    document.getElementById('genDocName').textContent = latestPres.title || latestPres.filename;
  }

  // Show selected avatar
  const avatarId = avatarData.selectedId;
  if (avatarId && avatarData.avatars.length) {
    const avatar = avatarData.avatars.find(a => a.id === avatarId);
    if (avatar) document.getElementById('genAvatarName').textContent = avatar.name;
  }

  // Show selected voice
  const voiceId = voiceData.selectedId;
  if (voiceId && voiceData.voices.length) {
    const voice = voiceData.voices.find(v => v.id === voiceId);
    if (voice) document.getElementById('genVoiceName').textContent = voice.name;
  }

  // Reset progress
  document.getElementById('genProgress').classList.remove('active');
  for (let i = 1; i <= 5; i++) {
    const step = document.getElementById(`genStep${i}`);
    step.classList.remove('active', 'done');
    step.querySelector('.gen-step-icon').textContent = '○';
  }
  document.getElementById('generateBtn').disabled = false;
  document.getElementById('generateBtn').textContent = '✨ Generate Presentation';
}

function closeGeneratePanel() {
  document.getElementById('generatePanel').classList.remove('active');
  document.body.style.overflow = '';
}

async function startGeneration() {
  if (generateState.isGenerating) return;
  generateState.isGenerating = true;

  const btn = document.getElementById('generateBtn');
  btn.disabled = true;
  btn.textContent = 'Generating...';

  const progress = document.getElementById('genProgress');
  progress.classList.add('active');

  // Step management — only advance when real progress is confirmed
  const steps = ['genStep1', 'genStep2', 'genStep3', 'genStep4', 'genStep5'];
  let currentStep = 0;

  function resetSteps() {
    steps.forEach(id => {
      const el = document.getElementById(id);
      el.classList.remove('active', 'done', 'error');
      el.querySelector('.gen-step-icon').textContent = '○';
    });
    currentStep = 0;
  }

  function setStepActive(index) {
    if (index < steps.length) {
      const el = document.getElementById(steps[index]);
      el.classList.add('active');
      el.querySelector('.gen-step-icon').textContent = '◉';
    }
  }

  function setStepDone(index) {
    if (index < steps.length) {
      const el = document.getElementById(steps[index]);
      el.classList.remove('active');
      el.classList.add('done');
      el.querySelector('.gen-step-icon').textContent = '✓';
    }
  }

  function setStepError(index) {
    if (index < steps.length) {
      const el = document.getElementById(steps[index]);
      el.classList.remove('active');
      el.classList.add('error');
      el.querySelector('.gen-step-icon').textContent = '✕';
    }
  }

  resetSteps();
  setStepActive(0); // Step 1: Extracting document

  // Call the generate API
  const presId = generateState.presentationId;
  if (!presId) {
    showToast('No presentation to generate', 'error');
    setStepError(0);
    generateState.isGenerating = false;
    btn.disabled = false;
    btn.textContent = '✨ Generate Presentation';
    return;
  }

  try {
    // Step 1 done → Step 2 active (after a realistic delay for extraction)
    await new Promise(r => setTimeout(r, 800));
    setStepDone(0);
    setStepActive(1); // Analyzing key topics

    const res = await apiRequest(`/presentations/${presId}/generate`, {
      method: 'POST',
      body: JSON.stringify({
        avatar_id: avatarData.selectedId || null,
        voice_id: voiceData.selectedId || null,
        mode: generateState.mode || 'generate'
      })
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Server error (${res.status})`);
    }

    const data = await res.json();

    if (data && data.status === 'success') {
      // Mark remaining steps done in sequence with visual feedback
      setStepDone(1);
      setStepActive(2);
      await new Promise(r => setTimeout(r, 400));
      setStepDone(2);
      setStepActive(3);
      await new Promise(r => setTimeout(r, 400));
      setStepDone(3);
      setStepActive(4);
      await new Promise(r => setTimeout(r, 400));
      setStepDone(4);

      // Store generated slides in the presentation
      const pres = presData.presentations.find(p => p.id === presId);
      if (pres) {
        pres.slides = data.presentation.slides;
        pres.status = 'ready';
        pres.avatar_id = data.presentation.avatar_id;
        pres.voice_id = data.presentation.voice_id;
      }

      btn.textContent = '✅ Generated! Opening Viewer...';
      showToast('Presentation generated! Your AI avatar is ready to present.', 'success');

      // Refresh presentations list
      loadPresentations();

      // Open viewer after a short delay
      setTimeout(() => {
        closeGeneratePanel();
        generateState.isGenerating = false;
        if (pres) openViewer(pres);
      }, 1500);
    } else {
      throw new Error(data?.detail || 'Generation failed — server returned an error');
    }
  } catch (err) {
    // Mark the current step as errored, leave previous done steps as-is
    const failedStep = Math.min(currentStep, steps.length - 1);
    // Find which step is currently active
    for (let i = 0; i < steps.length; i++) {
      const el = document.getElementById(steps[i]);
      if (el.classList.contains('active')) {
        setStepError(i);
        break;
      }
    }
    btn.disabled = false;
    btn.textContent = '✨ Retry Generation';
    generateState.isGenerating = false;
    showToast(err.message || 'Generation failed. Please try again.', 'error');
  }
}

// ==================== Q&A CHAT ====================
let qaState = {
  chatHistory: [],
  isAsking: false,
};

function toggleQAPanel() {
  const panel = document.getElementById('viewerQA');
  panel.classList.toggle('active');
  if (panel.classList.contains('active')) {
    document.getElementById('qaInput').focus();
  }
}

async function sendQuestion() {
  const input = document.getElementById('qaInput');
  const question = input.value.trim();
  if (!question || qaState.isAsking) return;

  qaState.isAsking = true;
  input.value = '';
  document.getElementById('qaSendBtn').disabled = true;

  // Add user message to chat
  addQAMessage(question, 'user');
  qaState.chatHistory.push({ role: 'user', content: question });

  // Show typing indicator
  const typingId = addQAMessage('Thinking...', 'assistant typing');

  const pres = viewer.presentation;
  if (!pres) {
    removeQAMessage(typingId);
    addQAMessage("I couldn't find the presentation context. Please try again.", 'assistant');
    qaState.isAsking = false;
    document.getElementById('qaSendBtn').disabled = false;
    return;
  }

  try {
    let res;
    if (pres._shared && pres._share_token) {
      // Public shared viewer — use public Q&A endpoint (no auth)
      res = await fetch(`${API_BASE}/shared/${pres._share_token}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, chat_history: qaState.chatHistory.slice(-6) })
      });
    } else {
      // Authenticated user
      res = await apiRequest(`/presentations/${pres.id}/ask`, {
        method: 'POST',
        body: JSON.stringify({ question, chat_history: qaState.chatHistory.slice(-6) })
      });
    }

    removeQAMessage(typingId);

    if (res.ok) {
      const data = await res.json();
      if (data.answer) {
        addQAMessage(data.answer, 'assistant');
        qaState.chatHistory.push({ role: 'assistant', content: data.answer });

        // Narrate the answer with the avatar's voice
        if (viewer.isPlaying || pres._shared) {
          const selectedVoice = voiceData.voices.find(v => v.id === voiceData.selectedId);
          const lang = selectedVoice?.language || 'en-US';
          const gender = selectedVoice?.gender || 'female';
          tts.speak(data.answer, lang, gender, 0.95);
        }
      } else {
        addQAMessage("I'm sorry, I couldn't process that question. Please try again.", 'assistant');
      }
    } else {
      addQAMessage("I'm sorry, I couldn't process that question. Please try again.", 'assistant');
    }
  } catch (err) {
    removeQAMessage(typingId);
    addQAMessage("Sorry, I'm having trouble answering right now. Please try again.", 'assistant');
  }

  qaState.isAsking = false;
  document.getElementById('qaSendBtn').disabled = false;
}

function addQAMessage(text, className) {
  const container = document.getElementById('qaMessages');
  const msgId = 'qa-msg-' + Date.now();
  const div = document.createElement('div');
  div.className = `qa-msg ${className}`;
  div.id = msgId;
  div.textContent = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return msgId;
}

function removeQAMessage(msgId) {
  const el = document.getElementById(msgId);
  if (el) el.remove();
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
    if (document.getElementById('generatePanel')?.classList.contains('active')) closeGeneratePanel();
    if (document.getElementById('presentationViewer')?.classList.contains('active')) closeViewer();
    if (document.getElementById('quizPanel')?.classList.contains('active')) closeQuizPanel();
    if (document.getElementById('scriptEditor')?.classList.contains('active')) closeScriptEditor();
  }
  // Arrow keys for slide navigation when viewer is open
  if (document.getElementById('presentationViewer')?.classList.contains('active')) {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') nextSlide();
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') prevSlide();
    if (e.key === ' ') { e.preventDefault(); togglePlayPause(); }
  }
});


// ==================== QUIZ PANEL ====================
let quizState = { questions: [], currentQ: 0, score: 0, answered: [] };

async function openQuizPanel() {
  const pres = viewer.presentation;
  if (!pres) return showToast('Open a presentation first', 'error');

  const panel = document.getElementById('quizPanel');
  if (!panel) return;
  panel.classList.add('active');
  document.getElementById('quizContent').innerHTML = '<div style="text-align:center;padding:40px;"><div class="loading-spinner"></div><p>Generating quiz questions...</p></div>';

  // For shared presentations, use pre-loaded quiz data or generate via shared endpoint
  if (pres._shared && pres._quiz && pres._quiz.length) {
    quizState = { questions: pres._quiz, currentQ: 0, score: 0, answered: [] };
    renderQuizQuestion();
    return;
  }

  try {
    let res;
    if (pres._shared && pres._share_token) {
      // Generate quiz for shared viewers via public Q&A (ask for quiz)
      res = await fetch(`${API_BASE}/shared/${pres._share_token}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: '__generate_quiz__', chat_history: [] })
      });
    } else {
      res = await fetch(`${API_BASE}/presentations/${pres.id}/quiz`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${state.token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ num_questions: 5 })
      });
    }
    const data = await res.json();
    const quizData = data.quiz || pres._quiz;
    if (quizData && quizData.length) {
      quizState = { questions: quizData, currentQ: 0, score: 0, answered: [] };
      renderQuizQuestion();
    } else {
      document.getElementById('quizContent').innerHTML = '<p style="text-align:center;padding:40px;color:var(--text-secondary);">Could not generate quiz. Try again after generating the presentation.</p>';
    }
  } catch (err) {
    document.getElementById('quizContent').innerHTML = '<p style="text-align:center;padding:40px;color:#ef4444;">Failed to generate quiz. Please try again.</p>';
  }
}

function renderQuizQuestion() {
  const q = quizState.questions[quizState.currentQ];
  if (!q) return renderQuizResults();

  const total = quizState.questions.length;
  const num = quizState.currentQ + 1;
  const isAnswered = quizState.answered[quizState.currentQ] !== undefined;

  let html = `
    <div class="quiz-progress">Question ${num} of ${total} • Score: ${quizState.score}/${total}</div>
    <div class="quiz-question">${escapeHtml(q.question)}</div>
    <div class="quiz-options">
  `;

  q.options.forEach((opt, i) => {
    let cls = 'quiz-option';
    if (isAnswered) {
      if (i === q.correct_answer) cls += ' correct';
      else if (i === quizState.answered[quizState.currentQ] && i !== q.correct_answer) cls += ' wrong';
    }
    const disabled = isAnswered ? 'style="pointer-events:none"' : '';
    html += `<div class="${cls}" ${disabled} onclick="answerQuiz(${i})">${escapeHtml(opt)}</div>`;
  });

  html += '</div>';
  if (isAnswered) {
    html += `<div class="quiz-explanation">💡 ${escapeHtml(q.explanation || '')}</div>`;
    html += `<button class="btn-primary" onclick="nextQuizQuestion()" style="margin-top:16px;">${num < total ? 'Next Question →' : 'See Results'}</button>`;
  }

  document.getElementById('quizContent').innerHTML = html;
}

function answerQuiz(optionIndex) {
  const q = quizState.questions[quizState.currentQ];
  quizState.answered[quizState.currentQ] = optionIndex;
  if (optionIndex === q.correct_answer) quizState.score++;
  renderQuizQuestion();
}

function nextQuizQuestion() {
  quizState.currentQ++;
  renderQuizQuestion();
}

function renderQuizResults() {
  const total = quizState.questions.length;
  const pct = Math.round((quizState.score / total) * 100);
  const emoji = pct >= 80 ? '🎉' : pct >= 60 ? '👍' : '📚';

  document.getElementById('quizContent').innerHTML = `
    <div style="text-align:center;padding:30px;">
      <div style="font-size:48px;margin-bottom:16px;">${emoji}</div>
      <h3 style="margin-bottom:8px;">Quiz Complete!</h3>
      <p style="font-size:24px;font-weight:700;color:var(--accent);margin-bottom:8px;">${quizState.score} / ${total} correct (${pct}%)</p>
      <p style="color:var(--text-secondary);margin-bottom:24px;">${pct >= 80 ? 'Excellent work!' : pct >= 60 ? 'Good effort! Review the slides for missed topics.' : 'Consider reviewing the presentation again.'}</p>
      <button class="btn-primary" onclick="quizState.currentQ=0;quizState.score=0;quizState.answered=[];renderQuizQuestion();">Retry Quiz</button>
    </div>
  `;
}

function closeQuizPanel() {
  document.getElementById('quizPanel')?.classList.remove('active');
}


// ==================== SCRIPT EDITOR ====================

async function openScriptEditor() {
  const pres = viewer.presentation;
  if (!pres) return showToast('Open a presentation first', 'error');
  if (!pres.slides || !pres.slides.length) return showToast('Generate presentation first', 'error');

  const panel = document.getElementById('scriptEditor');
  if (!panel) return;
  panel.classList.add('active');

  // If no scripts yet, generate them
  if (!pres.scripts || !pres.scripts.length) {
    document.getElementById('scriptContent').innerHTML = '<div style="text-align:center;padding:40px;"><div class="loading-spinner"></div><p>Generating narration scripts...</p></div>';
    try {
      const res = await fetch(`${API_BASE}/presentations/${pres.id}/scripts?style=professional`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${state.token}` }
      });
      const data = await res.json();
      if (data.scripts) pres.scripts = data.scripts;
    } catch (err) { /* fallback to empty */ }
  }

  renderScriptEditor();
}

function renderScriptEditor() {
  const pres = viewer.presentation;
  const scripts = pres?.scripts || [];
  const slides = pres?.slides || [];

  let html = '<div class="script-list">';
  slides.forEach((slide, i) => {
    const script = scripts[i] || { narration: '', duration_seconds: 10 };
    html += `
      <div class="script-item">
        <div class="script-slide-label">Slide ${i + 1}: ${escapeHtml(slide.title)}</div>
        <textarea class="script-textarea" id="script_${i}" rows="3" placeholder="Enter narration for this slide...">${escapeHtml(script.narration || '')}</textarea>
        <div class="script-meta">${script.duration_seconds || 10}s estimated</div>
      </div>
    `;
  });
  html += '</div>';
  html += '<div style="padding:16px;display:flex;gap:12px;justify-content:flex-end;">';
  html += '<button class="btn-secondary" onclick="regenerateScripts()">🔄 Regenerate</button>';
  html += '<button class="btn-primary" onclick="saveScripts()">💾 Save Scripts</button>';
  html += '</div>';

  document.getElementById('scriptContent').innerHTML = html;
}

async function regenerateScripts() {
  const pres = viewer.presentation;
  if (!pres) return;
  document.getElementById('scriptContent').innerHTML = '<div style="text-align:center;padding:40px;"><div class="loading-spinner"></div><p>Regenerating scripts...</p></div>';
  try {
    const res = await fetch(`${API_BASE}/presentations/${pres.id}/scripts?style=professional`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    const data = await res.json();
    if (data.scripts) { pres.scripts = data.scripts; renderScriptEditor(); }
  } catch (err) { showToast('Failed to regenerate', 'error'); }
}

async function saveScripts() {
  const pres = viewer.presentation;
  if (!pres) return;
  const slides = pres.slides || [];
  const scripts = slides.map((_, i) => {
    const el = document.getElementById(`script_${i}`);
    return { slide_index: i, narration: el?.value || '', duration_seconds: Math.max(5, Math.ceil((el?.value?.split(' ').length || 10) / 2.5)) };
  });

  try {
    const res = await fetch(`${API_BASE}/presentations/${pres.id}/scripts`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${state.token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ scripts })
    });
    if (res.ok) { pres.scripts = scripts; showToast('Scripts saved!', 'success'); }
  } catch (err) { showToast('Failed to save', 'error'); }
}

function closeScriptEditor() {
  document.getElementById('scriptEditor')?.classList.remove('active');
}


// ==================== SHARE / PUBLISH ====================

async function publishPresentation() {
  const pres = viewer.presentation;
  if (!pres) return;
  if (!pres.slides?.length) return showToast('Generate presentation first', 'error');

  try {
    const res = await fetch(`${API_BASE}/presentations/${pres.id}/publish`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    const data = await res.json();
    if (data.share_token) {
      pres.share_token = data.share_token;
      const shareUrl = `${window.location.origin}?shared=${data.share_token}`;
      showShareDialog(shareUrl, data.expires_in_hours || 24);
    } else {
      showToast(data.detail || 'Failed to publish', 'error');
    }
  } catch (err) { showToast('Publish failed', 'error'); }
}

function showShareDialog(url, expiryHours) {
  const dialog = document.createElement('div');
  dialog.className = 'generate-overlay active';
  dialog.id = 'shareDialog';
  dialog.style.zIndex = '3500';
  dialog.innerHTML = `
    <div class="generate-card" style="max-width:480px;">
      <div style="text-align:center;padding:24px;">
        <div style="font-size:48px;margin-bottom:16px;">🔗</div>
        <h3 style="margin-bottom:8px;">Presentation Published!</h3>
        <p style="color:var(--text-secondary);margin-bottom:6px;">Anyone with this link can view & ask questions</p>
        <p style="color:#f59e0b;font-size:0.8rem;margin-bottom:20px;">⏱ Link expires in ${expiryHours} hours</p>
        <div style="display:flex;gap:8px;margin-bottom:20px;">
          <input type="text" value="${url}" readonly id="shareUrlInput" style="flex:1;padding:10px 14px;border-radius:8px;border:1px solid var(--glass-border);background:var(--bg-card);color:#fff;font-size:13px;">
          <button class="btn-primary" onclick="copyShareUrl()">📋 Copy</button>
        </div>
        <button class="btn-secondary" onclick="document.getElementById('shareDialog').remove()">Close</button>
      </div>
    </div>
  `;
  document.body.appendChild(dialog);
}

function copyShareUrl() {
  const input = document.getElementById('shareUrlInput');
  if (input) {
    navigator.clipboard.writeText(input.value);
    showToast('Link copied to clipboard!', 'success');
  }
}


// ==================== SUMMARY PANEL ====================

async function openSummaryPanel() {
  const pres = viewer.presentation;
  if (!pres) return;

  const panel = document.getElementById('summaryPanel');
  if (!panel) return;
  panel.classList.add('active');
  document.getElementById('summaryContent').innerHTML = '<div style="text-align:center;padding:40px;"><div class="loading-spinner"></div><p>Analyzing document...</p></div>';

  try {
    const res = await fetch(`${API_BASE}/presentations/${pres.id}/summary`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    const data = await res.json();
    if (data.summary) renderSummary(data.summary);
    else document.getElementById('summaryContent').innerHTML = '<p style="padding:24px;color:var(--text-secondary);">Summary unavailable.</p>';
  } catch (err) {
    document.getElementById('summaryContent').innerHTML = '<p style="padding:24px;color:#ef4444;">Failed to load summary.</p>';
  }
}

function renderSummary(summary) {
  let html = '<div style="padding:20px;">';
  html += `<div class="summary-section"><h4>📋 Executive Summary</h4><p>${escapeHtml(summary.executive_summary || '')}</p></div>`;
  if (summary.key_points?.length) {
    html += '<div class="summary-section"><h4>🎯 Key Points</h4><ul>';
    summary.key_points.forEach(p => { html += `<li>${escapeHtml(p)}</li>`; });
    html += '</ul></div>';
  }
  if (summary.topics?.length) {
    html += '<div class="summary-section"><h4>📌 Topics</h4><div class="summary-tags">';
    summary.topics.forEach(t => { html += `<span class="voice-tag">${escapeHtml(t)}</span>`; });
    html += '</div></div>';
  }
  html += `<div class="summary-meta">
    <span>📊 Difficulty: ${summary.difficulty_level || 'N/A'}</span>
    <span>⏱ Read time: ${summary.estimated_read_time_minutes || '?'} min</span>
    <span>👥 Audience: ${escapeHtml(summary.target_audience || 'General')}</span>
  </div>`;
  html += '</div>';
  document.getElementById('summaryContent').innerHTML = html;
}

function closeSummaryPanel() {
  document.getElementById('summaryPanel')?.classList.remove('active');
}


// ==================== SHARED VIEWER (PUBLIC) ====================

let sharedViewerToken = null;
let sharedChatHistory = [];

async function openSharedViewer(token) {
  sharedViewerToken = token;
  sharedChatHistory = [];

  // Hide the dashboard, show a loading state
  document.getElementById('dashboardContent').style.display = 'none';
  document.querySelector('.navbar')?.style.setProperty('display', 'none');

  try {
    const res = await fetch(`${API_BASE}/shared/${token}`);
    if (res.status === 410) {
      document.body.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column;background:#0a0a1e;color:#fff;font-family:system-ui;">
        <div style="font-size:64px;margin-bottom:24px;">⏰</div>
        <h2 style="margin-bottom:12px;">Link Expired</h2>
        <p style="color:#94a3b8;max-width:400px;text-align:center;">This shared presentation link has expired (24-hour limit). Ask the creator for a new link.</p>
      </div>`;
      return;
    }
    if (!res.ok) {
      document.body.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column;background:#0a0a1e;color:#fff;font-family:system-ui;">
        <div style="font-size:64px;margin-bottom:24px;">🔍</div>
        <h2 style="margin-bottom:12px;">Presentation Not Found</h2>
        <p style="color:#94a3b8;">This link may be invalid or the presentation was removed.</p>
      </div>`;
      return;
    }

    const data = await res.json();
    // Build a mock presentation object to reuse the viewer
    const sharedPres = {
      id: 'shared_' + token,
      title: data.title,
      slides: data.slides || [],
      scripts: data.scripts || [],
      avatar_id: data.avatar_id,
      voice_id: data.voice_id,
      file_type: 'Shared',
      file_size: 0,
      filename: data.title,
      _shared: true,
      _share_token: token,
      _has_qa: data.has_qa,
      _quiz: data.quiz || null,
      _summary: data.summary || null,
    };

    // Open the viewer
    openViewer(sharedPres);

    // Update topbar for shared context
    document.getElementById('viewerTitle').childNodes[0].textContent = data.title;
    document.getElementById('viewerMeta').textContent = `Shared Presentation • ${data.total_slides} slides`;

    // Hide creator-only buttons in shared mode but keep Quiz and Q&A
    const controlsRight = document.querySelector('.controls-right');
    if (controlsRight) {
      const btns = controlsRight.querySelectorAll('.ctrl-btn');
      btns.forEach(btn => {
        const title = btn.getAttribute('title') || '';
        if (['Edit Scripts', 'Share'].includes(title)) {
          btn.style.display = 'none';
        }
      });
    }
  } catch (err) {
    document.body.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column;background:#0a0a1e;color:#fff;font-family:system-ui;">
      <div style="font-size:64px;margin-bottom:24px;">⚠️</div>
      <h2>Connection Error</h2>
      <p style="color:#94a3b8;">Could not load the shared presentation. Please try again.</p>
    </div>`;
  }
}

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
  grid.innerHTML = avatars.map(a => {
    const thumb = a.thumbnail || '';
    return `
    <div class="avatar-card ${avatarData.selectedId === a.id ? 'selected' : ''}" onclick="selectAvatar('${a.id}')">
      <img src="${thumb}" alt="${escapeHtml(a.name)}" loading="lazy">
      <div class="avatar-name">${escapeHtml(a.name)}</div>
      <div class="avatar-desc">${escapeHtml(a.description)}</div>
      <span class="avatar-badge">${a.category}</span>
    </div>
  `;}).join('');
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
  tts.stop();
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
          <button class="voice-preview-btn" onclick="event.stopPropagation(); previewVoice('${v.id}')" title="Preview voice">🔊 Preview</button>
        </div>
      </div>
    </div>
  `).join('');
}

function previewVoice(voiceId) {
  const voice = voiceData.voices.find(v => v.id === voiceId);
  if (!voice) return;
  const text = voice.preview_text || `Hello! I'm ${voice.name}. I'll be presenting your content in a clear and professional manner.`;
  tts.preview(text, voice.language, voice.gender);
  showToast(`Playing preview: ${voice.name}`, 'success');
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
  showToast(`Voice "${voice.name}" selected!`, 'success');
  // Open generate panel next
  setTimeout(() => openGeneratePanel(), 400);
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
