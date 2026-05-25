/**
 * AI Presentation Avatar Frontend
 * Interactive auth panel + profile manager + admin user panel.
 */

const CONFIG = {
  backendUrl:
    window.BACKEND_URL ||
    localStorage.getItem('backendUrl') ||
    (window.location.hostname === 'localhost' ? 'http://localhost:8000' : null),
  environment: window.location.hostname === 'localhost' ? 'development' : 'production',
  googleClientId: window.GOOGLE_CLIENT_ID || localStorage.getItem('googleClientId') || null,
};

const appState = {
  backendConnected: false,
  authToken: localStorage.getItem('auth_token') || null,
  user: null,
  pendingAuthMode: 'signin',
  googleClientId: null,
  signupEmail: null,
  otpResendTimer: 0,
  otpResendInterval: null,
};

async function initializeApp() {
  bindUiEvents();
  displayConfiguration();

  await initializeAuth();
}

function bindUiEvents() {
  const authToggleBtn = document.getElementById('authToggleBtn');
  const authPanel = document.getElementById('authPanel');
  const tabSignin = document.getElementById('tabSignin');
  const tabSignup = document.getElementById('tabSignup');
  const signinBtn = document.getElementById('signinBtn');
  const sendCodeBtn = document.getElementById('sendCodeBtn');
  const verifyAccountBtn = document.getElementById('verifyAccountBtn');
  const resendCodeBtn = document.getElementById('resendCodeBtn');
  const signOutQuickBtn = document.getElementById('signOutQuickBtn');
  const saveProfileBtn = document.getElementById('saveProfileBtn');
  const refreshAdminBtn = document.getElementById('refreshAdminBtn');
  const refreshStatusBtn = document.getElementById('refreshStatusBtn');
  const profileAvatarUrl = document.getElementById('profileAvatarUrl');
  
  // Profile dropdown events
  const userChip = document.getElementById('userChip');
  const profileDropdown = document.getElementById('profileDropdown');
  const closeProfileBtn = document.getElementById('closeProfileBtn');
  const saveProfileDropdownBtn = document.getElementById('saveProfileDropdownBtn');
  const dropdownProfileAvatarUrl = document.getElementById('dropdownProfileAvatarUrl');

  if (authToggleBtn) {
    authToggleBtn.addEventListener('click', () => {
      authPanel.classList.toggle('open');
    });
  }

  document.addEventListener('click', (event) => {
    if (!authPanel || !authToggleBtn) return;
    const clickInside = authPanel.contains(event.target) || authToggleBtn.contains(event.target);
    if (!clickInside) authPanel.classList.remove('open');
  });

  if (tabSignin) tabSignin.addEventListener('click', () => switchAuthTab('signin'));
  if (tabSignup) tabSignup.addEventListener('click', () => switchAuthTab('signup'));
  if (signinBtn) signinBtn.addEventListener('click', signInWithEmail);
  if (sendCodeBtn) sendCodeBtn.addEventListener('click', sendVerificationCode);
  if (verifyAccountBtn) verifyAccountBtn.addEventListener('click', verifyEmailAndCreateAccount);
  if (resendCodeBtn) resendCodeBtn.addEventListener('click', resendVerificationCode);
  if (signOutQuickBtn) signOutQuickBtn.addEventListener('click', signOut);
  if (saveProfileBtn) saveProfileBtn.addEventListener('click', saveProfile);
  if (refreshAdminBtn) refreshAdminBtn.addEventListener('click', loadAdminUsers);
  if (refreshStatusBtn) refreshStatusBtn.addEventListener('click', testBackendConnectivity);

  if (profileAvatarUrl) {
    profileAvatarUrl.addEventListener('input', () => {
      const preview = document.getElementById('profileAvatarPreview');
      const url = profileAvatarUrl.value.trim();
      if (preview) preview.src = url || fallbackAvatar('User');
    });
  }

  // Profile dropdown events
  if (userChip) {
    userChip.addEventListener('click', (e) => {
      if (!appState.authToken) return;
      e.stopPropagation();
      profileDropdown.classList.toggle('hidden');
    });
  }

  if (closeProfileBtn) {
    closeProfileBtn.addEventListener('click', () => {
      profileDropdown.classList.add('hidden');
    });
  }

  document.addEventListener('click', (event) => {
    if (!profileDropdown || !userChip) return;
    const clickInside = profileDropdown.contains(event.target) || userChip.contains(event.target);
    if (!clickInside) profileDropdown.classList.add('hidden');
  });

  if (saveProfileDropdownBtn) {
    saveProfileDropdownBtn.addEventListener('click', saveProfileFromDropdown);
  }

  // Sign out button in dropdown
  const signOutDropdownBtn = document.getElementById('signOutDropdownBtn');
  if (signOutDropdownBtn) {
    signOutDropdownBtn.addEventListener('click', signOut);
  }

  if (dropdownProfileAvatarUrl) {
    dropdownProfileAvatarUrl.addEventListener('input', () => {
      const preview = document.getElementById('dropdownProfileAvatar');
      const url = dropdownProfileAvatarUrl.value.trim();
      if (preview) preview.src = url || fallbackAvatar(document.getElementById('dropdownProfileName')?.value || 'User');
    });
  }

  // Document upload events
  const uploadArea = document.getElementById('uploadArea');
  const documentUpload = document.getElementById('documentUpload');

  if (uploadArea && documentUpload) {
    uploadArea.addEventListener('click', () => documentUpload.click());

    // File input change
    documentUpload.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) handleDocumentUpload(file);
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
      uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadArea.classList.remove('drag-over');
      const file = e.dataTransfer.files[0];
      if (file) handleDocumentUpload(file);
    });
  }
}

