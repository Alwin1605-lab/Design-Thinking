# 🚀 GramaFix Quick Start Guide

Get GramaFix up and running in 5 minutes!

---

## ✅ Prerequisites

- **Python 3.9+** installed
- **Node.js 16+** and npm installed
- **MongoDB** running locally (on port 27017)
- **Groq API Key** (free from https://console.groq.com/)

---

## 📦 Installation Steps

### 1. Clone/Download the Project
```bash
cd "D:\Design Thinking"
```

### 2. Backend Setup

```bash
# Navigate to Backend folder
cd Backend

# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1  # On Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Edit Backend/.env file and add your Groq API key:
# GROQ_API_KEY=gsk_your_key_here
```

### 3. Frontend Setup

```bash
# Navigate to Frontend folder
cd ..\Frontend

# Install dependencies
npm install

# No additional configuration needed!
```

### 4. Start MongoDB

Make sure MongoDB is running:
```bash
mongod --dbpath="C:\data\db"
```

---

## 🎬 Running the Application

### Start Backend (Terminal 1)
```bash
cd "D:\Design Thinking\Backend"
uvicorn main:app --reload
```

**Backend will be available at:** http://localhost:8000

### Start Frontend (Terminal 2)
```bash
cd "D:\Design Thinking\Frontend"
npm run dev
```

**Frontend will be available at:** http://localhost:5173

---

## 🐳 Deploy with Docker (One Command)

If you prefer containers, use the included docker-compose setup:

1) Prepare env files

- Backend: copy `.env.example` to `Backend/.env` and fill values (Mongo URI not required; compose sets it)
- Frontend: copy `.env.example` to `Frontend/.env` and fill at least:
   - `VITE_GOOGLE_MAPS_API_KEY`
   - No Firebase configuration is needed (Firebase has been removed)

2) Run

```powershell
cd d:\DT\Design-Thinking
docker compose up --build -d
```

Services:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- MongoDB: mongodb://localhost:27017

Stop:

```powershell
docker compose down
```

---

## 🎯 First Time Setup

### 1. Register a User
1. Open http://localhost:5173/register
2. Fill in the registration form:
   - **Name**: Your full name
   - **Phone**: 10-digit mobile number
   - **Email**: Your email address
   - **Password**: Choose a secure password
   - **Role**: Select from:
     - 👤 **Citizen** - Can report and vote on issues
     - 👮 **Officer** - Citizen + update issue status
     - ⚙️ **Admin** - Full access to all features
   - **Gram Panchayat**: Your village/panchayat name
   - **Address**: Your full address (optional)
   - **ID Proof**: Select type and enter number (optional)
3. Click "Register"
4. You'll be redirected to the login page

### 2. Login
1. Go to http://localhost:5173/login
2. Enter your **email** and **password**
3. Click "Login"
4. You'll be redirected to:
   - **Profile page** (for Citizens)
   - **Admin Dashboard** (for Officers/Admins)

### 3. Setup Groq API (for Voice Transcription)

1. **Get API Key**:
   - Go to https://console.groq.com/
   - Sign up for free account
   - Navigate to API Keys section
   - Create new API key
   - Copy the key

2. **Add to .env file**:
   ```env
   GROQ_API_KEY=gsk_your_actual_key_here
   ```

3. **Restart Backend**:
   ```bash
   # Press Ctrl+C to stop, then:
   uvicorn main:app --reload
   ```

---

## 🔐 Enable Authenticator (TOTP)

1. Login and go to your Profile page
2. Click "Enable Authenticator"
3. Scan the QR in Google Authenticator or Authy
4. Enter the 6-digit code to verify and enable TOTP
5. From the Login page, you can now login using the "Authenticator (TOTP)" tab

Backend environment options (optional, already sane defaults):

```
TOTP_ISSUER=GramaFix
TOTP_INTERVAL=30
TOTP_DIGITS=6
TOTP_VALID_WINDOW=1
TOTP_ENCRYPTION_KEY=<set a stable Fernet key for persistence>
```

