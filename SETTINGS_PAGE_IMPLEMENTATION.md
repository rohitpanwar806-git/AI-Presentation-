# AI Presentation Avatar - Enhanced Portal UI Implementation

**Reference Design**: Based on Akool.com Portal | **Date**: May 25, 2026

---

## 🎨 Phase 1: Enhanced Profile Dropdown (Ready to Implement)

### Current State ✅
- Avatar chip in header with click-to-open dropdown
- Profile name, email, mobile, gender, bio fields
- Avatar URL with live preview
- Save button with success/error messages

### Next Enhancement: Quick Stats Bar

**Add to Profile Dropdown:**
```html
<div id="profileDropdown" class="profile-dropdown hidden">
  <div class="profile-dropdown-header">
    <h3>Account Overview</h3>
    <button id="closeProfileBtn" class="close-btn">✕</button>
  </div>
  
  <!-- NEW: Quick Stats Section -->
  <div class="profile-quick-stats">
    <div class="stat-item">
      <span class="stat-label">Plan:</span>
      <span class="stat-value" id="profilePlan">Free</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">Presentations:</span>
      <span class="stat-value" id="profilePresentationCount">0</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">Storage:</span>
      <span class="stat-value" id="profileStorageUsage">0 MB / 5 GB</span>
    </div>
  </div>
  
  <div class="profile-dropdown-body">
    <!-- Existing form fields -->
    ...
  </div>
</div>
```

**CSS for Quick Stats:**
```css
.profile-quick-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 12px;
  background: rgba(108, 92, 231, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.stat-label {
  color: #a0a0a0;
}

.stat-value {
  color: #00b4d8;
  font-weight: 600;
}
```

---

## 📄 Phase 2: Dedicated Settings Page (Next)

### **Route Structure**
```
/dashboard              - Main dashboard
/settings             - All settings pages
  /settings/profile   - Profile info
  /settings/security  - Password, 2FA
  /settings/notifications - Email prefs
  /settings/billing   - Plan & usage
  /settings/api       - API keys
  /settings/account   - Account deletion
```

### **HTML Structure for Settings Page**