async function initializeAuth() {
  if (!CONFIG.backendUrl) {
    setPanelMessage('Set BACKEND_URL first to enable sign in.', true);
    return;
  }

  if (appState.authToken) {
    const loaded = await loadProfile();
    if (!loaded) clearSession();
  }

  const clientConfig = await fetchGoogleClientId();
  if (clientConfig.configured && clientConfig.client_id) {
    appState.googleClientId = clientConfig.client_id;
    await renderGoogleButtons();
  }

  updateAuthUi();
}

function switchAuthTab(tabName) {
  const signinView = document.getElementById('signinView');
  const signupView = document.getElementById('signupView');
  const tabSignin = document.getElementById('tabSignin');
  const tabSignup = document.getElementById('tabSignup');

  const signin = tabName === 'signin';
  signinView.classList.toggle('active', signin);
  signupView.classList.toggle('active', !signin);
  tabSignin.classList.toggle('active', signin);
  tabSignup.classList.toggle('active', !signin);
}

async function fetchGoogleClientId() {
  try {
    const res = await fetchWithTimeout(`${CONFIG.backendUrl}/auth/google/client-id`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });

    if (!res.ok) {
      return { configured: false, client_id: null };
    }

    const payload = await res.json();
    if ((!payload || !payload.client_id) && CONFIG.googleClientId) {
      return { configured: true, client_id: CONFIG.googleClientId };
    }

    return payload;
  } catch (error) {
    console.error('Failed to fetch Google client id', error);
    if (CONFIG.googleClientId) {
      return { configured: true, client_id: CONFIG.googleClientId };
    }
    return { configured: false, client_id: null };
  }
}

async function renderGoogleButtons() {
  if (!window.google || !window.google.accounts || !window.google.accounts.id) {
    setPanelMessage('Google sign-in is still loading. Refresh in a moment.', true);
    return;
  }

  window.google.accounts.id.initialize({
    client_id: appState.googleClientId,
    callback: handleGoogleCredential,
    ux_mode: 'popup',
  });

  // Calculate responsive button width
  const containerWidth = Math.min(window.innerWidth - 48, 360); // 48px for padding (24px each side)
  const buttonWidth = Math.max(containerWidth, 200); // Min 200px, max 360px

  const signInHost = document.getElementById('googleSignInBtn');
  const signUpHost = document.getElementById('googleSignUpBtn');

  if (signInHost) {
    signInHost.innerHTML = '';
    window.google.accounts.id.renderButton(signInHost, {
      theme: 'outline',
      size: 'large',
      text: 'signin_with',
      width: buttonWidth,
      shape: 'pill',
      click_listener: () => {
        appState.pendingAuthMode = 'signin';
      },
    });
  }

  if (signUpHost) {
    signUpHost.innerHTML = '';
    window.google.accounts.id.renderButton(signUpHost, {
      theme: 'filled_blue',
      size: 'large',
      text: 'signup_with',
      width: buttonWidth,
      shape: 'pill',
      click_listener: () => {
        appState.pendingAuthMode = 'signup';
      },
    });
  }
}

async function signInWithEmail() {
  const email = (document.getElementById('signinEmail')?.value || '').trim();
  const password = (document.getElementById('signinPassword')?.value || '').trim();

  if (!email || !password) {
    setPanelMessage('Please enter email and password.', true);
    return;
  }

  setPanelMessage('Signing in...', false);

  try {
    const res = await fetchWithTimeout(`${CONFIG.backendUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    const payload = await res.json();
    if (!res.ok) {
      throw new Error(payload.detail || 'Sign in failed');
    }

    applyAuthPayload(payload);
    setPanelMessage('Signed in successfully.', false);
  } catch (error) {
    setPanelMessage(`Sign in failed: ${error.message}`, true);
  }
}

async function sendVerificationCode() {
  const firstName = (document.getElementById('signupFirstName')?.value || '').trim();
  const lastName = (document.getElementById('signupLastName')?.value || '').trim();
  const gender = (document.getElementById('signupGender')?.value || '').trim();
  const email = (document.getElementById('signupEmail')?.value || '').trim();
  const password = (document.getElementById('signupPassword')?.value || '').trim();

  if (!firstName || !lastName || !gender || !email || !password) {
    setPanelMessage('Please complete all sign-up fields.', true);
    return;
  }

  setPanelMessage('Sending verification code to your email...', false);

  try {
    const res = await fetchWithTimeout(`${CONFIG.backendUrl}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ first_name: firstName, last_name: lastName, gender, email, password }),
    });

    const payload = await res.json();
    if (!res.ok) {
      throw new Error(payload.detail || 'Could not start registration');
    }

    appState.signupEmail = email;
    document.getElementById('verifyCodeRow')?.classList.remove('hidden');
    setPanelMessage(payload.message || 'Verification code sent. Check your email.', false);
    
    // Start OTP resend cooldown timer (60 seconds)
    startOtpResendTimer(60);
  } catch (error) {
    setPanelMessage(`Could not send code: ${error.message}`, true);
  }
}

