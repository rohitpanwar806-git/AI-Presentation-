// Settings Page Application

let appState = {
  user: null,
  authToken: null,
  currentSection: 'profile'
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
  // Load auth state
  const token = localStorage.getItem('authToken');
  const userStr = localStorage.getItem('user');

  if (!token || !userStr) {
    // Redirect to main page if not authenticated
    window.location.href = '/';
    return;
  }

  appState.authToken = token;
  appState.user = JSON.parse(userStr);

  // Initialize UI
  bindSettingsEvents();
  displayUserInfo();
  await loadUserProfile();
});

function bindSettingsEvents() {
  // Section navigation
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const section = btn.dataset.section;
      switchSection(section);
    });
  });

  // Profile form
  document.getElementById('saveSettingsBtn').addEventListener('click', saveProfile);

  // Settings message
  const avatarUpload = document.getElementById('avatarUpload');
  if (avatarUpload) {
    avatarUpload.addEventListener('change', handleAvatarUpload);
  }

  // Notification preferences
  document.getElementById('saveNotifBtn').addEventListener('click', saveNotifications);

  // User menu
  const userChip = document.getElementById('userChip');
  const userMenu = document.getElementById('userMenu');
  
  if (userChip) {
    userChip.addEventListener('click', () => {
      userMenu.classList.toggle('hidden');
    });
  }

  // Close menu when clicking outside
  document.addEventListener('click', (e) => {
    if (!userChip?.contains(e.target) && !userMenu?.contains(e.target)) {
      userMenu?.classList.add('hidden');
    }
  });

  // Sign out
  document.getElementById('signOutBtn')?.addEventListener('click', () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    window.location.href = '/';
  });

  // Security buttons
  document.getElementById('changePasswordBtn')?.addEventListener('click', () => {
    alert('Password change functionality coming soon');
  });

  document.getElementById('enable2FABtn')?.addEventListener('click', () => {
    alert('2FA setup coming soon');
  });

  document.getElementById('viewLoginHistoryBtn')?.addEventListener('click', () => {
    alert('Login history coming soon');
  });

  // Account buttons
  document.getElementById('downloadDataBtn')?.addEventListener('click', () => {
    alert('Data export functionality coming soon');
  });

  document.getElementById('deleteAccountBtn')?.addEventListener('click', () => {
    if (confirm('Are you sure you want to delete your account? This cannot be undone.')) {
      alert('Account deletion functionality coming soon');
    }
  });

  // API Keys
  document.getElementById('generateKeyBtn')?.addEventListener('click', () => {
    alert('API key generation coming soon');
  });
}

function displayUserInfo() {
  // Update user chip
  const userChipAvatar = document.getElementById('userChipAvatar');
  const userChipText = document.getElementById('userChipText');

  if (appState.user) {
    const displayName = appState.user.first_name 
      ? `${appState.user.first_name} ${appState.user.last_name || ''}`.trim()
      : appState.user.email.split('@')[0];

    if (userChipAvatar) {
      userChipAvatar.src = appState.user.avatar_url || generateAvatarUrl(displayName);
    }
    if (userChipText) {
      userChipText.textContent = displayName.split(' ')[0];
    }
  }
}

function generateAvatarUrl(name) {
  const sanitized = name.replace(/\s+/g, '+');
  return `https://ui-avatars.com/api/?name=${sanitized}&background=6c5ce7&color=fff`;
}

async function loadUserProfile() {
  try {
    const response = await fetch(`${CONFIG.backendUrl}/auth/profile`, {
      headers: {
        'Authorization': `Bearer ${appState.authToken}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error('Failed to load profile');
    }

    const user = await response.json();
    appState.user = user;

    // Update profile form
    fillProfileForm();
  } catch (error) {
    console.error('Error loading profile:', error);
    setMessage('settingsMessage', `Error loading profile: ${error.message}`, 'error');
  }
}

function fillProfileForm() {
  if (!appState.user) return;

  // Fill form fields
  document.getElementById('settingsFirstName').value = appState.user.first_name || '';
  document.getElementById('settingsLastName').value = appState.user.last_name || '';
  document.getElementById('settingsEmail').value = appState.user.email || '';
  document.getElementById('settingsBio').value = appState.user.bio || '';
  document.getElementById('settingsMobile').value = appState.user.mobile_number || '';
  document.getElementById('settingsGender').value = appState.user.gender || '';

  // Set avatar
  const avatarImg = document.getElementById('settingsProfileAvatar');
  const displayName = `${appState.user.first_name || ''} ${appState.user.last_name || ''}`.trim();
  avatarImg.src = appState.user.avatar_url || generateAvatarUrl(displayName);
}

async function saveProfile() {
  try {
    const payload = {
      first_name: document.getElementById('settingsFirstName').value,
      last_name: document.getElementById('settingsLastName').value,
      bio: document.getElementById('settingsBio').value,
      gender: document.getElementById('settingsGender').value,
      mobile_number: document.getElementById('settingsMobile').value,
      avatar_url: appState.user.avatar_url
    };

    const response = await fetch(`${CONFIG.backendUrl}/auth/profile`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${appState.authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || 'Failed to save profile');
    }

    appState.user = result;
    setMessage('settingsMessage', '✓ Profile saved successfully', 'success');
    displayUserInfo();

    // Update localStorage
    localStorage.setItem('user', JSON.stringify(appState.user));
  } catch (error) {
    console.error('Error saving profile:', error);
    setMessage('settingsMessage', `Error: ${error.message}`, 'error');
  }
}

function handleAvatarUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  // For now, just show a message
  // In a real app, you'd upload to a server or cloud storage
  alert('Avatar upload functionality coming soon. You can use the avatar URL field to set a custom avatar.');
}

async function saveNotifications() {
  // For now, just show a success message
  // In a real app, you'd save preferences to the backend
  setMessage('settingsMessage', '✓ Notification preferences saved', 'success');
  setTimeout(() => {
    document.getElementById('notifMessage')?.textContent = '';
  }, 3000);
}

function setMessage(elementId, message, type) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = message;
    element.className = `message ${type}`;
    
    // Clear after 5 seconds if success
    if (type === 'success') {
      setTimeout(() => {
        element.textContent = '';
        element.className = 'message';
      }, 5000);
    }
  }
}

function switchSection(sectionName) {
  // Hide all sections
  document.querySelectorAll('.settings-section').forEach(section => {
    section.classList.remove('active');
  });

  // Remove active from nav items
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
  });

  // Show selected section
  const sectionElement = document.getElementById(`${sectionName}-section`);
  if (sectionElement) {
    sectionElement.classList.add('active');
  }

  // Mark nav item as active
  document.querySelector(`[data-section="${sectionName}"]`)?.classList.add('active');

  appState.currentSection = sectionName;
}
