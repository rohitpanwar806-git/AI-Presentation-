# Portal UI & User Profile Options - Design Guide
**Reference**: Akool.com Portal UI | **Updated**: May 25, 2026

---

## 📱 Modern SaaS Portal UI - Best Practices

Based on industry leaders like Akool, here's what makes a great portal interface:

### 1. **Header Navigation Structure**

**Akool Implementation:**
```
┌─────────────────────────────────────────────────────┐
│ 🎨 LOGO    [⚡ Upgrade Button]  🌐  ☰ (Menu)       │
└─────────────────────────────────────────────────────┘
```

**Key Elements:**
- **Logo** (left side) - Clickable, returns to home
- **Primary CTA** - "Upgrade" button in prominent color (gradient purple)
- **Language Selector** - Globe icon for i18n
- **Mobile Menu** - Hamburger menu for responsive design
- **User Menu** - Avatar dropdown (right corner) for signed-in users

---

## 👤 User Profile Options - Comprehensive Menu

### **Level 1: Avatar Chip (Header)**
When user clicks their profile picture/avatar in header:

```
┌─────────────────────────────────┐
│ 👤 John Doe  ▼                  │
│                                  │
│ ┌─ Account Settings ──────────┐ │
│ │ • Profile                   │ │
│ │ • Account Settings          │ │
│ │ • Billing & Plans           │ │
│ │ • API Keys                  │ │
│ │ • Notifications             │ │
│ │ • Privacy & Security        │ │
│ │                             │ │
│ │ [Sign Out]                  │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

### **Level 2: Profile Section**

**Profile Overview:**
- **Profile Picture** - Avatar upload/change
- **Display Name** - Full name or username
- **Email Address** - Primary contact
- **Bio / About** - Optional personal description
- **Location** - City, country
- **Company** - Organization name
- **Website** - Personal/company URL
- **Social Links** - LinkedIn, Twitter, etc.

**Status Indicators:**
- Verification badge ✓
- Account status (Free, Pro, Enterprise)
- Member since (join date)
- Last active timestamp

### **Level 3: Account Settings**

#### **3.1 Security Settings**
- Change password
- Two-factor authentication (2FA)
  - Authenticator app
  - SMS verification
  - Backup codes
- Active sessions
- Device management
- Login history
- Recovery email
- Recovery phone

#### **3.2 Notification Preferences**
- Email notifications
  - Order updates
  - Account changes
  - Marketing emails
  - Weekly digest
  - System alerts
- Push notifications
- In-app notifications
- Notification frequency

#### **3.3 Privacy Settings**
- Profile visibility (Public/Private)
- Search indexing
- Data sharing preferences
- Download your data
- Delete account

#### **3.4 Billing & Subscription**
- Current plan details
- Billing cycle (Monthly/Annual)
- Payment method
- Invoice history
- Usage quota/remaining
- Upgrade/Downgrade
- Auto-renewal toggle
- Billing email

#### **3.5 API Keys & Integration**
- Generate new API key
- Regenerate existing key
- View secret key (once)
- Copy to clipboard
- Delete key
- Key usage statistics
- Webhooks configuration
- Integration status

---

## 🎨 UI/UX Design Patterns (From Akool)

### **Color Scheme**
```
Primary:     #6C5CE7 (Vibrant Purple) - CTAs, highlights
Secondary:   #00B4D8 (Cyan) - Links, accents
Dark BG:     #0F1419 (Near black) - Main background
Card BG:     #1A1F2E (Dark gray) - Card/panel background
Text:        #E8E8E8 (Light gray) - Primary text
Text-muted:  #A0A0A0 (Medium gray) - Secondary text
Success:     #27AE60 (Green) - Positive actions
Error:       #E74C3C (Red) - Warnings, errors
Warning:     #F39C12 (Orange) - Cautionary info
```

### **Typography**
- **Headlines**: Bold, large (24-32px)
- **Labels**: Medium weight, readable (14-16px)
- **Body text**: Regular, good line height (16-18px)
- **Code**: Monospace (Monaco, Courier)

### **Spacing & Layout**
- **Grid**: 4px baseline (multiples of 4)
- **Padding**: 16px, 24px, 32px
- **Margins**: Consistent vertical rhythm
- **Max width**: 1200px for content

### **Components**
- **Buttons**: Gradient background, rounded corners
  - Primary: Full gradient
  - Secondary: Outline style
  - Tertiary: Text only
  
- **Cards**: Subtle border, shadow on hover
  - Padding: 24px
  - Border radius: 12px
  - Border: 1px solid rgba(255,255,255,0.1)

- **Inputs**: Clean, focused state
  - Border on focus
  - Error state styling
  - Clear error messages

- **Modals**: Dark overlay, centered dialog
  - Title, content, actions
  - Close button (X) top-right
  - Scrollable on small screens

---

## 📊 Dashboard Features

### **Quick Stats Widget**
```
┌────────────────────────────────┐
│ Your Account Overview          │
├────────────────────────────────┤
│ 📊 Credits Used:   42 / 100    │
│ ⏰ Last Used:      2 mins ago  │
│ 📅 Renewal Date:   June 1      │
│ 📈 Current Plan:   Professional│
└────────────────────────────────┘
```

### **Usage Analytics**
- Monthly usage breakdown
- Feature usage statistics
- API call statistics
- Storage usage
- Export metrics

### **Quick Actions**
- Upgrade plan
- Add payment method
- View documentation
- Contact support
- View recent projects

---

## 🔐 Security Best Practices Shown

**From Akool's approach:**
1. **SOC 2 Compliance** - Displayed prominently
2. **Data Encryption** - At rest and in transit
3. **Regular Audits** - Third-party security reviews
4. **Trust Badges** - Security certifications
5. **Transparent Privacy** - Clear policy access
6. **Activity Logging** - User can view login history
7. **Session Management** - View and revoke active sessions

---

## 🎯 AI Presentation Avatar Portal - Recommendations

### **Immediate Enhancements to Make**

#### **1. Enhanced User Profile Card (In Header)**
```javascript
// Current state - needs expansion
Current: Simple avatar + dropdown