async function verifyEmailAndCreateAccount() {
  const email = (document.getElementById('signupEmail')?.value || appState.signupEmail || '').trim();
  const code = (document.getElementById('signupCode')?.value || '').trim();

  if (!email || !code) {
    setPanelMessage('Enter email and authentication code.', true);
    return;
  }

  setPanelMessage('Verifying your email...', false);

  try {
    const res = await fetchWithTimeout(`${CONFIG.backendUrl}/auth/verify-email`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ email, code }),
    });

    const payload = await res.json();
    if (!res.ok) {
      throw new Error(payload.detail || 'Verification failed');
    }

    applyAuthPayload(payload);
    setPanelMessage('Account created and verified successfully.', false);
    switchAuthTab('signin');
  } catch (error) {
    // Clear only the code field to allow quick retry
    const codeInput = document.getElementById('signupCode');
    if (codeInput) {
      codeInput.value = '';
      codeInput.focus();
    }
    setPanelMessage(`❌ ${error.message}. Please check your code and try again.`, true);
  }
}

async function resendVerificationCode() {
  const email = (document.getElementById('signupEmail')?.value || appState.signupEmail || '').trim();
  if (!email) {
    setPanelMessage('Enter your email first.', true);
    return;
  }

  // Check if timer is still active
  if (appState.otpResendTimer > 0) {
    setPanelMessage(`Please wait ${appState.otpResendTimer}s before resending.`, true);
    return;
  }

  try {
    const res = await fetchWithTimeout(`${CONFIG.backendUrl}/auth/resend-code`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    const payload = await res.json();
    if (!res.ok) throw new Error(payload.detail || 'Could not resend code');

    setPanelMessage('Verification code resent.', false);
    
    // Restart OTP resend cooldown timer
    startOtpResendTimer(60);
  } catch (error) {
    setPanelMessage(`Could not resend: ${error.message}`, true);
  }
}

async function handleGoogleCredential(response) {
  if (!response?.credential) {
    setPanelMessage('Google authentication failed. Try again.', true);
    return;
  }

  setPanelMessage('Verifying Google account...', false);

  try {
    const res = await fetchWithTimeout(`${CONFIG.backendUrl}/auth/google`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        credential: response.credential,
        mode: appState.pendingAuthMode,
      }),
    });

    const payload = await res.json();
    if (!res.ok) {
      throw new Error(payload.detail || 'Google sign in failed');
    }

    applyAuthPayload(payload);
    setPanelMessage('Signed in with Google.', false);
  } catch (error) {
    setPanelMessage(`Google sign in failed: ${error.message}`, true);
  }
}

async function loadProfile() {
  if (!appState.authToken) return false;

  try {
    const res = await fetchWithTimeout(`${CONFIG.backendUrl}/auth/profile`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${appState.authToken}`,
      },
    });

    if (!res.ok) return false;

    appState.user = await res.json();
    fillProfileForm(appState.user);
    updateAuthUi();
    return true;
  } catch (error) {
    console.error('Failed to load profile', error);
    return false;
  }
}

function fillProfileForm(user) {
  const data = user || {};
  const preview = document.getElementById('profileAvatarPreview');

  const set = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.value = value || '';
  };

  set('profileEmail', data.email);
  set('profileFirstName', data.first_name);
  set('profileLastName', data.last_name);
  set('profileGender', data.gender);
  set('profileAvatarUrl', data.avatar_url);
  set('profileBio', data.bio);

  if (preview) {
    preview.src = data.avatar_url || fallbackAvatar(data.name || data.email || 'User');
  }

  // Also fill the profile dropdown form
  fillProfileDropdownForm(data);
}

function fillProfileDropdownForm(user) {
  const data = user || {};
  const dropdownAvatar = document.getElementById('dropdownProfileAvatar');

  const set = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.value = value || '';
  };

  set('dropdownProfileEmail', data.email);
  set('dropdownProfileName', data.first_name && data.last_name ? `${data.first_name} ${data.last_name}` : '');
  set('dropdownProfileGender', data.gender);
  set('dropdownProfileAvatarUrl', data.avatar_url);
  set('dropdownProfileMobile', data.mobile || '');
  set('dropdownProfileBio', data.bio);

  if (dropdownAvatar) {
    dropdownAvatar.src = data.avatar_url || fallbackAvatar(data.name || data.email || 'User');
  }
}

async function saveProfile() {
  if (!appState.authToken) {
    setProfileMessage('Please sign in first.', true);
    return;
  }

  const firstName = (document.getElementById('profileFirstName')?.value || '').trim();
  const lastName = (document.getElementById('profileLastName')?.value || '').trim();
  const gender = (document.getElementById('profileGender')?.value || '').trim();
  const avatarUrl = (document.getElementById('profileAvatarUrl')?.value || '').trim();
  const bio = (document.getElementById('profileBio')?.value || '').trim();

  try {
    const res = await fetchWithTimeout(`${CONFIG.backendUrl}/auth/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        Authorization: `Bearer ${appState.authToken}`,
      },
      body: JSON.stringify({
        first_name: firstName,
        last_name: lastName,
        gender,
        avatar_url: avatarUrl,
        bio,
      }),
    });

    const payload = await res.json();
    if (!res.ok) throw new Error(payload.detail || 'Profile update failed');

    appState.user = payload;
    fillProfileForm(payload);
    updateAuthUi();
    setProfileMessage('Profile saved successfully.', false);
  } catch (error) {
    setProfileMessage(`Could not save profile: ${error.message}`, true);
  }
}

