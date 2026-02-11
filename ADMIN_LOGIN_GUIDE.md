# 🏛️ KUMBH SMART SEVA v2 - ADMIN LOGIN GUIDE

## Quick Start with Admin Account

### Step 1: Start the Application
```bash
cd c:\Users\yshel\Downloads\kumbh_smart_seva_v2\kumbh_smart_seva_v2
python app.py
```

Open your browser: **http://localhost:5000**

---

## Admin Login Credentials

### **Admin Account** (Full Access)
```
Email:    admin@kumbh.com
Password: admin123
Role:     Admin (full system access)
```

### **Supervisor Account** (Limited Access)
```
Email:    supervisor@kumbh.com
Password: admin123
Role:     Supervisor (volunteer management)
```

### **Volunteer Accounts** (Read-Only)
```
Email:    volunteer1@kumbh.com
Password: admin123
Role:     Volunteer (read-only access)
```

---

## Step-by-Step Admin Login Process

### 1️⃣ Go to Admin Login Page
- On homepage, look for **"Admin Login"** button (top right corner)
- Or navigate directly to: `http://localhost:5000/admin/login`

### 2️⃣ Enter Credentials
- **Email**: `admin@kumbh.com`
- **Password**: `admin123`
- Click **"Login"**

### 3️⃣ You're In! 🎉
After successful login, you'll see the **Admin Dashboard** with:
- 📊 Dashboard Statistics
- 📍 Location Status
- 👥 Volunteer Management
- 📈 Analytics
- 📋 Reports
- 🎫 Certificate Management

---

## Admin Dashboard Features

### Dashboard (Home)
- View total visitors
- Active alerts
- Crowd status by location
- Certificate statistics

### Analytics (`/admin/analytics`)
- Crowd patterns by location
- Peak hours analysis
- Daily visitor statistics
- Crowd level distribution

### Volunteers (`/admin/volunteers`)
- List all volunteers
- Assign volunteers to locations
- View volunteer assignments
- Set shift timings

### Alerts (`/admin/alerts`)
- View active alerts
- Crowd density warnings
- Facility notifications
- Resolve alerts

### Reports (`/admin/reports`)
- Generate custom reports
- Date range filtering
- Location-wise statistics
- Visitor count analysis

---

## Troubleshooting

### Issue: "Invalid credentials"
✅ **Solution**: Make sure you've run sample data initialization
```bash
python init_sample_data.py
```

### Issue: Can't see admin login button
✅ **Solution**: Click dropdown menu (≡) at top-right corner

### Issue: After login, getting redirected to login page again
✅ **Solution**: Clear browser cookies and try again

### Issue: 404 Page Not Found on admin pages
✅ **Solution**: Make sure you're logged in as admin

---

## Regular User Login (for comparison)

### Regular User Account
```
Email:    rajesh@example.com
Password: password123
```

Features available:
- 🔐 Digital Locker (document storage)
- 👤 Lost Person Registry
- 🎫 Build certificates
- 🎭 Face matching

---

## Database Reset (if needed)

If you need to reset all data and start fresh:

```bash
# Delete the database
Remove-Item database/main.db -Force

# Reinitialize
python init_sample_data.py
```

New credentials will be:
- Admin Email: `admin@kumbh.com` / Password: `admin123`
- User Email: `rajesh@example.com` / Password: `password123`

---

## Important Notes

⚠️ **Security Warning**: These are TEST credentials only
- Change passwords before production use
- Don't expose credentials in public repositories
- Use environment variables for sensitive data

---

## Quick Command Reference

| Task | Command |
|------|---------|
| Start app | `python app.py` |
| Initialize data | `python init_sample_data.py` |
| Run tests | `python test_system.py` |
| Debug face matcher | `python debug_face_matcher.py` |

---

## Need Help?

1. Check the console output for error messages
2. Run `python test_system.py` to diagnose issues
3. Check database: `database/main.db` exists and has data
4. Ensure all dependencies installed: `pip install -r requirements.txt`

---

**Last Updated**: February 9, 2026
**Status**: ✅ All Systems Operational