Recommended:
├─ Avatar Section
│  ├─ Profile picture (editable)
│  ├─ Display name
│  ├─ Verification badge
│  └─ Account tier badge
├─ Quick Stats
│  ├─ Presentations created: 5
│  ├─ Storage used: 2.3 GB / 10 GB
│  └─ Credits remaining: 150
└─ Quick Actions
   ├─ [Create Presentation]
   ├─ [Upgrade Plan]
   └─ [Account Settings]
```

#### **2. Sidebar Navigation** (For logged-in users)
```
Left Sidebar (Collapsible):
├─ 🏠 Dashboard
├─ 📄 My Presentations
│  ├─ Recent
│  ├─ Archived
│  └─ Shared with Me
├─ 🎨 Templates
├─ 🗣️ Voice Library
├─ 👥 Avatars
├─ 📊 Usage & Billing
├─ ⚙️ Settings
└─ 💬 Support
```

#### **3. User Settings Hierarchy**
```
Settings Page Structure:
├─ Profile
│  ├─ Basic Info (Name, Email, Bio)
│  ├─ Avatar & Banner
│  ├─ Social Links
│  └─ Preferences
├─ Security
│  ├─ Password
│  ├─ 2FA
│  ├─ Sessions
│  └─ Login History
├─ Notifications
│  ├─ Email Settings
│  ├─ Push Notifications
│  └─ Notification Center
├─ Billing
│  ├─ Current Plan
│  ├─ Payment Methods
│  ├─ Invoices
│  └─ Usage Quota
├─ API Keys
│  ├─ Generate Key
│  ├─ Manage Keys
│  └─ Webhooks
└─ Account
   ├─ Download Data
   ├─ Delete Account
   └─ Privacy Settings
```

#### **4. Team/Organization Features** (Future)
```
Organizations:
├─ Create Organization
├─ Manage Members
│  ├─ Invite users
│  ├─ Set roles (Owner, Editor, Viewer)
│  └─ Manage permissions
├─ Billing
│  ├─ Team subscription
│  └─ Usage allocation
└─ Team Settings
   ├─ Brand customization
   └─ Domain verification