async function saveProfileFromDropdown() {
  if (!appState.authToken) {
    setProfileDropdownMessage('Please sign in first.', true);
    return;
  }

  const fullName = (document.getElementById('dropdownProfileName')?.value || '').trim();
  const gender = (document.getElementById('dropdownProfileGender')?.value || '').trim();
  const avatarUrl = (document.getElementById('dropdownProfileAvatarUrl')?.value || '').trim();
  const mobile = (document.getElementById('dropdownProfileMobile')?.value || '').trim();
  const bio = (document.getElementById('dropdownProfileBio')?.value || '').trim();

  // Parse full name into first and last name
  const nameParts = fullName.split(' ').filter(p => p.length > 0);
  const firstName = nameParts[0] || '';
  const lastName = nameParts.slice(1).join(' ') || '';

  setProfileDropdownMessage('Saving...', false);

  try {
    const res = await fetchWithTimeout(`${CONFIG.backendUrl}/auth/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        Authorization: `Bearer ${appState.authToken}`,
      },
      body: JSON.stringify({
        first_name: firstName,
        last_name: lastName,
        gender,
        avatar_url: avatarUrl,
        bio,
      }),
    });

    const payload = await res.json();
    if (!res.ok) throw new Error(payload.detail || 'Profile update failed');

    appState.user = payload;
    fillProfileForm(payload);
    updateAuthUi();
    setProfileDropdownMessage('Changes saved successfully.', false);
    
    // Close dropdown after short delay
    setTimeout(() => {
      document.getElementById('profileDropdown')?.classList.add('hidden');
    }, 1500);
  } catch (error) {
    setProfileDropdownMessage(`Could not save: ${error.message}`, true);
  }
}

function setProfileMessage(text, isError) {
  const el = document.getElementById('profileMessage');
  if (!el) return;
  el.textContent = text;
  el.style.color = isError ? '#aa2f2f' : '#1d9a65';
}

function setProfileDropdownMessage(text, isError) {
  const el = document.getElementById('profileDropdownMessage');
  if (!el) return;
  el.textContent = text;
  el.style.color = isError ? '#aa2f2f' : '#1d9a65';
}

function applyAuthPayload(payload) {
  appState.authToken = payload.access_token;
  appState.user = payload.user;

  localStorage.setItem('auth_token', payload.access_token);
  fillProfileForm(payload.user);
  updateAuthUi();

  document.getElementById('authPanel')?.classList.remove('open');
}

function updateAuthUi() {
  const signedIn = Boolean(appState.authToken && appState.user);

  const userChip = document.getElementById('userChip');
  const userChipText = document.getElementById('userChipText');
  const userChipAvatar = document.getElementById('userChipAvatar');
  const signOutQuickBtn = document.getElementById('signOutQuickBtn');
  const authToggleBtn = document.getElementById('authToggleBtn');
  const profileSection = document.getElementById('profileSection');
  const profileLocked = document.getElementById('profileLocked');
  const profileDropdown = document.getElementById('profileDropdown');
  const uploadArticle = document.getElementById('uploadArticle');

  // Show userChip (avatar) only when signed in
  userChip.style.display = signedIn ? 'flex' : 'none';
  // Hide all sign in/account buttons when signed in - they should only be in the dropdown
  signOutQuickBtn.classList.toggle('hidden', true);
  authToggleBtn.style.display = signedIn ? 'none' : 'block';

  if (signedIn) {
    const displayName = appState.user.first_name && appState.user.last_name
      ? `${appState.user.first_name} ${appState.user.last_name}`
      : appState.user.first_name || appState.user.email;
    userChipText.textContent = displayName;
    userChipAvatar.src = appState.user.avatar_url || fallbackAvatar(displayName);

    if (profileSection) {
      profileSection.classList.remove('hidden');
    }
    if (profileLocked) {
      profileLocked.classList.add('hidden');
    }
    
    // Show upload section only to signed-in users
    if (uploadArticle) uploadArticle.style.display = 'block';
  } else {
    if (profileSection) {
      profileSection.classList.add('hidden');
    }
    if (profileLocked) {
      profileLocked.classList.remove('hidden');
    }
    if (profileDropdown) profileDropdown.classList.add('hidden');
    
    // Hide upload section when not signed in
    if (uploadArticle) uploadArticle.style.display = 'none';
  }

  const isAdmin = Boolean(appState.user && appState.user.is_admin);

  const adminPanel = document.getElementById('adminPanel');
  adminPanel.style.display = isAdmin ? 'block' : 'none';
  if (isAdmin) {
    loadAdminUsers();
    testBackendConnectivity();
  }
}

function signOut() {
  clearSession();
  setPanelMessage('Signed out.', false);
}

function clearSession() {
  appState.authToken = null;
  appState.user = null;
  localStorage.removeItem('auth_token');

  fillProfileForm({
    email: '',
    first_name: '',
    last_name: '',
    gender: '',
    avatar_url: '',
    bio: '',
  });

  const adminBody = document.getElementById('adminUsersBody');
  if (adminBody) {
    adminBody.innerHTML = '<tr><td colspan="5" class="small">No users loaded yet.</td></tr>';
  }

  updateAuthUi();
}

function setPanelMessage(text, isError) {
  const msg = document.getElementById('panelAuthMessage');
  if (!msg) return;
  msg.style.display = 'block';
  msg.textContent = text;
  msg.classList.toggle('error', Boolean(isError));
}

async function loadAdminUsers() {
  if (!appState.authToken || !appState.user?.is_admin) return;

  const body = document.getElementById('adminUsersBody');
  const stats = document.getElementById('adminStats');

  try {
    body.innerHTML = '<tr><td colspan="5" class="small">Loading users...</td></tr>';

    const res = await fetchWithTimeout(`${CONFIG.backendUrl}/auth/admin/users`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${appState.authToken}`,
      },
    });

    const payload = await res.json();
    if (!res.ok) throw new Error(payload.detail || 'Could not load users');

    stats.innerHTML = `
      <span class="tag">Total: ${payload.total}</span>
      <span class="tag">Verified: ${payload.verified}</span>
      <span class="tag">Admins: ${payload.admins}</span>
    `;

    if (!payload.items?.length) {
      body.innerHTML = '<tr><td colspan="5" class="small">No users available.</td></tr>';
      return;
    }

    body.innerHTML = payload.items
      .map((user) => {
        const verifiedChip = user.is_verified ? '<span class="chip ok">Verified</span>' : '<span class="chip warn">Pending</span>';
        const activeChip = user.is_active ? '<span class="chip ok">Active</span>' : '<span class="chip bad">Disabled</span>';
        const adminChip = user.is_admin ? '<span class="chip ok">Admin</span>' : '<span class="chip">User</span>';

        return `
          <tr>
            <td>
              <strong>${escapeHtml(user.name || user.email)}</strong><br />
              <span class="small">${escapeHtml(user.email)}</span>
            </td>
            <td>${verifiedChip}${activeChip}${adminChip}</td>
            <td>${escapeHtml(user.login_provider || 'email')}</td>
            <td>${formatDate(user.created_at)}</td>
            <td>
              <button class="btn btn-soft" onclick="toggleAdmin(${user.id})" style="padding:0.38rem 0.55rem; font-size:0.78rem;">
                ${user.is_admin ? 'Revoke admin' : 'Make admin'}
              </button>
              <button class="btn btn-soft" onclick="toggleActive(${user.id})" style="padding:0.38rem 0.55rem; font-size:0.78rem; margin-top:0.3rem;">
                ${user.is_active ? 'Disable' : 'Enable'}
              </button>
            </td>
          </tr>
        `;
      })
      .join('');
  } catch (error) {
    body.innerHTML = `<tr><td colspan="5" class="small">${escapeHtml(error.message)}</td></tr>`;
  }
}

