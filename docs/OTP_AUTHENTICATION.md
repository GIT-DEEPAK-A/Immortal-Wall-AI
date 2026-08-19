# Immortal Wall AI - OTP Authentication System

## Overview

This document describes the complete OTP (One-Time Password) based email authentication system implemented for Immortal Wall AI, a cybersecurity threat detection and response platform.

The system provides secure two-factor authentication (2FA) using email-based OTP tokens, ensuring only authorized users can access the platform.

---

## Architecture

### Components

1. **Authentication Backend (FastAPI)**
   - User credential validation
   - OTP generation and storage
   - OTP verification
   - Email delivery

2. **Database Layer (SQLAlchemy + SQLite)**
   - User management
   - OTP entry tracking
   - Audit logging

3. **Email Service (SMTP)**
   - OTP delivery via Gmail
   - Secure app password authentication

4. **Frontend (HTML/CSS/JavaScript)**
   - Login interface
   - OTP input screen
   - Success confirmation page

---

## Setup Instructions

### 1. Environment Configuration

**Create a `.env` file** in the project root:

```bash
cp .env.example .env
```

**Edit `.env` with your Gmail credentials:**

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_SENDER=deepakananthan4@gmail.com
SMTP_APP_PASSWORD=your_16_character_app_password

OTP_TTL_MINUTES=10
OTP_MAX_ATTEMPTS=3
```

### 2. Gmail App Password Setup

Since Gmail doesn't allow direct password usage for third-party apps, you need to generate an **App Password**:

#### Steps:
1. Go to https://myaccount.google.com/
2. Click **Security** in the left sidebar
3. Enable **2-Step Verification** (if not already enabled)
4. In Security settings, find **App passwords**
5. Select **Mail** and **Windows Computer** (or your platform)
6. Google will generate a 16-character password
7. Copy this password to `SMTP_APP_PASSWORD` in `.env`

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Initialization

The database automatically initializes on first run with demo users:

- **Admin Account**
  - Email: `deepakananthan4@gmail.com`
  - Password: `password`
  - Role: Admin

- **Analyst Account**
  - Email: `analyst@immortalwall.ai`
  - Password: `password`
  - Role: Analyst

### 5. Start the Backend

```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

---

## User Flow

### Step 1: Login Page
```
URL: http://localhost:8000/auth/login
```

**User Input:**
- Email address
- Password

**Actions:**
- Validate credentials against database
- On success: Generate 6-digit OTP
- Send OTP to registered email
- Display OTP input screen

### Step 2: OTP Verification Page
```
URL: http://localhost:8000/auth/otp
```

**OTP Features:**
- Countdown timer (default: 10 minutes)
- Max 3 incorrect attempts
- Auto-expiration after timer ends
- Resend button (max 3 resends)
- Invalid OTP rejection

**User Input:**
- 6-digit OTP from email

**Actions:**
- Verify OTP matches and is not expired
- Check attempt count
- On success: Create session
- Redirect to success page

### Step 3: Success Page
```
URL: http://localhost:8000/auth/success
```

**Displays:**
- User email
- User role
- Authentication confirmation
- Link to dashboard

---

## API Endpoints

### 1. POST `/api/auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (Success - 200):**
```json
{
  "message": "OTP sent to your email",
  "email": "user@example.com"
}
```

**Response (Error - 401):**
```json
{
  "detail": "Invalid email or password"
}
```

### 2. POST `/api/auth/send-otp`

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response (Success - 200):**
```json
{
  "message": "New OTP sent to your email",
  "email": "user@example.com"
}
```

### 3. POST `/api/auth/verify-otp`

**Request:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