```

---

## 🚀 Implementation Roadmap

### **Phase 1: User Profile Expansion** (Now)
- [x] Profile dropdown (basic)
- [ ] Profile page (dedicated route)
- [ ] Avatar upload
- [ ] Edit profile fields
- [ ] Social links
- [ ] Verification badges

### **Phase 2: Settings Dashboard** (Next)
- [ ] Account settings page
- [ ] Security settings
- [ ] Notification preferences
- [ ] Privacy controls
- [ ] Session management

### **Phase 3: Billing & Usage** (Future)
- [ ] Usage dashboard
- [ ] Billing history
- [ ] Payment methods
- [ ] Plan upgrade/downgrade
- [ ] Invoice download

### **Phase 4: Team Features** (Later)
- [ ] Organization creation
- [ ] Member management
- [ ] Role-based access
- [ ] Team billing

---

## 💻 UI Components Library (To Create)

```javascript
// Reusable components needed:
1. ProfileCard
   - props: user, compact/expanded mode
   - shows: avatar, name, stats
   
2. SettingsPanel
   - props: section (profile|security|billing)
   - shows: sidebar + content area
   
3. StatWidget
   - props: icon, label, value, percentage
   - shows: metric with visual indicator
   
4. QuickActionButton
   - props: icon, label, onClick
   - shows: rounded button with icon
   
5. FormSection
   - props: title, fields, onSave
   - shows: form with validation
   
6. NotificationBadge
   - props: count, color
   - shows: small badge on avatar
```

---

## 📝 Content Strategy

### **Microcopy Examples (From Akool)**
```
❌ "Save" 
✅ "Save Changes" (clearer intent)

❌ "Delete"
✅ "Delete Account" (confirmation tone)

❌ "Error"
✅ "Couldn't save your changes. Try again or contact support." (helpful)

❌ "Loading"
✅ "Preparing your account..." (contextual)
```

---

## 🎪 Responsive Design (Mobile-First)

### **Mobile Menu Pattern** (From Akool)
```
Mobile Top Bar:
┌─────────────────────────────────┐
│ Logo          [👤] [☰]         │
└─────────────────────────────────┘

Side Drawer (On ☰ click):
┌─────────────────────────────────┐
│ ╳                               │
│                                  │
│ 🏠 Dashboard                    │
│ 📄 Presentations                │
│ ⚙️ Settings                     │
│ 💬 Support                      │
│                                  │
│ ─────────────────────────────── │
│ 👤 John Doe                     │
│ 📧 john@example.com            │
│ [Sign Out]                      │
└─────────────────────────────────┘
```

---

## ✅ Implementation Checklist

- [ ] Responsive header with user menu
- [ ] Profile page (dedicated route)
- [ ] Settings sidebar navigation
- [ ] Security settings form
- [ ] Notification preferences
- [ ] Billing/usage dashboard
- [ ] Account deletion flow
- [ ] Session management view
- [ ] Login history display
- [ ] API key management
- [ ] 2FA setup flow
- [ ] Password change form
- [ ] Email verification flow
- [ ] Privacy policy modal
- [ ] Support/help integration

---

## 🔗 Related Features to AI Presentation Avatar

### **Presentation-Specific Settings**
- Default avatar preference
- Preferred voices
- Default language
- Template preferences
- Export quality settings
- Watermark toggle
- Branding options

### **Integration Points**
- Profile avatar → Default presentation avatar
- User bio → Creator info on presentation
- Company name → Branding customization
- Email → Account recovery
- 2FA → Account security

---

## 📚 Reference Files Location

- **Current Profile Dropdown**: [frontend/web/app.js](frontend/web/app.js#L430-L480)
- **User Model**: [backend/db/models.py](backend/db/models.py)
- **Auth Endpoints**: [backend/api/auth.py](backend/api/auth.py)
- **Frontend Config**: [frontend/web/config.js](frontend/web/config.js)

---

## 🎯 Next Steps

1. **Review** this design guide with your team
2. **Prioritize** features for MVP
3. **Design** UI mockups for new pages
4. **Implement** phase 1 (profile expansion)
5. **Test** on mobile devices
6. **Gather** user feedback
7. **Iterate** based on analytics

---

**This guide provides a complete blueprint for building a modern, user-friendly portal that matches industry standards set by leaders like Akool. Start with profile expansion and gradually add more sophisticated features as needed.**