function toggleAdmin(userId) {
  adminAction('toggle-admin', userId);
}

function toggleActive(userId) {
  adminAction('toggle-active', userId);
}

async function adminAction(path, userId) {
  if (!appState.authToken || !appState.user?.is_admin) return;

  try {
    const res = await fetchWithTimeout(`${CONFIG.backendUrl}/auth/admin/users/${userId}/${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${appState.authToken}`,
      },
    });

    if (!res.ok) {
      const payload = await res.json();
      throw new Error(payload.detail || 'Action failed');
    }

    await loadAdminUsers();

    const updatedUser = await res.json();
    if (updatedUser.id === appState.user.id) {
      appState.user = updatedUser;
      updateAuthUi();
    }
  } catch (error) {
    alert(`Error: ${error.message}`);
  }
}

function escapeHtml(text) {
  if (!text) return '';
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}

function formatDate(isoString) {
  if (!isoString) return 'N/A';
  try {
    return new Date(isoString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return 'Invalid';
  }
}

async function testBackendConnectivity() {
  const indicator = document.getElementById('backendStatusIndicator');
  const statusText = document.getElementById('backendStatusText');
  const statusDetail = document.getElementById('backendStatusDetail');

  if (!indicator || !statusText) return;

  try {
    indicator.classList.remove('ok', 'error');
    indicator.classList.add('loading');
    statusText.textContent = 'Checking...';

    const res = await Promise.race([
      fetch(`${CONFIG.backendUrl}/health`, {
        method: 'GET',
        headers: { Accept: 'application/json' },
        mode: 'cors',
      }),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000)),
    ]);

    if (res.ok) {
      const data = await res.json();
      indicator.classList.add('ok');
      statusText.textContent = '🟢 Connected';
      if (statusDetail) statusDetail.textContent = `v${data.version || 'unknown'}`;
      appState.backendConnected = true;
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (error) {
    indicator.classList.add('error');
    statusText.textContent = '🔴 Disconnected';
    if (statusDetail) statusDetail.textContent = error.message;
    appState.backendConnected = false;
  }
}

function setPanelMessage(text, isError) {
  const el = document.getElementById('panelMessage');
  if (!el) return;
  el.textContent = text;
  el.style.color = isError ? '#aa2f2f' : '#1d9a65';
}

function fallbackAvatar(name) {
  const url = new URL('https://api.dicebear.com/8.x/initials/svg');
  url.searchParams.append('seed', (name || 'User').trim());
  url.searchParams.append('backgroundColor', '6c5ce7');
  url.searchParams.append('textColor', 'ffffff');
  return url.toString();
}

function displayConfiguration() {
  if (CONFIG.backendUrl) {
    const el = document.getElementById('configDisplay');
    if (el) el.textContent = CONFIG.backendUrl;
  }
}

function fetchWithTimeout(url, options = {}, timeout = 10000) {
  return Promise.race([
    fetch(url, {
      ...options,
      mode: 'cors',
      credentials: 'include',
    }),
    new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), timeout)),
  ]);
}