```html
<!DOCTYPE html>
<html>
<head>
  <title>Settings - AI Presentation Avatar</title>
</head>
<body>
  <!-- Header (Same as main app) -->
  <header class="app-header">
    <div class="header-content">
      <div class="logo-area">
        <a href="/" class="logo">🎬 AI Presentation Avatar</a>
      </div>
      <div class="header-right">
        <button id="userChip" class="user-chip">
          <img id="userChipAvatar" src="" alt="Avatar">
          <span id="userChipText">User</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Main Settings Layout -->
  <div class="settings-container">
    <!-- Sidebar Navigation -->
    <aside class="settings-sidebar">
      <nav class="settings-nav">
        <button class="nav-item active" data-section="profile">
          <span class="icon">👤</span>
          <span>Profile</span>
        </button>
        <button class="nav-item" data-section="security">
          <span class="icon">🔒</span>
          <span>Security</span>
        </button>
        <button class="nav-item" data-section="notifications">
          <span class="icon">🔔</span>
          <span>Notifications</span>
        </button>
        <button class="nav-item" data-section="billing">
          <span class="icon">💳</span>
          <span>Billing & Plan</span>
        </button>
        <button class="nav-item" data-section="api">
          <span class="icon">🔑</span>
          <span>API Keys</span>
        </button>
        <button class="nav-item" data-section="account">
          <span class="icon">⚠️</span>
          <span>Account</span>
        </button>
      </nav>
    </aside>

    <!-- Main Content Area -->
    <main class="settings-content">
      <!-- PROFILE SECTION -->
      <section id="profile-section" class="settings-section active">
        <div class="section-header">
          <h2>Profile Settings</h2>
          <p>Manage your personal information</p>
        </div>

        <div class="settings-form">
          <!-- Avatar Upload -->
          <div class="form-group">
            <label>Profile Picture</label>
            <div class="avatar-upload-area">
              <img id="settingsProfileAvatar" src="" alt="Profile" class="avatar-preview">
              <div class="upload-controls">
                <input type="file" id="avatarUpload" accept="image/*" style="display:none">
                <button onclick="document.getElementById('avatarUpload').click()" class="btn btn-secondary">
                  Change Picture
                </button>
                <button class="btn btn-text">Remove</button>
              </div>
            </div>
          </div>

          <!-- Name -->
          <div class="form-group">
            <label for="settingsFirstName">First Name</label>
            <input type="text" id="settingsFirstName" class="form-control" placeholder="John">
          </div>

          <div class="form-group">
            <label for="settingsLastName">Last Name</label>
            <input type="text" id="settingsLastName" class="form-control" placeholder="Doe">
          </div>

          <!-- Email -->
          <div class="form-group">
            <label for="settingsEmail">Email Address</label>
            <div class="email-field">
              <input type="email" id="settingsEmail" class="form-control" disabled>
              <span class="verified-badge">✓ Verified</span>
            </div>
            <small>Change email requires reverification</small>
          </div>

          <!-- Bio -->
          <div class="form-group">
            <label for="settingsBio">Bio / About</label>
            <textarea id="settingsBio" class="form-control" rows="4" 
              placeholder="Tell us about yourself..."></textarea>
          </div>

          <!-- Social Links -->
          <div class="form-group">
            <label for="settingsWebsite">Website / Portfolio</label>
            <input type="url" id="settingsWebsite" class="form-control" 
              placeholder="https://example.com">
          </div>

          <div class="form-group">
            <label for="settingsLinkedIn">LinkedIn Profile</label>
            <input type="text" id="settingsLinkedIn" class="form-control" 
              placeholder="linkedin.com/in/username">
          </div>

          <!-- Save Button -->
          <div class="form-actions">
            <button id="saveSettingsBtn" class="btn btn-primary">Save Changes</button>
            <span id="settingsMessage" class="message"></span>
          </div>
        </div>
      </section>

      <!-- SECURITY SECTION -->
      <section id="security-section" class="settings-section" style="display:none">
        <div class="section-header">
          <h2>Security Settings</h2>
          <p>Protect your account</p>
        </div>

        <div class="security-items">
          <!-- Change Password -->
          <div class="security-item">
            <div class="item-header">
              <h3>Password</h3>
              <p>Last changed 3 months ago</p>
            </div>
            <button class="btn btn-secondary" onclick="showChangePasswordModal()">
              Change Password
            </button>
          </div>

          <!-- Two-Factor Authentication -->
          <div class="security-item">
            <div class="item-header">
              <h3>Two-Factor Authentication</h3>
              <p>Add an extra layer of security</p>
            </div>
            <div class="item-status">
              <span class="badge badge-disabled">Disabled</span>
              <button class="btn btn-primary" onclick="show2FASetup()">
                Enable 2FA
              </button>
            </div>
          </div>

          <!-- Active Sessions -->
          <div class="security-item">
            <div class="item-header">
              <h3>Active Sessions</h3>
              <p>Manage devices signed in to your account</p>
            </div>
            <div id="sessions-list" class="sessions-list">
              <!-- Sessions will be listed here -->
            </div>
          </div>

          <!-- Login History -->
          <div class="security-item">
            <div class="item-header">
              <h3>Login History</h3>
              <p>Recent account access</p>
            </div>
            <button class="btn btn-secondary" onclick="showLoginHistory()">
              View Login History
            </button>
          </div>
        </div>
      </section>

      <!-- NOTIFICATIONS SECTION -->
      <section id="notifications-section" class="settings-section" style="display:none">
        <div class="section-header">
          <h2>Notification Preferences</h2>
          <p>Choose how you want to be contacted</p>
        </div>

        <div class="notification-preferences">
          <div class="preference-item">
            <div class="preference-header">
              <h3>Email Notifications</h3>
            </div>
            <label class="checkbox-item">
              <input type="checkbox" id="emailPresentation" checked>
              <span>Presentation updates and completion</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" id="emailAccount" checked>
              <span>Account changes and security alerts</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" id="emailPromo">
              <span>Product updates and promotions</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" id="emailWeekly">
              <span>Weekly digest of usage statistics</span>
            </label>
          </div>

          <div class="preference-item">
            <div class="preference-header">
              <h3>System Notifications</h3>
            </div>
            <label class="checkbox-item">
              <input type="checkbox" id="inAppNotif" checked>
              <span>Show in-app notifications</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" id="pushNotif">
              <span>Browser push notifications</span>
            </label>
          </div>

          <div class="form-actions">
            <button id="saveNotifBtn" class="btn btn-primary">Save Preferences</button>
          </div>
        </div>
      </section>

      <!-- BILLING SECTION -->
      <section id="billing-section" class="settings-section" style="display:none">
        <div class="section-header">
          <h2>Billing & Plan</h2>
          <p>Manage your subscription</p>
        </div>

        <div class="billing-container">
          <div class="current-plan">
            <h3>Current Plan</h3>
            <div class="plan-card">
              <div class="plan-name">Free Plan</div>
              <div class="plan-details">
                <div>Monthly credits: 100</div>
                <div>Storage: 5 GB</div>
                <div>Presentations: Unlimited</div>
              </div>
              <button class="btn btn-primary">Upgrade to Pro</button>
            </div>
          </div>

          <div class="billing-history">
            <h3>Billing History</h3>
            <table class="invoices-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Invoice</th>
                </tr>
              </thead>
              <tbody>
                <!-- Invoices will be listed here -->
              </tbody>
            </table>
          </div>

          <div class="payment-methods">
            <h3>Payment Methods</h3>
            <button class="btn btn-secondary">Add Payment Method</button>
          </div>
        </div>
      </section>

      <!-- API KEYS SECTION -->
      <section id="api-section" class="settings-section" style="display:none">
        <div class="section-header">
          <h2>API Keys</h2>
          <p>Manage developer access</p>
        </div>

        <div class="api-container">
          <button class="btn btn-primary" onclick="showGenerateKeyModal()">
            Generate New Key
          </button>

          <div id="api-keys-list" class="api-keys-list">
            <!-- API keys will be listed here -->
          </div>

          <div class="api-documentation">
            <h3>Documentation</h3>
            <p>Learn how to use the API</p>
            <button class="btn btn-secondary">
              <a href="/docs/api" target="_blank">View API Docs</a>
            </button>
          </div>
        </div>
      </section>

      <!-- ACCOUNT SECTION -->
      <section id="account-section" class="settings-section" style="display:none">
        <div class="section-header">
          <h2>Account</h2>
          <p>Manage your account status</p>
        </div>

        <div class="account-items">
          <div class="account-item danger">
            <div class="item-header">
              <h3>Download Your Data</h3>
              <p>Export all your presentations and settings</p>
            </div>
            <button class="btn btn-secondary">Download Data</button>
          </div>

          <div class="account-item danger">
            <div class="item-header">
              <h3>Delete Account</h3>
              <p>Permanently delete your account and all data</p>
            </div>
            <button class="btn btn-danger" onclick="showDeleteAccountModal()">
              Delete Account
            </button>
          </div>
        </div>
      </section>
    </main>
  </div>

  <!-- Modals (will be added below) -->
  <div id="changePasswordModal" class="modal hidden">
    <!-- Change password form -->
  </div>

  <!-- Scripts -->
  <script src="settings.js"></script>
</body>
</html>
```

