# 🎨 Responsive Design - Developer Quick Reference

**Quick Guide for Maintaining & Extending RWD**

---

## 🎯 Quick Facts

- **Approach:** Mobile-first with CSS Grid/Flexbox
- **Breakpoints:** 320px, 480px, 768px, 980px, 1200px
- **Scaling Method:** `clamp()` for typography and spacing
- **Touch Targets:** 44px minimum (WCAG AA)
- **Container Max:** 1180px
- **CSS Variables:** Used for all responsive sizing

---

## 📐 CSS Breakpoints Reference

```css
/* Mobile XS (320px-479px) */
@media (max-width: 320px) { }
@media (max-width: 480px) { }

/* Tablet (481px-767px) */
@media (min-width: 481px) and (max-width: 767px) { }

/* Tablet-Desktop (768px-979px) */
@media (max-width: 768px) { }

/* Desktop (769px-1199px) */
@media (min-width: 769px) { }

/* Large Desktop (980px-1199px) */
@media (min-width: 980px) { }

/* Extra Large (1200px+) */
@media (min-width: 1200px) { }
```

---

## 🔧 Common Responsive Patterns

### Responsive Font Sizes
```css
/* Mobile-friendly scaling */
.heading { font-size: clamp(1.5rem, 4vw, 2.3rem); }
.body { font-size: clamp(14px, 2vw, 16px); }
.small { font-size: clamp(12px, 1.8vw, 14px); }
```

### Responsive Spacing
```css
/* Padding/margin that scales */
.card { padding: clamp(12px, 2.5vw, 20px); }
.section { margin-bottom: clamp(16px, 3vw, 24px); }
.gap { gap: clamp(8px, 2vw, 16px); }
```

### Responsive Grid
```css
/* 1 col on mobile, 2 on tablet, 4 on desktop */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: clamp(12px, 2vw, 16px);
}
```

### Responsive Flex
```css
/* Wraps on mobile, spreads on desktop */
.flex {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
}
```

### Two-Column Layout
```css
/* 2 col on desktop, 1 col on mobile */
.layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: clamp(12px, 2.5vw, 24px);
}

@media (max-width: 768px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
```

---

## 🔤 CSS Variables for Responsive Sizing

```css
:root {
  /* Font sizes */
  --font-base: clamp(14px, 2vw, 16px);
  --font-small: clamp(12px, 1.8vw, 14px);
  --font-large: clamp(18px, 2.5vw, 24px);
  --font-xlarge: clamp(24px, 4vw, 32px);
  
  /* Spacing */
  --spacing-xs: clamp(4px, 1vw, 8px);
  --spacing-sm: clamp(8px, 1.5vw, 12px);
  --spacing-md: clamp(12px, 2vw, 16px);
  --spacing-lg: clamp(16px, 2.5vw, 24px);
  --spacing-xl: clamp(20px, 3vw, 32px);
}
```

**Usage:**
```css
body { font-size: var(--font-base); }
.card { padding: var(--spacing-lg); }
.grid { gap: var(--spacing-md); }
```

---

## ✅ Adding New Responsive Elements

### New Card Component
```css
.new-card {
  /* Base styles */
  background: #fff;
  border-radius: 14px;
  border: 1px solid var(--line);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
  
  /* Responsive width */
  width: 100%;
  max-width: 100%;
  
  /* Responsive font */
  font-size: var(--font-base);
}

/* Stack on mobile, side-by-side on desktop */
.new-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-md);
}
```

### New Form Input
```css
.new-input {
  width: 100%;
  padding: clamp(8px, 1.5vw, 10px) clamp(10px, 2vw, 12px);
  font-size: clamp(13px, 2vw, 16px);
  min-height: 44px;  /* Touch target */
  border: 1px solid #ccc;
  border-radius: 8px;
}

/* Responsive label */
.new-input-label {
  font-size: var(--font-small);
  margin-bottom: var(--spacing-xs);
}

/* Two columns on desktop, 1 on mobile */
.new-input-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-sm);
}

@media (max-width: 480px) {
  .new-input-row {
    grid-template-columns: 1fr;
  }
}
```

### New Button
```css
.new-btn {
  padding: clamp(8px, 1.5vw, 10px) clamp(12px, 2vw, 16px);
  font-size: clamp(13px, 2vw, 16px);
  min-height: 44px;
  min-width: 44px;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

/* Responsive button group */
.new-btn-group {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

@media (max-width: 480px) {
  .new-btn-group {
    flex-direction: column;
  }

  .new-btn {
    width: 100%;
  }
}
```

---

## 📋 Responsive Element Checklist

When adding new elements, ensure:

