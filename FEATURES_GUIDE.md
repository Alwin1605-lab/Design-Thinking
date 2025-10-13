# 🚀 GramaFix - Advanced Features Implementation Guide

This guide provides step-by-step instructions for implementing the advanced features in GramaFix.

---

## ✅ Completed Features

### 1. Role-Based Authentication System
**Status**: ✅ **COMPLETED**

The authentication system now supports three user roles:
- **👤 Citizen**: Can report issues, vote on priorities, view issues
- **👮 Officer**: Citizen privileges + update issue status, manage local issues
- **⚙️ Admin**: Full access to all features and analytics

**Files Updated**:
- `Frontend/src/Register.jsx` - Comprehensive registration form with role selection
- `Frontend/src/Login.jsx` - Email-based login with role-based routing
- `Frontend/src/Profile.jsx` - User profile display with role badges
- `Backend/main.py` - Authentication endpoints (`/api/auth/register`, `/api/auth/login`, `/api/auth/profile`)
- `Backend/models.py` - Enhanced User model with email, password, ID proof fields

**Usage**:
1. Register at `/register` - Select role, provide details
2. Login at `/login` - Redirects based on role (admin/officer → dashboard, citizen → profile)
3. View profile at `/profile` - Shows user details with role-specific actions

---

## 📋 Pending Features - Setup Required

### 2. 📱 SMS Integration (Firebase Cloud Messaging)

**Purpose**: Send SMS notifications for issue updates, status changes, and important alerts.

#### Setup Steps:

1. **Create Firebase Project**:
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Click "Add Project" → Enter "GramaFix"
   - Disable Google Analytics (optional)
   - Create project