window.appState = appState;
window.toggleAdmin = toggleAdmin;
window.toggleActive = toggleActive;

function displayConfiguration() {
  const backendUrl = document.getElementById('backendUrl');
  if (backendUrl) {
    backendUrl.textContent = CONFIG.backendUrl || 'Not configured';
  }
}

// Admin-only features are hidden by default and only shown when user.is_admin=true
async function testBackendConnectivity() {
  if (!appState.user?.is_admin) {
    return;
  }

  const statusText = document.getElementById('statusText');
  const dot = document.getElementById('statusDot');
  const backendStatusText = document.getElementById('backendStatusText');
  const healthStatus = document.getElementById('healthStatus');
  const infoStatus = document.getElementById('infoStatus');

  if (!CONFIG.backendUrl) {
    statusText.textContent = 'Not configured';
    backendStatusText.textContent = 'Not configured';
    healthStatus.textContent = 'Not configured';
    infoStatus.textContent = 'Not configured';
    dot.classList.remove('ok');
    return;
  }

  try {
    backendStatusText.textContent = 'Checking...';

    const healthRes = await fetchWithTimeout(`${CONFIG.backendUrl}/health`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });

    const infoRes = await fetchWithTimeout(`${CONFIG.backendUrl}/`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });

    const ok = healthRes.ok && infoRes.ok;
    appState.backendConnected = ok;

    statusText.textContent = ok ? 'Connected' : 'Degraded';
    backendStatusText.textContent = ok ? 'Connected' : 'Issue detected';
    healthStatus.textContent = healthRes.ok ? 'OK' : `Error ${healthRes.status}`;
    infoStatus.textContent = infoRes.ok ? 'OK' : `Error ${infoRes.status}`;
    dot.classList.toggle('ok', ok);
  } catch (error) {
    appState.backendConnected = false;
    statusText.textContent = 'Disconnected';
    backendStatusText.textContent = 'Disconnected';
    healthStatus.textContent = 'Failed';
    infoStatus.textContent = 'Failed';
    dot.classList.remove('ok');
  }
}

function fallbackAvatar(seedText) {
  const seed = encodeURIComponent(seedText || 'User');
  return `https://api.dicebear.com/8.x/initials/svg?seed=${seed}`;
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString();
}

function fetchWithTimeout(url, options = {}, timeout = 10000) {
  return Promise.race([
    fetch(url, {
      ...options,
      mode: 'cors',
      credentials: 'include',
    }),
    new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), timeout)),
  ]);
}