- [ ] Uses responsive font sizes (clamp)
- [ ] Uses responsive spacing (CSS variables)
- [ ] Has proper touch targets (44px+)
- [ ] Works on mobile (320px)
- [ ] Works on tablet (768px)
- [ ] Works on desktop (1200px)
- [ ] No horizontal scrolling
- [ ] Text is readable
- [ ] Images scale properly
- [ ] Forms are usable on mobile
- [ ] Interactive elements are accessible
- [ ] Dark mode considered
- [ ] Print styles considered

---

## 🎨 Container Queries (Future)

```css
/* Modern approach (not in current browser support) */
@container (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 100px 1fr;
  }
}
```

---

## 📱 Testing Quick Commands

### Chrome DevTools
```javascript
// Get all media queries
window.matchMedia('(min-width: 768px)').matches  // true/false

// Get viewport size
console.log(window.innerWidth, window.innerHeight)

// Test touch device
window.matchMedia('(hover: none)').matches  // true if touch
```

### CSS Testing
```css
/* Verify clamp works */
.test { font-size: clamp(10px, 2vw, 20px); }

/* Check breakpoint */
@media (max-width: 768px) {
  .test { color: red; }
}
```

---

## 🔴 Common Mistakes to Avoid

### ❌ Fixed Widths
```css
/* Bad */
.card { width: 300px; }

/* Good */
.card { 
  width: 100%;
  max-width: 300px;
}
```

### ❌ No Touch Targets
```css
/* Bad */
.btn { padding: 2px 4px; }

/* Good */
.btn { min-height: 44px; }
```

### ❌ No Responsive Spacing
```css
/* Bad */
.card { padding: 20px; }

/* Good */
.card { padding: clamp(12px, 2.5vw, 20px); }
```

### ❌ Hardcoded Breakpoints
```css
/* Bad */
@media (max-width: 768px) {
  body { font-size: 14px; }
}

/* Good */
body { font-size: clamp(14px, 2vw, 16px); }
```

### ❌ Overflow Issues
```css
/* Bad */
.container { width: 1200px; }  /* On 320px phone = overflow */

/* Good */
.container {
  width: min(1200px, calc(100% - 2rem));
}
```

---

## 🎯 Testing Checklist

- [ ] Tested on iPhone (375px)
- [ ] Tested on Android (360px)
- [ ] Tested on iPad (768px)
- [ ] Tested on Desktop (1920px)
- [ ] Tested in portrait mode
- [ ] Tested in landscape mode
- [ ] Tested with browser zoom (100%, 150%, 200%)
- [ ] Tested with reduced motion enabled
- [ ] Tested with dark mode enabled
- [ ] Tested with screen reader
- [ ] Tested touch interactions
- [ ] Tested keyboard navigation

---

## 📚 Resources

### Learn More
- [MDN: Responsive Web Design](https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design)
- [CSS Tricks: A Complete Guide to Grid](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [CSS Tricks: A Complete Guide to Flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)
- [Can I Use: clamp()](https://caniuse.com/css-clamp)

### Tools
- Chrome DevTools Device Mode
- Firefox Responsive Design Mode
- BrowserStack
- Responsively App

---

## 💡 Pro Tips

### 1. Use CSS Variables
```css
:root { --spacing: clamp(8px, 2vw, 16px); }
.element { padding: var(--spacing); }
```

### 2. Mobile First
Write mobile styles first, then add `@media (min-width: X)` for larger screens.

### 3. Test Regularly
Test on actual devices, not just DevTools.

### 4. Use clamp()
```css
/* No media queries needed */
font-size: clamp(14px, 2vw, 16px);
```

### 5. Touch Targets
Always ensure interactive elements are at least 44x44px.

### 6. Container Queries (Future)
Prepare for container queries which are more flexible than media queries.

### 7. Print Styles
Don't forget print media:
```css
@media print {
  .no-print { display: none; }
}
```

### 8. Reduced Motion
Respect user preferences:
```css
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; }
}
```

---

## 🚀 Performance Tips

1. **Use CSS Variables** - Faster than recalculating
2. **Avoid Calc Overuse** - Only when necessary
3. **CSS Grid > Floats** - More performant
4. **Flexbox > Tables** - Better for layouts
5. **Optimize Images** - Use srcset for responsive images
6. **Lazy Load** - Load images as needed
7. **Minimize Media Queries** - Use CSS variables instead

---

## ✅ Final Checklist Before Deployment

- [x] All responsive sizes tested
- [x] CSS variables working
- [x] Media queries correct
- [x] Touch targets 44px+
- [x] No horizontal overflow
- [x] Images scale properly
- [x] Forms usable on mobile
- [x] Navigation responsive
- [x] Performance optimized
- [x] Accessibility verified

---

**Last Updated:** May 25, 2026  
**Status:** ✅ Complete  
**Ready for:** Production deployment

