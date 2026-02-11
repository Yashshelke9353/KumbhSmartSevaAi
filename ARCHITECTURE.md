# Kumbh Smart Seva v2.0 - Architecture Overview

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Public Web UI          Admin Dashboard       Volunteer App      │
│  ├─ Home               ├─ Dashboard           ├─ Login          │
│  ├─ Certificate        ├─ Analytics           ├─ Assignment     │
│  ├─ Verify             ├─ Volunteers          ├─ Crowd Status   │
│  ├─ Lost & Found       ├─ Alerts              └─ Reports        │
│  └─ Register/Login     └─ Reports                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER (Flask)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Routes & Controllers (app.py)                                   │
│  ├─ User Routes (register, login, dashboard)                    │
│  ├─ Certificate Routes (generate, verify, view)                 │
│  ├─ Admin Routes (dashboard, analytics, management)             │
│  ├─ API Endpoints (REST for AJAX calls)                         │
│  └─ Authentication & Decorators                                 │
│                                                                   │
│  Business Logic (modules/)                                       │
│  ├─ CertificateManager - Certificate operations                 │
│  ├─ AdminManager - Admin operations & crowd management          │
│  ├─ Auth - Authentication & JWT                                 │
│  ├─ DigitalLocker - Document storage                            │
│  ├─ LostPersonRegistry - Missing person tracking                │
│  └─ FaceRecognitionMatcher - AI matching                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DATA ACCESS LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  DatabaseManager (database/db_manager.py)                        │
│  ├─ Connection pooling                                          │
│  ├─ Query execution                                             │
│  ├─ Transaction management                                      │
│  └─ Schema initialization                                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  SQLite (Development)        PostgreSQL (Production)             │
│  ├─ database/main.db         ├─ kumbh_seva DB                  │
│  └─ 10 tables                └─ SSL/Auth support                │
│                                                                   │
│  Tables:                                                         │
│  ├─ users, admin_users      (Authentication)                   │
│  ├─ locations               (Sacred sites)                      │
│  ├─ visitor_certificates    (Digital certs)                    │
│  ├─ crowd_data              (Monitoring)                       │
│  ├─ alerts, volunteer_assignments  (Management)                │
│  └─ locker_items, lost_persons, found_persons  (Features)     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Diagram

```
┌─────────────┐
│   Visitor   │
└──────┬──────┘
       │
       │ Registration/Certificate
       ↓
┌──────────────────────────┐
│  Certificate System      │
│  ├─ Generate certificate │
│  ├─ Generate QR code     │
│  └─ Verify identity      │
└──────────┬───────────────┘
           │
           ↓ Store
    ┌──────────────────────┐
    │ Database             │
    │ (visitor_certificates,
    │  users, locations)   │
    └──────┬───────────────┘
           │
           ├─ Read ──→ Admin Dashboard
           │          ├─ Statistics
           │          ├─ Charts
           │          └─ Reports
           │
           ├─ Read ──→ Crowd Monitoring
           │          ├─ Real-time data
           │          ├─ Alerts
           │          └─ Trends
           │
           └─ Read ──→ Analytics Engine
                      ├─ Daily reports
                      ├─ Peak hours
                      └─ Predictions
```

## 🎯 Feature Module Architecture

```
Certificate Generation
├─ Form Validation
├─ File Upload (Photo)
├─ QR Code Generation
├─ Database Storage
├─ Duplicate Detection
└─ PDF Export

Admin Dashboard
├─ Statistics Calculation
├─ Real-time Updates
├─ Alert Management
├─ Chart Rendering
└─ Performance Metrics

Analytics System
├─ Daily Statistics
├─ Peak Hour Analysis
├─ Crowd Level Distribution
├─ Location Comparison
└─ Report Generation

Volunteer Management
├─ User Registration
├─ Role Assignment
├─ Shift Scheduling
├─ Location Assignment
└─ Activity Tracking

Crowd Management
├─ Real-time Monitoring
├─ Capacity Calculation
├─ Alert Generation
├─ Level Classification
└─ Trend Analysis

Alert System
├─ Alert Creation
├─ Severity Classification
├─ Notification Dispatch
├─ Resolution Tracking
└─ History Maintenance
```

## 📊 User Roles & Permissions

```
PUBLIC USER                VISITOR USER             ADMIN
├─ View Home              ├─ All public features   ├─ All features
├─ Generate Cert          ├─ Digital Locker        ├─ Full Dashboard
├─ Verify Cert            ├─ Lost & Found          ├─ Analytics
├─ View About             ├─ Reports              ├─ User Management
└─ Contact                └─ Dashboard            └─ Settings

SUPERVISOR                 VOLUNTEER
├─ Volunteer Management    ├─ Crowd Monitoring
├─ Assignments             ├─ Status Updates
├─ Location Reports        ├─ Basic Reports
├─ Analytics              └─ Shift Details
└─ Alert Management
```

## 🔐 Security Architecture

