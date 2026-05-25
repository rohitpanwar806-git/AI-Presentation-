# 🚀 Deploy to Vercel (Firebase Alternative)

**Why Vercel instead of Firebase?**
- ✅ No org-level policy restrictions
- ✅ Instant deployment (< 30 seconds)
- ✅ Free hosting with unlimited bandwidth
- ✅ Auto-HTTPS and global CDN
- ✅ Environment variables support

---

## Quick Deploy

```powershell
cd "c:\Users\rohit\Downloads\AI-Presentation-"
npx vercel deploy --prod --name ai-presentation-avatar
```

---

## Expected Output

```
? Set up and deploy "C:\Users\rohit\Downloads\AI-Presentation-"? [Y/n] y
? Which scope do you want to deploy to? RohitPanwar806
? Link to existing project? [y/N] n
? What's your project's name? ai-presentation-avatar
? In which directory is your code located? ./frontend/web
? Want to modify these settings? [y/N] n

✅ Production: https://ai-presentation-avatar.vercel.app
✅ Inspect: https://vercel.com/...
```

---

## Result

**Frontend URL:** `https://ai-presentation-avatar.vercel.app`  
**Backend URL:** `https://presentation-api-558900038680.asia-south1.run.app`

Both will be connected via CORS ✅

---

## Verify Deployment

Visit: https://ai-presentation-avatar.vercel.app

Check:
- [ ] Page loads in <1 second
- [ ] "Backend: Connected" shows green ✅
- [ ] /health endpoint responds
- [ ] / endpoint responds

---

Done! 🎉