async function handleDocumentUpload(file) {
  const uploadArea = document.getElementById('uploadArea');
  const uploadProgress = document.getElementById('uploadProgress');
  const uploadSuccess = document.getElementById('uploadSuccess');
  const uploadError = document.getElementById('uploadError');
  const uploadFileName = document.getElementById('uploadFileName');
  const uploadBar = document.getElementById('uploadBar');
  const errorMessage = document.getElementById('errorMessage');

  // Reset messages
  uploadSuccess.classList.add('hidden');
  uploadError.classList.add('hidden');

  // Validate file type
  const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
  if (!allowedTypes.includes(file.type)) {
    errorMessage.textContent = '❌ Invalid file type. Please upload PDF, PPTX, or DOCX.';
    uploadError.classList.remove('hidden');
    return;
  }

  // Validate file size (max 50MB)
  const maxSize = 50 * 1024 * 1024;
  if (file.size > maxSize) {
    errorMessage.textContent = '❌ File too large. Maximum size is 50MB.';
    uploadError.classList.remove('hidden');
    return;
  }

  // Check if user is authenticated
  if (!appState.authToken) {
    errorMessage.textContent = '❌ Please sign in first to upload documents.';
    uploadError.classList.remove('hidden');
    return;
  }

  // Show progress
  uploadProgress.classList.remove('hidden');
  uploadFileName.textContent = `Uploading: ${file.name}`;
  uploadBar.style.width = '0%';

  try {
    const formData = new FormData();
    formData.append('file', file);

    // Simulate upload progress
    let progress = 0;
    const progressInterval = setInterval(() => {
      progress += Math.random() * 30;
      if (progress > 90) progress = 90;
      uploadBar.style.width = progress + '%';
    }, 300);

    const response = await fetch(`${CONFIG.backendUrl}/presentations/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${appState.authToken}`,
      },
      body: formData,
      mode: 'cors',
    });

    clearInterval(progressInterval);
    uploadBar.style.width = '100%';

    if (response.ok) {
      const data = await response.json();
      uploadProgress.classList.add('hidden');
      uploadSuccess.classList.remove('hidden');
      
      // Clear file input
      document.getElementById('documentUpload').value = '';
      
      // Store the uploaded filename
      appState.currentPresentation = data.filename;
      
      // Hide upload area and show avatar/voice selection
      setTimeout(() => {
        uploadSection.style.opacity = '0.7';
        uploadSection.style.pointerEvents = 'none';
        
        // Load and show avatar selection
        loadAvatarsForSelection();
        loadVoicesForSelection();
      }, 2000);
    } else {
      const error = await response.text();
      errorMessage.textContent = '❌ Upload failed: ' + (error || 'Please try again');
      uploadProgress.classList.add('hidden');
      uploadError.classList.remove('hidden');
    }
  } catch (error) {
    uploadProgress.classList.add('hidden');
    errorMessage.textContent = '❌ Upload error: ' + error.message;
    uploadError.classList.remove('hidden');
  }
}

function startOtpResendTimer(seconds) {
  appState.otpResendTimer = seconds;
  const resendBtn = document.getElementById('resendCodeBtn');
  const timerMsg = document.getElementById('resendTimerMsg');
  const timerCount = document.getElementById('timerCount');

  // Show timer message and disable only the resend button
  if (timerMsg) timerMsg.style.display = 'block';
  if (resendBtn) resendBtn.disabled = true;
  // NOTE: verifyAccountBtn stays enabled so user can retry code entry

  // Clear any existing interval
  if (appState.otpResendInterval) {
    clearInterval(appState.otpResendInterval);
  }

  // Update timer every second
  appState.otpResendInterval = setInterval(() => {
    appState.otpResendTimer--;
    if (timerCount) timerCount.textContent = appState.otpResendTimer;

    if (appState.otpResendTimer <= 0) {
      clearInterval(appState.otpResendInterval);
      appState.otpResendInterval = null;
      
      // Hide timer message and enable resend button
      if (timerMsg) timerMsg.style.display = 'none';
      if (resendBtn) {
        resendBtn.disabled = false;
        resendBtn.textContent = 'Resend code';
      }
    } else {
      // Update resend button text to show time remaining
      if (resendBtn) {
        resendBtn.textContent = `Resend code (${appState.otpResendTimer}s)`;
      }
    }
  }, 1000);
}

async function loadAvatarsForSelection() {
  try {
    const response = await fetch(`${CONFIG.backendUrl}/avatars`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${appState.authToken}`,
      },
      mode: 'cors',
    });

    if (response.ok) {
      const data = await response.json();
      appState.avatars = data.avatars;
      showAvatarSelection(data.avatars);
    } else {
      console.error('Failed to load avatars');
    }
  } catch (error) {
    console.error('Error loading avatars:', error);
  }
}

async function loadVoicesForSelection() {
  try {
    const response = await fetch(`${CONFIG.backendUrl}/voices`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${appState.authToken}`,
      },
      mode: 'cors',
    });

    if (response.ok) {
      const data = await response.json();
      appState.voices = data.voices;
      showVoiceSelection(data.voices);
    } else {
      console.error('Failed to load voices');
    }
  } catch (error) {
    console.error('Error loading voices:', error);
  }
}