2. **Enable Cloud Messaging**:
   - In Firebase Console, go to Project Settings (gear icon)
   - Go to "Cloud Messaging" tab
   - Note the **Server Key** (you'll need this)

3. **Install Firebase Admin SDK**:
   ```bash
   cd Backend
   pip install firebase-admin
   ```

4. **Download Service Account Key**:
   - Firebase Console → Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Save as `Backend/firebase-credentials.json`

5. **Add to Backend Code**:
   
   Add to `Backend/main.py`:
   ```python
   import firebase_admin
   from firebase_admin import credentials, messaging
   
   # Initialize Firebase
   cred = credentials.Certificate("firebase-credentials.json")
   firebase_admin.initialize_app(cred)
   
   async def send_sms_notification(phone: str, message: str):
       """Send SMS via Firebase Cloud Messaging"""
       try:
           message = messaging.Message(
               notification=messaging.Notification(
                   title="GramaFix Update",
                   body=message,
               ),
               token=phone,  # FCM token, not phone number
           )
           response = messaging.send(message)
           return {"success": True, "message_id": response}
       except Exception as e:
           return {"success": False, "error": str(e)}
   ```

6. **Frontend Integration**:
   - Add Firebase SDK to `Frontend/package.json`
   - Request notification permissions
   - Store FCM token in user profile

**Note**: Firebase doesn't directly send SMS. For actual SMS:
- Use **Twilio** (recommended): https://www.twilio.com/
- Or **AWS SNS**: https://aws.amazon.com/sns/

---

### 3. 🗺️ Google Maps Integration

**Purpose**: Display issue locations on an interactive map, show nearby issues.

#### Setup Steps:

1. **Get Google Maps API Key**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project "GramaFix"
   - Enable APIs: "Maps JavaScript API", "Geocoding API", "Places API"
   - Credentials → Create API Key
   - **Important**: Restrict key to your domain/localhost

2. **Install React Google Maps**:
   ```bash
   cd Frontend
   npm install @react-google-maps/api
   ```

3. **Create Map Component** (`Frontend/src/IssuesMap.jsx`):
   ```jsx
   import React from 'react';
   import { GoogleMap, LoadScript, Marker, InfoWindow } from '@react-google-maps/api';
   
   const IssuesMap = ({ issues }) => {
     const [selected, setSelected] = React.useState(null);
     
     const mapStyles = {
       height: "500px",
       width: "100%"
     };
     
     const defaultCenter = {
       lat: 20.5937, // Center of India
       lng: 78.9629
     };
     
     return (
       <LoadScript googleMapsApiKey="YOUR_API_KEY_HERE">
         <GoogleMap
           mapContainerStyle={mapStyles}
           zoom={8}
           center={defaultCenter}
         >
           {issues.map((issue) => (
             <Marker
               key={issue._id}
               position={{
                 lat: issue.location.latitude,
                 lng: issue.location.longitude
               }}
               onClick={() => setSelected(issue)}
               icon={{
                 url: getCategoryIcon(issue.category),
                 scaledSize: new window.google.maps.Size(40, 40)
               }}
             />
           ))}
           
           {selected && (
             <InfoWindow
               position={{
                 lat: selected.location.latitude,
                 lng: selected.location.longitude
               }}
               onCloseClick={() => setSelected(null)}
             >
               <div>
                 <h3>{selected.category}</h3>
                 <p>{selected.description}</p>
                 <p>Status: {selected.status}</p>
               </div>
             </InfoWindow>
           )}
         </GoogleMap>
       </LoadScript>
     );
   };
   
   function getCategoryIcon(category) {
     const icons = {
       'Roads': '/icons/road.png',
       'Water': '/icons/water.png',
       'Electricity': '/icons/electricity.png',
       'School': '/icons/school.png',
       'Farming': '/icons/farming.png',
       'Sanitation': '/icons/sanitation.png',
     };
     return icons[category] || '/icons/default.png';
   }
   
   export default IssuesMap;
   ```

4. **Add Map to Routes**:
   - Update `Frontend/src/App.jsx`:
   ```jsx
   import IssuesMap from './IssuesMap';
   
   // Add route
   <Route path="/map" element={<IssuesMap />} />
   ```

5. **Add Map Link to Header**:
   ```jsx
   <Link to="/map" className="nav-link">🗺️ Map View</Link>
   ```

**Environment Variables**:
- Create `Frontend/.env`:
  ```
  VITE_GOOGLE_MAPS_API_KEY=your_actual_api_key_here
  ```
- Use in code: `import.meta.env.VITE_GOOGLE_MAPS_API_KEY`

---

### 4. 💾 IndexedDB for Offline Mode

**Purpose**: Allow users to report issues offline, sync when connection is restored.

#### Setup Steps:

1. **Install Dexie.js** (IndexedDB wrapper):
   ```bash
   cd Frontend
   npm install dexie
   ```

2. **Create Database** (`Frontend/src/db.js`):
   ```javascript
   import Dexie from 'dexie';
   
   const db = new Dexie('GramaFixDB');
   db.version(1).stores({
     issues: '++id, category, description, status, synced',
     drafts: '++id, timestamp',
     users: 'id, email, name'
   });
   
   export default db;
   ```

3. **Offline Issue Submission** (`Frontend/src/ReportIssue.jsx`):
   ```javascript
   import db from './db';
   
   const handleSubmit = async (e) => {
     e.preventDefault();
     
     if (!navigator.onLine) {
       // Save to IndexedDB
       await db.issues.add({
         ...formData,
         synced: false,
         timestamp: new Date()
       });
       alert('Saved offline! Will sync when online.');
       return;
     }
     
     // Normal API call
     // ... existing code
   };
   ```

4. **Background Sync** (`Frontend/src/syncService.js`):
   ```javascript
   import db from './db';
   
   export async function syncOfflineData() {
     const unsyncedIssues = await db.issues
       .where('synced')
       .equals(false)
       .toArray();
     
     for (const issue of unsyncedIssues) {
       try {
         const response = await fetch('http://localhost:8000/api/issues', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify(issue)
         });
         
         if (response.ok) {
           await db.issues.update(issue.id, { synced: true });
         }
       } catch (error) {
         console.error('Sync failed:', error);
       }
     }
   }
   
   // Run on connection restore
   window.addEventListener('online', syncOfflineData);
   ```

5. **Add Sync Indicator** in Header:
   ```jsx
   const [isOnline, setIsOnline] = useState(navigator.onLine);
   
   useEffect(() => {
     window.addEventListener('online', () => setIsOnline(true));
     window.addEventListener('offline', () => setIsOnline(false));
   }, []);
   
   // In render
   {!isOnline && <span className="offline-badge">📡 Offline Mode</span>}
   ```

---

### 5. 🌐 Multi-Language Support

**Purpose**: Support Hindi, Tamil, Telugu, and other regional languages.

#### Setup Steps:

1. **Install i18next**:
   ```bash
   cd Frontend
   npm install react-i18next i18next i18next-browser-languagedetector
   ```

2. **Create Translation Files**:
   
   `Frontend/src/locales/en.json`:
   ```json
   {
     "header": {
       "title": "GramaFix",
       "report": "Report Issue",
       "issues": "View Issues",
       "admin": "Admin Dashboard"
     },
     "home": {
       "hero_title": "Report Village Issues Instantly",
       "hero_subtitle": "Voice-enabled issue reporting for rural communities"
     },
     "categories": {
       "roads": "Roads",
       "water": "Water",
       "electricity": "Electricity",
       "school": "School",
       "farming": "Farming",
       "sanitation": "Sanitation"
     }
   }
   ```
   
   `Frontend/src/locales/hi.json` (Hindi):
   ```json
   {
     "header": {
       "title": "ग्रामफिक्स",
       "report": "समस्या दर्ज करें",
       "issues": "समस्याएं देखें",
       "admin": "प्रशासन डैशबोर्ड"
     },
     "home": {
       "hero_title": "गाँव की समस्याओं की तुरंत रिपोर्ट करें",
       "hero_subtitle": "ग्रामीण समुदायों के लिए आवाज-सक्षम समस्या रिपोर्टिंग"
     },
     "categories": {
       "roads": "सड़कें",
       "water": "पानी",
       "electricity": "बिजली",
       "school": "स्कूल",
       "farming": "खेती",
       "sanitation": "स्वच्छता"
     }
   }
   ```

3. **Configure i18next** (`Frontend/src/i18n.js`):
   ```javascript
   import i18n from 'i18next';
   import { initReactI18next } from 'react-i18next';
   import LanguageDetector from 'i18next-browser-languagedetector';
   
   import en from './locales/en.json';
   import hi from './locales/hi.json';
   
   i18n
     .use(LanguageDetector)
     .use(initReactI18next)
     .init({
       resources: {
         en: { translation: en },
         hi: { translation: hi }
       },
       fallbackLng: 'en',
       interpolation: {
         escapeValue: false
       }
     });
   
   export default i18n;
   ```

4. **Initialize in App** (`Frontend/src/main.jsx`):
   ```javascript
   import './i18n';
   ```

5. **Use in Components**:
   ```jsx
   import { useTranslation } from 'react-i18next';
   
   function Header() {
     const { t, i18n } = useTranslation();
     
     return (
       <header>
         <h1>{t('header.title')}</h1>
         <select onChange={(e) => i18n.changeLanguage(e.target.value)}>
           <option value="en">English</option>
           <option value="hi">हिंदी</option>
           <option value="ta">தமிழ்</option>
         </select>
       </header>
     );
   }
   ```

---

### 6. 📧 Email Notifications

**Purpose**: Send email notifications for issue status updates.

#### Setup Steps:

**Option A: Using SendGrid (Recommended)**

1. **Sign up**: https://sendgrid.com/ (Free 100 emails/day)
2. **Get API Key**: Settings → API Keys → Create API Key
3. **Install**:
   ```bash
   cd Backend
   pip install sendgrid
   ```

4. **Add to Backend** (`Backend/main.py`):
   ```python
   from sendgrid import SendGridAPIClient
   from sendgrid.helpers.mail import Mail
   
   SENDGRID_API_KEY = "YOUR_SENDGRID_API_KEY"
   
   async def send_email(to_email: str, subject: str, content: str):
       """Send email notification"""
       message = Mail(
           from_email='noreply@gramafix.com',
           to_emails=to_email,
           subject=subject,
           html_content=content
       )
       
       try:
           sg = SendGridAPIClient(SENDGRID_API_KEY)
           response = sg.send(message)
           return {"success": True, "status": response.status_code}
       except Exception as e:
           return {"success": False, "error": str(e)}
   
   # Call when status changes
   @app.put("/api/issues/{issue_id}/status")
   async def update_issue_status(issue_id: str, update: StatusUpdate):
       # ... existing code
       
       # Send email
       issue = await issues_collection.find_one({"_id": ObjectId(issue_id)})
       if issue:
           await send_email(
               to_email=issue['reporter_email'],
               subject=f"Issue Update - {issue['category']}",
               content=f"<h2>Status Updated</h2><p>Your issue has been updated to: <b>{update.status}</b></p>"
           )
   ```

**Option B: Using Gmail SMTP**

1. **Enable 2-Factor Authentication** in Gmail
2. **Generate App Password**: Google Account → Security → App Passwords
3. **Install**:
   ```bash
   pip install python-dotenv aiosmtplib email-validator
   ```

4. **Add to Backend**:
   ```python
   import aiosmtplib
   from email.mime.text import MIMEText
   from email.mime.multipart import MIMEMultipart
   
   async def send_email_gmail(to_email: str, subject: str, body: str):
       message = MIMEMultipart()
       message["From"] = "your-email@gmail.com"
       message["To"] = to_email
       message["Subject"] = subject
       message.attach(MIMEText(body, "html"))
       
       await aiosmtplib.send(
           message,
           hostname="smtp.gmail.com",
           port=587,
           start_tls=True,
           username="your-email@gmail.com",
           password="your-app-password"
       )
   ```

---

## 🔐 Environment Variables Setup

Create `.env` files for security:

**Frontend/.env**:
```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_MAPS_API_KEY=your_google_maps_key
```

**Backend/.env**:
```env
MONGODB_URI=mongodb://localhost:27017/GramaFix
SENDGRID_API_KEY=your_sendgrid_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
JWT_SECRET=your_random_secret_key
```

Install python-dotenv:
```bash
pip install python-dotenv
```

Load in Backend/main.py:
```python
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")
```

---

## 📦 Complete Package Installation

Run these commands to install all dependencies:

**Backend**:
```bash
cd Backend
pip install firebase-admin sendgrid python-dotenv aiosmtplib email-validator twilio
```

**Frontend**:
```bash
cd Frontend
npm install @react-google-maps/api dexie react-i18next i18next i18next-browser-languagedetector
```

---

## 🚀 Next Steps

1. **Complete SMS Setup**: Choose Twilio or Firebase and follow setup steps
2. **Get Google Maps API Key**: Enable Maps APIs and add to frontend
3. **Implement Offline Mode**: Add IndexedDB for offline functionality
4. **Add Multi-Language**: Create translation files for regional languages
5. **Setup Email**: Configure SendGrid or Gmail SMTP for notifications

For any issues or questions, refer to the documentation or raise an issue in the project repository.

---

## 📞 API Services Pricing

- **Twilio SMS**: $0.0079/SMS (Free trial: $15 credit)
- **SendGrid Email**: Free up to 100 emails/day
- **Google Maps**: $7/1000 requests (Free: $200 credit monthly)
- **Firebase**: Free up to 10K messages/month

---

**Happy Coding! 🎉**