---

## 🎨 CSS Styling for Settings Page

```css
/* Settings Container Layout */
.settings-container {
  display: flex;
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  min-height: calc(100vh - 80px);
}

/* Sidebar Navigation */
.settings-sidebar {
  width: 240px;
  flex-shrink: 0;
}

.settings-nav {
  position: sticky;
  top: 80px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  color: #a0a0a0;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
}

.nav-item:hover {
  background: rgba(108, 92, 231, 0.1);
  color: #e8e8e8;
  border-color: rgba(108, 92, 231, 0.2);
}

.nav-item.active {
  background: rgba(108, 92, 231, 0.2);
  color: #6c5ce7;
  border-color: #6c5ce7;
}

.nav-item .icon {
  font-size: 18px;
}

/* Main Content Area */
.settings-content {
  flex: 1;
  min-width: 0;
}

.settings-section {
  background: #1a1f2e;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 32px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.section-header {
  margin-bottom: 32px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 24px;
}

.section-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #e8e8e8;
  margin-bottom: 8px;
}

.section-header p {
  color: #a0a0a0;
  font-size: 14px;
}

/* Form Styling */
.settings-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: #e8e8e8;
}

.form-control {
  padding: 12px 16px;
  background: #0f1419;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #e8e8e8;
  font-size: 14px;
  transition: all 0.2s ease;
}

.form-control:focus {
  outline: none;
  border-color: #6c5ce7;
  box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.1);
}

.form-control:disabled {
  background: rgba(255, 255, 255, 0.05);
  color: #a0a0a0;
  cursor: not-allowed;
}

/* Avatar Upload Area */
.avatar-upload-area {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.avatar-preview {
  width: 120px;
  height: 120px;
  border-radius: 12px;
  object-fit: cover;
  border: 2px solid rgba(108, 92, 231, 0.3);
}

.upload-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Security Items */
.security-items {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.security-item {
  padding: 24px;
  background: #0f1419;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.security-item .item-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #e8e8e8;
  margin-bottom: 4px;
}

.security-item .item-header p {
  color: #a0a0a0;
  font-size: 13px;
}

/* Buttons */
.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #6c5ce7 0%, #00b4d8 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(108, 92, 231, 0.3);
}

.btn-secondary {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #e8e8e8;
}

.btn-secondary:hover {
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.05);
}

.btn-danger {
  background: #e74c3c;
  color: white;
}

.btn-danger:hover {
  background: #c0392b;
}

.btn-text {
  background: transparent;
  color: #6c5ce7;
  padding: 8px 12px;
}

/* Responsive Design */
@media (max-width: 768px) {
  .settings-container {
    flex-direction: column;
    gap: 0;
  }

  .settings-sidebar {
    width: 100%;
    position: relative;
    top: 0;
  }

  .settings-nav {
    position: static;
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 8px;
  }

  .settings-section {
    padding: 24px 16px;
  }

  .avatar-upload-area {
    flex-direction: column;
    align-items: center;
  }
}
```