To generate a Fernet key for TOTP_ENCRYPTION_KEY:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

---

## 🤖 Chatbot (Groq LLM)

If `GROQ_API_KEY` is set in Backend/.env, the Chatbot widget uses Groq to answer questions. Without a key, it replies with simple built-in messages.

---

## 🎤 Testing Voice Transcription

1. Go to http://localhost:5173/report
2. Select a category (e.g., Roads)
3. Click "🎤 Start Recording"
4. Allow microphone access when prompted
5. Speak clearly: "The road near the village temple has a big pothole and needs immediate repair"
6. Click "🔴 Stop Recording"
7. Wait 2-3 seconds for transcription
8. The transcribed text will appear in the description field
9. Fill in remaining fields and submit!

---

## 📱 Key Features to Test

### ✅ Report an Issue
- Navigate to "Report Issue"
- Try voice input for description
- Add photos
- Location is auto-captured
- Submit and view in "View Issues"

### ✅ Vote on Issues
- Go to "View Issues"
- Find an issue
- Click "Vote for Priority"
- See vote count increase

### ✅ Admin Dashboard (Officer/Admin only)
- Login as Officer or Admin
- Access "Dashboard" from header
- View analytics and statistics
- Update issue status
- Add remarks

### ✅ User Profile
- Click your name in header
- View your profile details
- See role badge
- Access quick actions

---

## 🔔 Push Notifications

Firebase/FCM has been removed per project direction. If you need SMS updates to reporters, you can optionally enable Twilio in Backend/.env:

```
ENABLE_TWILIO_SMS=true
ENABLE_TWILIO_OTP=false
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=...
```
Leave these unset or `false` to disable SMS entirely.

---

## 🐛 Troubleshooting

### Backend won't start
**Error**: `ModuleNotFoundError: No module named 'groq'`
**Solution**: 
```bash
pip install groq
```

**Error**: `ModuleNotFoundError: No module named 'dotenv'`
**Solution**:
```bash
pip install python-dotenv
```

**Error**: `Could not connect to MongoDB`
**Solution**: Make sure MongoDB is running:
```bash
mongod --dbpath="C:\data\db"
```

### Frontend won't start
**Error**: `Cannot find module 'react'`
**Solution**:
```bash
cd Frontend
npm install
```

### Voice transcription not working
**Issue**: "Groq API key not configured"
**Solution**: 
1. Check Backend/.env file exists
2. Verify GROQ_API_KEY is set
3. Restart backend

**Issue**: "Failed to access microphone"
**Solution**:
1. Check browser permissions (Chrome/Edge recommended)
2. Use HTTPS or localhost
3. Allow microphone in browser settings

### MongoDB connection errors
**Issue**: Connection refused
**Solution**:
```bash
# Create data directory
mkdir C:\data\db

# Start MongoDB
mongod --dbpath="C:\data\db"
```

---

## 📚 Documentation

- **Main README**: `README.md`
- **Features Guide**: `FEATURES_GUIDE.md` - Setup for SMS, Maps, Offline mode, etc.
- **Groq Whisper Setup**: `GROQ_WHISPER_SETUP.md` - Detailed voice setup guide

---

## 🎉 You're All Set!

The application is now ready to use! Here's what you can do:

1. **Register multiple users** with different roles
2. **Report issues** as a Citizen
3. **Update status** as an Officer
4. **View analytics** as an Admin
5. **Test voice input** with Groq Whisper
6. **Vote on issues** to prioritize them

---

## 🆘 Need Help?

- Check the documentation files
- Review error messages in terminal
- Verify all services are running (MongoDB, Backend, Frontend)
- Check browser console for frontend errors

---

## 🔒 Default Ports

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **MongoDB**: mongodb://localhost:27017

---

**Happy Building! 🌾✨**