```
Request ──→ HTTPS/SSL ──→ Firewall ──→ Web Server (Nginx) ──→ WSGI Server (Gunicorn)
                                                                      │
                                                                      ↓
                                                          ┌──────────────────────┐
                                                          │ Flask Application    │
                                                          ├─ Input Validation    │
                                                          ├─ Session Management  │
                                                          ├─ CSRF Protection     │
                                                          ├─ Rate Limiting       │
                                                          └─ Error Handling      │
                                                                      │
                                                                      ↓
                                                          ┌──────────────────────┐
                                                          │ Database Connection  │
                                                          ├─ Parameterized Query │
                                                          ├─ Prepared Statements │
                                                          ├─ Password Hashing    │
                                                          └─ Transaction Control │
                                                                      │
                                                                      ↓
                                                          ┌──────────────────────┐
                                                          │ File System          │
                                                          ├─ Secure Filenames    │
                                                          ├─ Type Validation     │
                                                          ├─ Size Limits         │
                                                          └─ Virus Scanning      │
```

## 🚀 Deployment Architecture

```
Development                 Staging                 Production
┌──────────────┐           ┌──────────────┐        ┌──────────────┐
│ Local PC     │           │ Test Server  │        │ Production   │
├──────────────┤           ├──────────────┤        ├──────────────┤
│ Python 3.9   │           │ Python 3.9   │        │ Python 3.9   │
│ Flask (dev)  │           │ Gunicorn     │        │ Gunicorn (4) │
│ SQLite       │           │ PostgreSQL   │        │ PostgreSQL   │
│ Hot reload   │           │ Nginx        │        │ Nginx        │
│ Debug mode   │           │ SSL (self)   │        │ SSL (LE)     │
└──────────────┘           └──────────────┘        └──────────────┘
       │                          │                       │
       ↓                          ↓                       ↓
  Git webhook          Docker registry            Docker registry
       │                          │                       │
       ↓                          ↓                       ↓
  Auto deploy         Staging tests              Production deploy
  (Hot reload)        Load testing               Backup + Monitor
```

## 📈 Technology Stack Layers

```
┌─────────────────────────────────────────────────────┐
│ PRESENTATION LAYER                                  │
│ Bootstrap 5.3 | Chart.js | Font Awesome | HTML5    │
│ Vanilla JavaScript | CSS3 | Responsive Design      │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ WEB FRAMEWORK LAYER                                 │
│ Flask 3.0.0 | Werkzeug 3.0.1 | Jinja2              │
│ Session Management | Route Handling | Template Rendering │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ APPLICATION LOGIC LAYER                             │
│ Python 3.9 | Custom Modules | Business Logic       │
│ Certificate Generation | Crowd Analysis | Auth      │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ DATA PERSISTENCE LAYER                              │
│ SQLAlchemy | SQLite / PostgreSQL | SQL Queries      │
│ Transaction Management | Query Optimization         │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ SUPPORTING LIBRARIES                                │
│ PyJWT | QRCode | Pillow | OpenCV | NumPy            │
│ python-dotenv | reportlab | redis (optional)       │
└─────────────────────────────────────────────────────┘
```

## 🔗 API Flow

```
CLIENT REQUEST
      │
      ↓
┌─────────────────────────────────────┐
│ Route Handler                        │
├─────────────────────────────────────┤
│ 1. Check Authentication              │
│ 2. Validate Input                    │
│ 3. Convert to Proper Format          │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│ Business Logic                       │
├─────────────────────────────────────┤
│ CertificateManager                  │
│ AdminManager                        │
│ Custom Logic                        │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│ Data Access                          │
├─────────────────────────────────────┤
│ DatabaseManager.query()              │
│ Parameterized SQL                    │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│ Database                             │
├─────────────────────────────────────┤
│ Execute Query                        │
│ Return Results                       │
└─────────────┬───────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│ Response Formatter                   │
├─────────────────────────────────────┤
│ JSON / Template Rendering            │
│ Error Handling                       │
└─────────────┬───────────────────────┘
              │
              ↓
          CLIENT
```

## 📦 Folder Structure & Dependencies

```
kumbh_smart_seva_v2/
│
├── app.py
│   └── Imports: Flask, modules.*, database.*
│
├── database/
│   └── db_manager.py
│       └── Uses: sqlite3, os
│
├── modules/
│   ├── certificate_manager.py    → qrcode, uuid, PIL
│   ├── admin_manager.py          → sqlite3
│   ├── auth.py                   → jwt, functools
│   ├── locker.py                 → existing
│   ├── lost_person.py            → existing
│   └── face_recognition_matcher.py → cv2, numpy
│
├── templates/
│   ├── base.html                 → Bootstrap, Font Awesome
│   ├── *.html                    → Jinja2 templating
│   └── CSS/JS embedded
│
├── static/
│   ├── css/                      → Bootstrap, Custom CSS
│   ├── js/                       → Chart.js, Vanilla JS
│   └── uploads/                  → Images, QR codes, PDFs
│
└── Configuration Files
    ├── requirements.txt
    ├── start.sh
    ├── init_sample_data.py
    └── Documentation
```

## 🎯 Development Workflow

```
1. LOCAL DEVELOPMENT
   ↓
2. UNIT TESTING (Python)
   ↓
3. INTEGRATION TESTING
   ↓
4. LOAD TESTING (optional)
   ↓
5. SECURITY AUDIT
   ↓
6. CODE REVIEW
   ↓
7. STAGING DEPLOYMENT
   ↓
8. USER ACCEPTANCE TESTING
   ↓
9. PRODUCTION DEPLOYMENT
   ↓
10. MONITORING & MAINTENANCE
```

---

**Visual Reference**: Kumbh Smart Seva v2.0 Complete Architecture  
**Last Updated**: February 2026  
**Status**: ✅ Production Ready
