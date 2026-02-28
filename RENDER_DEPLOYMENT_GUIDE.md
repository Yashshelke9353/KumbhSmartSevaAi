# 🚀 Render Deployment Guide - Fix for Internal Server Error

## Problem
After deploying on Render, you get "Internal Server Error" when trying to access pages after the home page.

## Root Causes Fixed

### ✅ 1. **Database Not Initialized on Startup**
**Issue:** Database initialization (`db.init_db()`) was only called in the `if __name__ == '__main__'` block, which doesn't execute when running with Gunicorn on Render.

**Fixed:** Database initialization now happens at app startup, before any routes are defined.

### ✅ 2. **Hardcoded Secret Key**
**Issue:** Flask secret key was hardcoded, causing security issues and session problems.

**Fixed:** Secret key now uses environment variable with proper fallback.

### ✅ 3. **Missing Error Handlers**
**Issue:** 500 errors weren't being properly caught and displayed.

**Fixed:** Added custom error handlers for 500 and 404 errors.

### ✅ 4. **Module Initialization Errors Not Logged**
**Issue:** If any module failed to initialize, it would crash silently.

**Fixed:** All modules now have try-catch blocks with proper error logging.

---

## Deployment Steps on Render

### Step 1: Prepare Your Repository

1. Make sure all files are committed to Git:
```bash
git add .
git commit -m "Fix Render deployment issues"
git push
```

### Step 2: Set Environment Variables on Render

Go to your Render dashboard and add these environment variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `FLASK_ENV` | `production` | Running in production mode |
| `DATABASE_PATH` | `/tmp/main.db` | Temporary storage (see note below) |
| `SECRET_KEY` | *Your secret key* | Generate: `python -c "import os; print(os.urandom(24).hex())"` |
| `GEMINI_API_KEY` | *Optional* | If using translation feature |

### Step 3: Deploy on Render

1. Push your code to GitHub
2. Connect your GitHub repo to Render
3. Render will automatically use `render.yaml` for configuration
4. Deploy!

---

## ⚠️ Important: Database Persistence Issue

### Current Setup (Ephemeral Storage)
- Database path: `/tmp/main.db`
- Problem: **Data is lost every time the app restarts**
- Only good for: Testing/development

### Production Solution: Use PostgreSQL
1. Add a PostgreSQL database in Render dashboard
2. Get the database URL
3. Update your app to use PostgreSQL instead of SQLite

**To use PostgreSQL, you'll need to:**
1. Install PostgreSQL driver: `pip install psycopg2-binary`
2. Update `database/db_manager.py` to use PostgreSQL
3. Update connection string to use the DATABASE_URL from Render

---

## Testing After Deployment

### Step 1: Check Application Logs
Go to Render dashboard → Your service → Logs

**You should see:**
```
✓ Database initialized successfully
✓ DatabaseManager initialized
✓ DigitalLocker initialized
✓ LostPersonRegistry initialized
✓ FaceRecognitionMatcher initialized
✓ CertificateManager initialized
✓ AdminManager initialized
```

### Step 2: Test Basic Routes
- Home page: `https://yourapp.onrender.com/` ✅
- Register: `https://yourapp.onrender.com/register` ✅
- Login: `https://yourapp.onrender.com/login` ✅

### Step 3: If Still Getting 500 Error
1. Check the Render logs for the actual error message
2. Look for module initialization errors
3. Verify DATABASE_PATH environment variable is set
4. Ensure `requirements.txt` has all dependencies

---

## Common Issues and Fixes

### Issue: "ModuleNotFoundError" for OpenCV
**Why:** OpenCV needs system libraries on Render
**Fix:** The app has automatic fallback - it will work without OpenCV (using PIL instead)

### Issue: "Database is locked"
**Why:** Multiple processes trying to access database simultaneously
**Fix:** Upgrade to PostgreSQL for production use

### Issue: "File upload fails"
**Why:** `/tmp/` directory is ephemeral and gets cleaned up
**Fix:** Use a persistent cloud storage service (AWS S3, Google Cloud Storage)

### Issue: "Static files (CSS, JS) not loading"
**Cause:** Flask not serving static files in production
**Fix:** Gunicorn + proper static file configuration

---

## Files Changed

1. **app.py** - Database initialization moved to app startup
2. **render.yaml** - Updated environment variables and configuration
3. **templates/500.html** - Custom error page (NEW)
4. **templates/404.html** - Custom error page (NEW)
5. **modules installed** - Error handling for all module initialization

---

## Next Steps for Production

1. **Use PostgreSQL** instead of SQLite (highly recommended)
2. **Add file storage** (S3, Google Cloud Storage) for certificates and uploads
3. **Set up proper SECRET_KEY** in Render dashboard
4. **Configure HTTPS** (Render does this automatically)
5. **Monitor logs** regularly
6. **Set up alerting** for errors

---

## Still Having Issues?

Check the Render logs:
1. Go to Render dashboard
2. Click on your service
3. Go to "Logs" tab
4. Look for error messages
5. Search for the first "Error:" or "Exception:" message

Share that message, and I can help fix it!
