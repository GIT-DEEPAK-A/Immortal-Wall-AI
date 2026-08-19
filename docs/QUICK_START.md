# Quick Start Guide - OTP Authentication System

## 5-Minute Setup

### 1. Configure Gmail App Password

1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification** (if needed)
3. Go to **App passwords**
4. Select **Mail** and **Windows Computer**
5. Copy the 16-character password

### 2. Create .env File

```bash
# In project root directory
cp .env.example .env
```

Edit `.env`:
```env
SMTP_APP_PASSWORD=your_16_char_app_password_here
```

### 3. Install & Run

```bash
# Install dependencies
pip install -r requirements.txt

# Start the backend
uvicorn backend.app:app --reload
```

### 4. Test Authentication

Open in browser:
```
http://localhost:8000/auth/login
```

**Demo Credentials:**
- Email: `deepakananthan4@gmail.com`
- Password: `password`

---

## What Happens During Authentication

1. **Login Page**: Enter email & password
2. **Backend**: Validates credentials → Generates OTP → Sends email
3. **OTP Page**: Enter 6-digit code from email (10-minute timer)
4. **Backend**: Verifies OTP → Creates session
5. **Success Page**: Authentication complete!

---

## File Structure

```
backend/
├── templates/auth/
│   ├── login.html          # Login page
│   ├── otp.html            # OTP verification page
│   └── success.html        # Success confirmation page
├── static/css/
│   └── auth.css            # Authentication styling
├── routes/
│   └── auth_routes.py      # API endpoints
├── services/
│   └── auth_service.py     # OTP logic
├── database/
│   ├── models.py           # Database models
│   └── db.py               # Database manager
├── app.py                  # FastAPI application
└── config.py               # Configuration

docs/
└── OTP_AUTHENTICATION.md   # Full documentation

.env.example                # Environment template
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/auth/login` | Login page |
| GET | `/auth/otp` | OTP input page |
| GET | `/auth/success` | Success page |
| POST | `/api/auth/login` | Validate credentials |
| POST | `/api/auth/send-otp` | Resend OTP |
| POST | `/api/auth/verify-otp` | Verify OTP |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Email not received | Check `SMTP_APP_PASSWORD` in `.env` |
| OTP expired | Click "Resend OTP" button |
| Wrong credentials | Use demo email/password |
| Port 8000 in use | Change port: `--port 8001` |

---

## Next Steps

1. **Customize** the login page styling in `backend/static/css/auth.css`
2. **Add users** by creating user accounts in database
3. **Configure** email templates in `backend/services/auth_service.py`
4. **Deploy** to production (see OTP_AUTHENTICATION.md)

---

## Support

For detailed documentation, see: `docs/OTP_AUTHENTICATION.md`

For API documentation: http://localhost:8000/docs