function showAvatarSelection(avatars) {
  const uploadArticle = document.getElementById('uploadArticle');
  if (!uploadArticle) return;

  // Create avatar selection panel
  let avatarPanel = document.getElementById('avatarSelectionPanel');
  if (!avatarPanel) {
    avatarPanel = document.createElement('div');
    avatarPanel.id = 'avatarSelectionPanel';
    avatarPanel.style.cssText = 'margin-top: 2rem; padding: 1.5rem; background: #f5f5f5; border-radius: 8px;';
    uploadArticle.appendChild(avatarPanel);
  }

  let avatarHTML = '<h3 style="margin-top: 0; margin-bottom: 1rem;">👤 Select Your Avatar</h3>';
  avatarHTML += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">';
  
  avatars.forEach(avatar => {
    avatarHTML += `
      <div style="padding: 1rem; background: white; border-radius: 8px; border: 2px solid #ddd; cursor: pointer; transition: all 0.3s ease;" 
           onmouseover="this.style.borderColor='#0e6ba8'; this.style.boxShadow='0 4px 12px rgba(14, 107, 168, 0.2)';"
           onmouseout="this.style.borderColor='#ddd'; this.style.boxShadow='';"
           onclick="selectAvatar('${avatar.id}', '${avatar.name.replace(/'/g, "\\'")}')">
        <div style="font-size: 2.5rem; text-align: center; margin-bottom: 0.5rem;">🎭</div>
        <p style="font-weight: 600; margin: 0.5rem 0; font-size: 0.9rem; color: #153a55;">${avatar.name}</p>
        <p style="font-size: 0.8rem; color: #666; margin: 0;">${avatar.description}</p>
      </div>
    `;
  });
  
  avatarHTML += '</div>';
  avatarPanel.innerHTML = avatarHTML;
}

function showVoiceSelection(voices) {
  const uploadArticle = document.getElementById('uploadArticle');
  if (!uploadArticle) return;

  // Create voice selection panel
  let voicePanel = document.getElementById('voiceSelectionPanel');
  if (!voicePanel) {
    voicePanel = document.createElement('div');
    voicePanel.id = 'voiceSelectionPanel';
    voicePanel.style.cssText = 'margin-top: 2rem; padding: 1.5rem; background: #f5f5f5; border-radius: 8px;';
    uploadArticle.appendChild(voicePanel);
  }

  let voiceHTML = '<h3 style="margin-top: 0; margin-bottom: 1rem;">🎙️ Select Your Voice</h3>';
  voiceHTML += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">';
  
  voices.forEach(voice => {
    voiceHTML += `
      <div style="padding: 1rem; background: white; border-radius: 8px; border: 2px solid #ddd; cursor: pointer; transition: all 0.3s ease;" 
           onmouseover="this.style.borderColor='#1b9aaa'; this.style.boxShadow='0 4px 12px rgba(27, 154, 170, 0.2)';"
           onmouseout="this.style.borderColor='#ddd'; this.style.boxShadow='';"
           onclick="selectVoice('${voice.id}', '${voice.name.replace(/'/g, "\\'")}')">
        <div style="font-size: 2.5rem; text-align: center; margin-bottom: 0.5rem;">🎵</div>
        <p style="font-weight: 600; margin: 0.5rem 0; font-size: 0.9rem; color: #153a55;">${voice.name}</p>
        <p style="font-size: 0.8rem; color: #666; margin: 0;">${voice.description}</p>
        <p style="font-size: 0.75rem; color: #999; margin: 0.5rem 0 0 0;">${voice.language}</p>
      </div>
    `;
  });
  
  voiceHTML += '</div>';
  voicePanel.innerHTML = voiceHTML;
}

async function selectAvatar(avatarId, avatarName) {
  try {
    const response = await fetch(`${CONFIG.backendUrl}/avatars/select?avatar_id=${avatarId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${appState.authToken}`,
      },
      mode: 'cors',
    });

    if (response.ok) {
      appState.selectedAvatar = avatarId;
      console.log('Avatar selected:', avatarName);
      
      // Highlight selected avatar
      const avatarPanel = document.getElementById('avatarSelectionPanel');
      if (avatarPanel) {
        const divs = avatarPanel.querySelectorAll('div[onclick*="selectAvatar"]');
        divs.forEach(div => {
          if (div.getAttribute('onclick').includes(avatarId)) {
            div.style.borderColor = '#0e6ba8';
            div.style.background = '#f0f5ff';
          } else {
            div.style.borderColor = '#ddd';
            div.style.background = 'white';
          }
        });
      }
    }
  } catch (error) {
    console.error('Error selecting avatar:', error);
  }
}

async function selectVoice(voiceId, voiceName) {
  try {
    const response = await fetch(`${CONFIG.backendUrl}/voices/select?voice_id=${voiceId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${appState.authToken}`,
      },
      mode: 'cors',
    });

    if (response.ok) {
      appState.selectedVoice = voiceId;
      console.log('Voice selected:', voiceName);
      
      // Highlight selected voice
      const voicePanel = document.getElementById('voiceSelectionPanel');
      if (voicePanel) {
        const divs = voicePanel.querySelectorAll('div[onclick*="selectVoice"]');
        divs.forEach(div => {
          if (div.getAttribute('onclick').includes(voiceId)) {
            div.style.borderColor = '#1b9aaa';
            div.style.background = '#f0f7f8';
          } else {
            div.style.borderColor = '#ddd';
            div.style.background = 'white';
          }
        });
      }
    }
  } catch (error) {
    console.error('Error selecting voice:', error);
  }
}

window.appState = appState;
window.toggleAdmin = toggleAdmin;
window.toggleActive = toggleActive;