**Response (Success - 200):**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "Admin",
    "created_at": "2026-01-15T10:30:00"
  }
}
```

**Response (Error - 400):**
```json
{
  "detail": "Invalid or expired OTP"
}
```

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(128) NOT NULL,
  salt VARCHAR(64) NOT NULL,
  role VARCHAR(20) DEFAULT 'Analyst',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### OTP Entries Table

```sql
CREATE TABLE otps (
  id INTEGER PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  otp_hash VARCHAR(128) NOT NULL,
  expiry_time DATETIME NOT NULL,
  attempts INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Security Features

### 1. Password Security
- **PBKDF2-HMAC-SHA256** hashing with salt
- 100,000 iterations for key derivation
- Unique salt per user

### 2. OTP Security
- **6-digit numeric** OTP (1 million combinations)
- **SHA-256 hashing** for storage (OTP never stored in plain text)
- **2-10 minute expiry** (configurable)
- **Max 3 attempts** before OTP invalidation
- **Automatic cleanup** of expired OTPs

### 3. Email Security
- **Gmail SMTP with TLS/SSL** (port 465)
- **App Password** instead of account password
- No passwords logged or transmitted in plain text

### 4. Session Security
- Session data stored in browser sessionStorage (not persistent)
- Auto-cleared on logout
- CORS enabled for trusted origins only

### 5. Rate Limiting
- OTP resend limited to 3 attempts
- Failed login attempts tracked
- Failed OTP attempts limited to 3

---

## Configuration Options

### OTP Settings

| Setting | Default | Env Variable | Description |
|---------|---------|-------------|-------------|
| TTL | 10 min | `OTP_TTL_MINUTES` | OTP validity duration |
| Max Attempts | 3 | `OTP_MAX_ATTEMPTS` | Max wrong OTP entries |
| Max Resends | 3 | - | Max resend requests |

### Email Settings

| Setting | Default | Env Variable |
|---------|---------|-------------|
| SMTP Host | smtp.gmail.com | `SMTP_HOST` |
| SMTP Port | 465 | `SMTP_PORT` |
| Sender | deepakananthan4@gmail.com | `SMTP_SENDER` |
| App Password | - | `SMTP_APP_PASSWORD` |

---

## Troubleshooting

### Issue: "Failed to send OTP"

**Cause:** Gmail App Password not configured

**Solution:**
1. Generate Gmail App Password (see Setup Step 2)
2. Update `SMTP_APP_PASSWORD` in `.env`
3. Restart backend server

### Issue: "SMTP Connection Error"

**Cause:** Wrong SMTP credentials or network issue

**Solution:**
1. Verify Gmail credentials
2. Check firewall rules for port 465
3. Ensure App Password is correct (not account password)

### Issue: "Invalid email or password"

**Cause:** Wrong credentials or user doesn't exist

**Solution:**
1. Use demo credentials from database initialization
2. Check email spelling
3. Verify password is correct

### Issue: "OTP Expired"

**Cause:** Timer reached zero before OTP verification

**Solution:**
1. Click "Resend OTP" button
2. Increase `OTP_TTL_MINUTES` if needed
3. User can try again with new OTP

---

## Testing

### Manual Testing Workflow

1. **Navigate to login page:**
   ```
   http://localhost:8000/auth/login
   ```

2. **Enter demo credentials:**
   - Email: `deepakananthan4@gmail.com`
   - Password: `password`

3. **Check email for OTP:**
   - Check inbox (may take 5-10 seconds)
   - Look for subject: "Immortal Wall AI - Secure Login OTP"

4. **Enter OTP:**
   - Copy 6-digit code from email
   - Paste into OTP input field
   - Submit within 10 minutes

5. **Verify success page:**
   - Should display user email and role
   - Session info stored in browser

### Automated Testing

Run the test suite:

```bash
pytest tests/test_auth.py -v
```

---

## Production Deployment

### Security Checklist

- [ ] Change all default credentials
- [ ] Update `SESSION_SECRET_KEY` and `SECRET_KEY`
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set `DEBUG=False` in production
- [ ] Update CORS origins to your domain
- [ ] Enable database encryption
- [ ] Set up log rotation
- [ ] Configure backup strategy
- [ ] Monitor failed login attempts

### Environment Variables for Production

```env
DEBUG=False
FLASK_ENV=production
HOST=0.0.0.0
PORT=8000
SECRET_KEY=your_long_random_secret_key
SESSION_SECRET_KEY=another_long_random_secret
CORS_ORIGINS=https://yourdomain.com
SMTP_SENDER=notifications@yourdomain.com
SMTP_APP_PASSWORD=your_app_password
OTP_TTL_MINUTES=5
```

### Deployment Platforms

#### Using Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 backend.app:app
```

#### Using Docker:
```bash
docker build -t immortal-wall-ai .
docker run -p 8000:8000 --env-file .env immortal-wall-ai
```

---

## API Integration Example

### JavaScript/Frontend Integration

```javascript
// Login
const loginResponse = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

// Verify OTP
const otpResponse = await fetch('/api/auth/verify-otp', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    otp: '123456'
  })
});

const userData = await otpResponse.json();
// Use userData.user for authenticated requests
```

### Python Integration

```python
import requests

# Login
response = requests.post('http://localhost:8000/api/auth/login', json={
    'email': 'user@example.com',
    'password': 'password123'
})

# Verify OTP
response = requests.post('http://localhost:8000/api/auth/verify-otp', json={
    'email': 'user@example.com',
    'otp': '123456'
})
```

---

## Support & Documentation

- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8000/redoc (ReDoc)
- **Health Check:** http://localhost:8000/api/health
- **System Status:** http://localhost:8000/api/system-status

---

## License

This authentication system is part of the Immortal Wall AI project and follows the same license terms.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-01 | Initial OTP authentication system implementation |

---

## Contributors

- Deepak Ananthan (deepakananthan4@gmail.com)
- Immortal Wall AI Team

---

**Last Updated:** May 1, 2026