---

## 📋 Implementation Plan

### **Frontend Files to Modify/Create**

1. **Create: `frontend/web/settings.html`**
   - New settings page (use structure above)

2. **Create: `frontend/web/settings.js`**
   - Navigation between sections
   - Load user data
   - Handle form submissions
   - Modal management

3. **Create: `frontend/web/settings.css`**
   - All styling (use CSS above)

4. **Modify: `frontend/web/index.html`**
   - Add link to settings page in user menu

5. **Modify: `frontend/web/app.js`**
   - Add settings navigation functions
   - Handle settings updates via API

### **Backend Files to Verify**

- ✅ [backend/api/auth.py](backend/api/auth.py) - Has PUT /auth/profile endpoint
- ✅ [backend/db/models.py](backend/db/models.py) - User model has all fields
- ⏳ Add GET /auth/admin/sessions endpoint (for session management)
- ⏳ Add GET /auth/login-history endpoint (for login history)

---

## 🔄 Data Flow

```javascript
User Flow:
1. User clicks settings link
2. Load settings page
3. Fetch user data from /auth/profile
4. Display in form fields
5. User edits fields
6. Submit to PUT /auth/profile
7. Show success/error message
8. Update appState.user
9. Sync with profile dropdown
```

---

## ✅ Quality Checklist

- [ ] Settings page responsive on mobile
- [ ] Form validation before submit
- [ ] Error messages clear and actionable
- [ ] Success feedback to user
- [ ] All fields sync correctly
- [ ] No sensitive data in console logs
- [ ] Accessibility (keyboard nav, screen reader)
- [ ] Performance (lazy load sections)
- [ ] Animations smooth (60fps)

---

## 🎯 Success Metrics

Track these after implementation:
- Settings page load time < 2s
- Form submission success rate > 95%
- Mobile completion rate
- User feedback/ratings
- Settings edit frequency

---

**Ready to implement Phase 2 settings dashboard!**
