from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Depends, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import re
from datetime import datetime, timedelta
import secrets
import string
from typing import List, Optional
from models import Issue, User, StatusUpdate, Category
import json
try:
    from dotenv import load_dotenv
except Exception:  # python-dotenv not installed
    def load_dotenv(*args, **kwargs):
        return None
from jose import jwt, JWTError
from passlib.context import CryptContext

# Load environment variables from .env file
load_dotenv()

# Import notifications after env is loaded so it can read configuration
# n8n notifications removed; no external notification hooks

# ---- App Setup ----
app = FastAPI(title="GramaFix API", version="1.0.0")

# CORS: use explicit origins when credentials are enabled
cors_origins_env = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
)
allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- MongoDB ----
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/GramaFix")
MONGO_DB_NAME = os.getenv("MONGODB_DB_NAME")
client = AsyncIOMotorClient(MONGO_URI)
# If URI includes DB, use it; else default to GramaFix; allow env override
if MONGO_DB_NAME:
    db_name = MONGO_DB_NAME
else:
    try:
        tail = MONGO_URI.rsplit("/", 1)[-1]
        db_name = (tail.split("?", 1)[0] or "GramaFix") if "/" in MONGO_URI else "GramaFix"
    except Exception:
        db_name = "GramaFix"
db = client[db_name]
issues_collection = db["issues"]
users_collection = db["users"]
status_updates_collection = db["status_updates"]
otp_codes_collection = db["otp_codes"]

# Role-based user collections ("branches")
users_citizen_collection = db["users_citizen"]
users_admin_collection = db["users_admin"]
users_panchayat_collection = db["users_panchayat"]  # maps to officer role

def get_user_role_collection(role: str):
    r = (role or "").lower()
    if r == "admin":
        return users_admin_collection
    if r in ("officer", "panchayat"):
        return users_panchayat_collection
    return users_citizen_collection

# Category-based issue collections ("branches")
issues_roads = db["issues_roads"]
issues_water = db["issues_water"]
issues_electricity = db["issues_electricity"]
issues_school = db["issues_school"]
issues_farming = db["issues_farming"]
issues_sanitation = db["issues_sanitation"]

def get_issue_category_collection(category: str):
    c = (category or "").lower()
    if c == "roads":
        return issues_roads
    if c == "water":
        return issues_water
    if c == "electricity":
        return issues_electricity
    if c == "school":
        return issues_school
    if c == "farming":
        return issues_farming
    if c == "sanitation":
        return issues_sanitation
    # fallback bucket
    return db[f"issues_{re.sub(r'[^a-z0-9]+', '_', c)}"]

# ---- File Upload Config ----
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

# ---- Groq Configuration for Whisper ----
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # For chatbot
GROQ_API_KEY_VOICE = os.getenv("GROQ_API_KEY_VOICE", "")  # For voice transcription
TRANSCRIBE_MODEL = "whisper-large-v3-turbo"  # Turbo model is less prone to hallucinations
ENABLE_SYMBOL_NORMALIZATION = True

def get_groq_client(use_voice_key=False):
    """Initialize and return Groq client. Set use_voice_key=True for transcription."""
    api_key = GROQ_API_KEY_VOICE if use_voice_key else GROQ_API_KEY
    if not api_key:
        key_type = "voice transcription" if use_voice_key else "chatbot"
        raise HTTPException(status_code=500, detail=f"Groq API key not configured for {key_type}")
    try:
        from groq import Groq  # lazy import to avoid hard dependency on startup
    except Exception:
        raise HTTPException(status_code=500, detail="Groq SDK not installed. Please install 'groq' Python package.")
    return Groq(api_key=api_key)

def normalize_spoken_symbols(text: str) -> str:
    """
    Convert spoken programming/special symbols to actual symbols:
    - "open parenthesis" → "("
    - "close bracket" → "]"
    - "colon" → ":"
    - etc.
    """
    if not text:
        return text
    
    # Define patterns for common spoken terms
    patterns = [
        (r"\bopen\s+parenthesis\b", "("),
        (r"\bclose\s+parenthesis\b", ")"),
        (r"\bopen\s+square\s+bracket\b", "["),
        (r"\bclose\s+square\s+bracket\b", "]"),
        (r"\bopen\s+curly\s+brace\b", "{"),
        (r"\bclose\s+curly\s+brace\b", "}"),
        (r"\bsemicolon\b", ";"),
        (r"\bcolon\b", ":"),
        (r"\bcomma\b", ","),
        (r"\bperiod\b|\bdot\b", "."),
        (r"\bplus\s+equals\b", "+="),
        (r"\bminus\s+equals\b", "-="),
        (r"\bdouble\s+equals\b", "=="),
        (r"\bequals\b", "="),
        (r"\bgreater\s+than\b", ">"),
        (r"\bless\s+than\b", "<"),
    (r"\bslash\b", "/"),
    # replacement must escape backslash for re.sub
    (r"\bbackslash\b", "\\\\"),
        (r"\bpercent\b", "%"),
        (r"\bdollar\s+sign\b", "$"),
        (r"\bat\s+sign\b", "@"),
        (r"\bhash\b|\bpound\b", "#"),
        (r"\bampersand\b", "&"),
        (r"\basterisk\b|\bstar\b", "*"),
        (r"\bunderscore\b", "_"),
        (r"\bhyphen\b|\bdash\b", "-"),
        (r"\bquestion\s+mark\b", "?"),
        (r"\bexclamation\s+mark\b", "!"),
    ]
    
    # Apply all replacements (case-insensitive)
    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result

# ---- Predefined Categories ----
CATEGORIES = [
    {"name": "Roads", "icon": "🛣", "description": "Damaged roads, potholes"},
    {"name": "Water", "icon": "💧", "description": "Water supply issues"},
    {"name": "Electricity", "icon": "💡", "description": "Power cuts, street lights"},
    {"name": "School", "icon": "🏫", "description": "School infrastructure"},
    {"name": "Farming", "icon": "🚜", "description": "Agricultural issues"},
    {"name": "Sanitation", "icon": "🗑", "description": "Waste disposal, toilets"},
]

# ---- Auth / Security ----
JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
ALGORITHM = "HS256"
# Prefer PBKDF2-SHA256 to avoid bcrypt backend issues and 72-byte limit; keep bcrypt variants for legacy verifies
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt_sha256", "bcrypt"],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_minutes: int = 60 * 24 * 7):
    to_encode = data.copy()
    # Optionally add exp; omitted for simplicity but recommended in production
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(roles: List[str]):
    async def _inner(user = Depends(get_current_user)):
        role = (user.get("role") or "").lower()
        if role not in [r.lower() for r in roles]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return _inner

# ---- Optional: S3 Uploads ----
ENABLE_S3_UPLOADS = os.getenv("ENABLE_S3_UPLOADS", "false").lower() in ("1", "true", "yes")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "")
AWS_REGION = os.getenv("AWS_REGION", "")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

def _s3_client():
    import boto3  # lazy import
    return boto3.client(
        "s3",
        region_name=AWS_REGION or None,
        aws_access_key_id=AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY or None,
    )

def store_file(content: bytes, filename: str, content_type: Optional[str]) -> str:
    """Store file and return a URL or local path under /uploads."""
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    key = f"{datetime.now().timestamp()}_{safe_name}"
    if ENABLE_S3_UPLOADS and AWS_S3_BUCKET:
        try:
            s3 = _s3_client()
            extra_args = {"ContentType": content_type} if content_type else {}
            s3.put_object(Bucket=AWS_S3_BUCKET, Key=key, Body=content, **extra_args)
            if AWS_REGION:
                return f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
            else:
                return f"https://{AWS_S3_BUCKET}.s3.amazonaws.com/{key}"
        except Exception:
            pass  # fallback to local
    file_path = os.path.join(UPLOAD_FOLDER, key)
    with open(file_path, "wb") as f:
        f.write(content)
    return f"uploads/{key}"

# ---- Optional: Twilio SMS (OTP / Alerts) ----
ENABLE_TWILIO_SMS = os.getenv("ENABLE_TWILIO_SMS", "false").lower() in ("1", "true", "yes")
ENABLE_TWILIO_OTP = os.getenv("ENABLE_TWILIO_OTP", "false").lower() in ("1", "true", "yes")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
DEBUG_OTP = os.getenv("DEBUG_OTP", "false").lower() in ("1", "true", "yes")

def send_sms(to: str, body: str) -> bool:
    if not (ENABLE_TWILIO_SMS or ENABLE_TWILIO_OTP):
        return False
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER):
        return False
    try:
        from twilio.rest import Client  # lazy import
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(to=to, from_=TWILIO_FROM_NUMBER, body=body)
        return True
    except Exception:
        return False

# ---- TOTP (Time-based One-Time Password) config ----
TOTP_ISSUER = os.getenv("TOTP_ISSUER", "GramaFix")
TOTP_ENCRYPTION_KEY = os.getenv("TOTP_ENCRYPTION_KEY", "")
TOTP_INTERVAL = int(os.getenv("TOTP_INTERVAL", "30"))
TOTP_DIGITS = int(os.getenv("TOTP_DIGITS", "6"))
TOTP_VALID_WINDOW = int(os.getenv("TOTP_VALID_WINDOW", "1"))  # allow +/- 1 step

_fernet_instance = None
def _get_fernet():
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance
    try:
        from cryptography.fernet import Fernet
        key = TOTP_ENCRYPTION_KEY
        if not key:
            # Generate ephemeral key for dev if none provided
            key = Fernet.generate_key().decode("utf-8")
            print("[WARN] TOTP_ENCRYPTION_KEY is not set. Generated ephemeral key for this process. Set it in your .env for persistence.")
        if isinstance(key, str):
            key = key.encode("utf-8")
        _fernet_instance = Fernet(key)
        return _fernet_instance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TOTP encryption not available: {e}")

def _enc_secret(secret: str) -> str:
    f = _get_fernet()
    return f.encrypt(secret.encode("utf-8")).decode("utf-8")

def _dec_secret(enc: str) -> str:
    f = _get_fernet()
    return f.decrypt(enc.encode("utf-8")).decode("utf-8")

async def init_indexes():
    # Helpful indexes for queries used in app
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index("phone", unique=True)
    await issues_collection.create_index([("created_at", -1)])
    await issues_collection.create_index("gram_panchayat")
    await issues_collection.create_index("category")
    await issues_collection.create_index("status")
    await status_updates_collection.create_index("issue_id")
    # device tokens removed (Firebase messaging removed)
    # OTP TTL index (expire after 'expires_at')
    try:
        await otp_codes_collection.create_index("phone")
        await otp_codes_collection.create_index("expires_at", expireAfterSeconds=0)
    except Exception:
        pass
    # per-role user collections
    for uc in (users_citizen_collection, users_admin_collection, users_panchayat_collection):
        try:
            await uc.create_index("email")
            await uc.create_index("phone")
            await uc.create_index("gram_panchayat")
        except Exception:
            pass
    # per-category issue collections
    for ic in (issues_roads, issues_water, issues_electricity, issues_school, issues_farming, issues_sanitation):
        try:
            await ic.create_index([("created_at", -1)])
            await ic.create_index("status")
            await ic.create_index("gram_panchayat")
        except Exception:
            pass

@app.on_event("startup")
async def on_startup():
    try:
        await init_indexes()
    except Exception as e:
        print(f"Index initialization warning: {e}")

# ---- Routes ----

@app.get("/api/health")
async def health():
    return {"status": "GramaFix Backend running ✅", "version": "1.0.0"}


@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio file to text using Groq Whisper model.
    Converts audio to optimal format and uses best settings for accuracy.
    """
    temp_path = None
    converted_path = None
    try:
        # Read uploaded audio file
        audio_data = await file.read()
        
        print(f"📝 Received audio file: {file.filename}")
        print(f"   Size: {len(audio_data)} bytes")
        print(f"   Content-Type: {file.content_type}")
        
        # Validate file size
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file received")
        
        if len(audio_data) < 1000:
            raise HTTPException(status_code=400, detail="Audio file too short (less than 1KB)")
        
        # Save temporarily
        timestamp = datetime.now().timestamp()
        temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{timestamp}_{file.filename}")
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        
        print(f"   Saved to: {temp_path}")
        
        # Convert to WAV format for better Whisper accuracy
        try:
            from pydub import AudioSegment
            from pydub.effects import normalize
            print("🔄 Converting audio to WAV format for optimal transcription...")
            
            # Load audio (supports webm, mp4, ogg, etc.)
            audio = AudioSegment.from_file(temp_path)
            
            # Apply preprocessing to improve transcription accuracy:
            # 1. Normalize audio (increases volume to optimal level)
            audio = normalize(audio)
            
            # 2. Boost volume by additional 3dB to ensure clarity
            audio = audio + 3
            
            # 3. Remove silence from start and end (common cause of hallucinations)
            # Detect leading silence
            def detect_leading_silence(sound, silence_threshold=-40.0, chunk_size=10):
                trim_ms = 0
                assert chunk_size > 0
                while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
                    trim_ms += chunk_size
                return trim_ms

            start_trim = detect_leading_silence(audio)
            end_trim = detect_leading_silence(audio.reverse())
            
            duration = len(audio)
            if start_trim < duration and end_trim < duration:
                audio = audio[start_trim:duration-end_trim]
                print(f"   Trimmed silence: {start_trim}ms from start, {end_trim}ms from end")
            
            # 4. Convert to optimal settings for Whisper
            # 16kHz sample rate, mono, 16-bit
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            
            converted_path = os.path.join(UPLOAD_FOLDER, f"converted_{timestamp}.wav")
            audio.export(converted_path, format="wav")
            print(f"   Converted to: {converted_path}")
            print(f"   Final audio duration: {len(audio)/1000:.2f}s")
            
            # Use converted file for transcription
            transcription_file = converted_path
            transcription_content_type = "audio/wav"
        except ImportError:
            print("⚠️  pydub not available, using original file")
            transcription_file = temp_path
            transcription_content_type = file.content_type or "audio/webm"
        except Exception as conv_error:
            print(f"⚠️  Audio conversion failed: {conv_error}, using original file")
            transcription_file = temp_path
            transcription_content_type = file.content_type or "audio/webm"
        
        # Transcribe using Groq Whisper with voice-specific API key
        print("🎤 Starting Groq Whisper transcription...")
        client = get_groq_client(use_voice_key=True)
        
        # Common hallucinated phrases that Whisper produces with unclear audio
        HALLUCINATION_PHRASES = [
            "thank you", "thanks for watching", "thank you for watching",
            "bye", "goodbye", "see you", "please subscribe",
            "thanks", "thank you so much", "like and subscribe",
            ".", "..", "..."  # Just punctuation
        ]
        
        transcript = None
        best_transcript = None
        
        # Try multiple strategies to get accurate transcription
        strategies = [
            # Strategy 1: Turbo model with no hallucination suppression
            {
                "model": "whisper-large-v3-turbo",
                "temperature": 0.0,
                "language": "en",
                "prompt": "Report: "  # Short prompt to anchor context
            },
            # Strategy 2: Standard model with higher temperature
            {
                "model": "whisper-large-v3",
                "temperature": 0.4,
                "language": "en",
            },
            # Strategy 3: Turbo model with no language constraint
            {
                "model": "whisper-large-v3-turbo",
                "temperature": 0.0,
            }
        ]
        
        for idx, strategy in enumerate(strategies):
            try:
                print(f"🔄 Attempt {idx + 1}: Using {strategy.get('model', 'default')} model...")
                
                with open(transcription_file, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        file=(os.path.basename(transcription_file), audio_file, transcription_content_type),
                        model=strategy["model"],
                        response_format="verbose_json",
                        **{k: v for k, v in strategy.items() if k != "model"}
                    )
                
                # Extract text
                if hasattr(transcription, 'text'):
                    current_transcript = transcription.text.strip()
                else:
                    current_transcript = str(transcription).strip()
                
                # Log this attempt
                print(f"   Result {idx + 1}: '{current_transcript}'")
                
                # Check if this is a hallucination
                is_hallucination = any(
                    current_transcript.lower().strip() == phrase.lower().strip() 
                    for phrase in HALLUCINATION_PHRASES
                )
                
                if not is_hallucination and len(current_transcript) > 3:
                    # Found a good transcription!
                    transcript = current_transcript
                    print(f"✅ Valid transcription found on attempt {idx + 1}")
                    break
                else:
                    # Keep this as backup but continue trying
                    if best_transcript is None or len(current_transcript) > len(best_transcript):
                        best_transcript = current_transcript
                    print(f"   ⚠️  Possible hallucination detected, trying next strategy...")
                    
            except Exception as e:
                print(f"   ❌ Attempt {idx + 1} failed: {e}")
                continue
        
        # If all strategies failed or returned hallucinations, use the best one we got
        if transcript is None:
            transcript = best_transcript if best_transcript else "Unable to transcribe audio clearly. Please try again."
            print(f"⚠️  All attempts showed hallucinations. Using best result: '{transcript}'")
        
        # Extract text and metadata from verbose response
        if hasattr(transcription, 'text'):
            transcript = transcription.text.strip()
        else:
            transcript = str(transcription).strip()
        
        # Log detailed information if available
        detected_language = getattr(transcription, 'language', 'unknown')
        duration = getattr(transcription, 'duration', 'unknown')
        
        print(f"✅ Transcription received:")
        print(f"   Language detected: {detected_language}")
        print(f"   Duration: {duration}s")
        print(f"   Transcript length: {len(transcript)} chars")
        print(f"   Full transcript: '{transcript}'")
        
        # Log segments if available for debugging
        if hasattr(transcription, 'segments') and transcription.segments:
            print(f"   Segments: {len(transcription.segments)}")
            for i, seg in enumerate(transcription.segments[:3]):  # Show first 3 segments
                seg_text = getattr(seg, 'text', '')
                print(f"     Segment {i+1}: '{seg_text}'")
        
        # Normalize spoken symbols if enabled
        if ENABLE_SYMBOL_NORMALIZATION:
            transcript = normalize_spoken_symbols(transcript)
        
        # Clean up temp files
        try:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            if converted_path and os.path.exists(converted_path):
                os.remove(converted_path)
        except:
            pass
        
        return JSONResponse(content={
            "success": True,
            "transcript": transcript
        })
        
    except Exception as e:
        # Clean up temp files on error
        try:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            if converted_path and os.path.exists(converted_path):
                os.remove(converted_path)
        except:
            pass
        
        # Log the detailed error
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ Transcription Error: {str(e)}")
        print(f"Full traceback:\n{error_detail}")
        
        return JSONResponse(
            content={"success": False, "error": str(e), "detail": error_detail},
            status_code=500
        )


# ---- Authentication Routes ----

@app.post("/api/auth/register")
async def register_user(user: User):
    """Register a new user (citizen, officer, or admin)"""
    # Check if email already exists
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if phone already exists
    existing_phone = await users_collection.find_one({"phone": user.phone})
    if existing_phone:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # Hash password
    user_dict = user.model_dump(exclude={"id"})
    user_dict["password"] = hash_password(user_dict["password"])
    user_dict["created_at"] = datetime.now()
    user_dict["is_active"] = True
    
    result = await users_collection.insert_one(user_dict)
    inserted_id = result.inserted_id
    # Mirror into role-specific collection
    try:
        role_coll = get_user_role_collection(user_dict.get("role"))
        # ensure same _id for cross-updates
        role_doc = {**user_dict, "_id": inserted_id}
        await role_coll.insert_one(role_doc)
    except Exception:
        pass
    user_dict["_id"] = str(inserted_id)
    
    return {
        "message": "User registered successfully",
        "user_id": str(result.inserted_id)
    }


@app.post("/api/auth/login")
async def login_user(credentials: dict):
    """Login user with email and password"""
    email = credentials.get("email")
    password = credentials.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    # Find user by email
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check password (with migration fallback from legacy plaintext)
    stored_pw = user.get("password", "")
    valid = False
    try:
        valid = verify_password(password, stored_pw)
    except Exception:
        valid = False
    if not valid:
        # Legacy support: plaintext match then upgrade to hash
        if stored_pw and stored_pw == password:
            try:
                await users_collection.update_one(
                    {"_id": user["_id"]}, {"$set": {"password": hash_password(password)}}
                )
            except Exception:
                pass
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is inactive")
    
    # Remove sensitive data
    user["_id"] = str(user["_id"])
    user.pop("password", None)
    # serialize dates
    if isinstance(user.get("created_at"), datetime):
        user["created_at"] = user["created_at"].isoformat()
    if isinstance(user.get("updated_at"), datetime):
        user["updated_at"] = user["updated_at"].isoformat()
    
    # Generate JWT token
    token = create_access_token({"sub": user["_id"]})
    
    return {
        "message": "Login successful",
        "token": token,
        "user": user
    }


## Firebase phone auth removed: no longer verifying Firebase tokens.


@app.get("/api/auth/profile")
async def get_profile(user_id: str):
    """Get user profile by ID"""
    try:
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user["_id"] = str(user["_id"])
        user.pop("password", None)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {str(e)}")


@app.put("/api/auth/profile")
async def update_profile(user_id: str, updates: dict):
    """Update user profile"""
    try:
        # Don't allow updating sensitive fields
        updates.pop("password", None)
        updates.pop("role", None)
        updates.pop("email", None)
        updates["updated_at"] = datetime.now()
        
        # Fetch user to determine role branch
        existing_user = await users_collection.find_one({"_id": ObjectId(user_id)})
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": updates}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Mirror update to role-specific collection
        try:
            if existing_user:
                role = existing_user.get("role")
                role_coll = get_user_role_collection(role)
                await role_coll.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
        except Exception:
            pass
        return {"message": "Profile updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating profile: {str(e)}")


@app.get("/api/categories")
async def get_categories():
    """Get all issue categories"""
    return {"categories": CATEGORIES}


@app.post("/api/issues")
async def create_issue(
    background_tasks: BackgroundTasks,
    category: str = Form(...),
    description: str = Form(...),
    reporter_name: str = Form(...),
    reporter_phone: str = Form(...),
    gram_panchayat: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    address: str = Form(...),
    voice_description: Optional[str] = Form(None),
    images: List[UploadFile] = File(None),
):
    """Create a new issue report"""
    
    # Handle image uploads
    image_paths = []
    if images:
        for img in images:
            if img.filename:
                content = await img.read()
                stored_path = store_file(content, img.filename, img.content_type)
                image_paths.append(stored_path)

    issue = {
        "category": category,
        "description": description,
        "voice_description": voice_description,
        "location": {
            "latitude": latitude,
            "longitude": longitude,
            "address": address
        },
        "images": image_paths,
        "reporter_name": reporter_name,
        "reporter_phone": reporter_phone,
        "status": "Received",
        "priority_votes": 0,
        "voters": [],
        "assigned_to": None,
        "gram_panchayat": gram_panchayat,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "resolved_at": None
    }

    result = await issues_collection.insert_one(issue)
    issue["_id"] = result.inserted_id
    # Ensure progress_images array exists
    if not issue.get("progress_images"):
        issue["progress_images"] = []
    # Mirror into category-specific collection
    try:
        cat_coll = get_issue_category_collection(category)
        await cat_coll.insert_one(issue)
    except Exception:
        pass
    # Notifications removed (n8n, Firebase, SMS all removed per user direction)
    
    # SMS notifications disabled per user request
    # if ENABLE_TWILIO_SMS and reporter_phone:
    #     try:
    #         send_sms(
    #             to=reporter_phone,
    #             body=f"GramaFix: Issue received in {gram_panchayat}. Category: {category}. We'll update you on progress."
    #         )
    #     except Exception:
    #         pass
    
    return {
        "message": "Issue reported successfully",
        "issue_id": str(result.inserted_id),
        "status": "Received"
    }


@app.get("/api/issues")
async def get_issues(
    gram_panchayat: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """Get all issues with optional filters"""
    
    query = {}
    if gram_panchayat:
        query["gram_panchayat"] = gram_panchayat
    if category:
        query["category"] = category
    if status:
        query["status"] = status

    cursor = issues_collection.find(query).sort("created_at", -1).limit(limit)
    issues = []
    
    async for issue in cursor:
        issue["_id"] = str(issue["_id"])
        # ensure datetime serialization
        if isinstance(issue.get("created_at"), datetime):
            issue["created_at"] = issue["created_at"].isoformat()
        if isinstance(issue.get("updated_at"), datetime):
            issue["updated_at"] = issue["updated_at"].isoformat()
        if issue.get("resolved_at"):
            if isinstance(issue.get("resolved_at"), datetime):
                issue["resolved_at"] = issue["resolved_at"].isoformat()
        issues.append(issue)
    
    return {"issues": issues, "count": len(issues)}


@app.get("/api/issues/{issue_id}")
async def get_issue(issue_id: str):
    """Get a specific issue by ID"""
    
    if not ObjectId.is_valid(issue_id):
        raise HTTPException(status_code=400, detail="Invalid issue ID")
    
    issue = await issues_collection.find_one({"_id": ObjectId(issue_id)})
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    issue["_id"] = str(issue["_id"])
    if isinstance(issue.get("created_at"), datetime):
        issue["created_at"] = issue["created_at"].isoformat()
    if isinstance(issue.get("updated_at"), datetime):
        issue["updated_at"] = issue["updated_at"].isoformat()
    if issue.get("resolved_at") and isinstance(issue.get("resolved_at"), datetime):
        issue["resolved_at"] = issue["resolved_at"].isoformat()
    
    return issue


@app.put("/api/issues/{issue_id}/status")
async def update_issue_status(
    background_tasks: BackgroundTasks,
    issue_id: str,
    status: str = Form(...),
    remarks: Optional[str] = Form(None),
    updated_by: str = Form(...),
    assigned_department: Optional[str] = Form(None),
    progress_images: List[UploadFile] = File(None),
    user = Depends(require_role(["admin", "officer", "panchayat"]))
):
    """Update issue status (for officers/admin)"""
    
    if not ObjectId.is_valid(issue_id):
        raise HTTPException(status_code=400, detail="Invalid issue ID")
    
    valid_statuses = ["Received", "In Progress", "Resolved"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    update_data = {
        "status": status,
        "updated_at": datetime.utcnow()
    }
    
    if status == "Resolved":
        update_data["resolved_at"] = datetime.utcnow()
    
    # Handle optional assigned_department
    if assigned_department:
        update_data["assigned_department"] = assigned_department
    # Handle optional progress images
    new_progress_paths = []
    if progress_images:
        for img in progress_images:
            if img and img.filename:
                content = await img.read()
                stored = store_file(content, img.filename, img.content_type)
                new_progress_paths.append(stored)
    if new_progress_paths:
        # Append to array
        await issues_collection.update_one(
            {"_id": ObjectId(issue_id)},
            {"$push": {"progress_images": {"$each": new_progress_paths}}},
        )

    result = await issues_collection.update_one(
        {"_id": ObjectId(issue_id)},
        {"$set": update_data}
    )
    
    # Log status update
    status_log = {
        "issue_id": issue_id,
        "status": status,
        "remarks": remarks,
        "updated_by": updated_by,
        "updated_at": datetime.utcnow(),
        "assigned_department": assigned_department,
        "progress_images": new_progress_paths,
    }
    await status_updates_collection.insert_one(status_log)
    # Mirror update to category-specific collection
    try:
        if 'updated_issue' in locals() and updated_issue:
            cat_coll = get_issue_category_collection(updated_issue.get("category"))
            await cat_coll.update_one({"_id": ObjectId(issue_id)}, {"$set": update_data})
    except Exception:
        pass
    # Load issue for notifications
    updated_issue = await issues_collection.find_one({"_id": ObjectId(issue_id)})
    if updated_issue:
        # Notifications removed (n8n, Firebase, SMS all removed per user direction)
        pass
    
    # SMS notifications disabled per user request
    # try:
    #     if ENABLE_TWILIO_SMS and updated_issue and updated_issue.get("reporter_phone"):
    #         send_sms(
    #             to=updated_issue.get("reporter_phone"),
    #             body=f"GramaFix update: Your issue status is now '{status}'."
    #         )
    # except Exception:
    #     pass
    
    return {
        "message": "Status updated successfully",
        "issue_id": issue_id,
        "new_status": status
    }


# ---- OTP Authentication ----

@app.post("/api/auth/request_otp")
async def request_otp(payload: dict):
    """Request an OTP code for a phone number. Expires in 5 minutes."""
    phone = payload.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="phone is required")
    # generate 6-digit code
    code = "".join(secrets.choice(string.digits) for _ in range(6))
    hashed = pwd_context.hash(code)
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=5)
    doc = {
        "phone": phone,
        "code": hashed,
        "created_at": now,
        "expires_at": expires_at,
        "attempts": 0,
    }
    await otp_codes_collection.update_one(
        {"phone": phone},
        {"$set": doc},
        upsert=True,
    )
    # send SMS if enabled
    if ENABLE_TWILIO_OTP:
        send_sms(to=phone, body=f"Your GramaFix OTP is {code}. It expires in 5 minutes.")
    resp = {"success": True, "message": "OTP sent if SMS is enabled"}
    if DEBUG_OTP and not ENABLE_TWILIO_OTP:
        resp["debug_code"] = code
    return resp


@app.post("/api/auth/verify_otp")
async def verify_otp(payload: dict):
    """Verify OTP code and issue a JWT. Creates a citizen user if phone doesn't exist."""
    phone = payload.get("phone")
    code = payload.get("code")
    name = payload.get("name") or "Citizen"
    gram_panchayat = payload.get("gram_panchayat")
    if not phone or not code:
        raise HTTPException(status_code=400, detail="phone and code are required")
    rec = await otp_codes_collection.find_one({"phone": phone})
    if not rec:
        raise HTTPException(status_code=400, detail="OTP not requested or expired")
    # basic attempt limit
    attempts = rec.get("attempts", 0)
    if attempts >= 5:
        raise HTTPException(status_code=429, detail="Too many attempts. Request a new OTP.")
    await otp_codes_collection.update_one({"_id": rec["_id"]}, {"$inc": {"attempts": 1}})
    try:
        valid = verify_password(code, rec.get("code", ""))
    except Exception:
        valid = False
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid code")
    # success - optionally delete the record now
    try:
        await otp_codes_collection.delete_one({"_id": rec["_id"]})
    except Exception:
        pass
    # fetch or create user by phone
    user = await users_collection.find_one({"phone": phone})
    if not user:
        user = {
            "name": name,
            "phone": phone,
            "role": "citizen",
            "gram_panchayat": gram_panchayat,
            "created_at": datetime.utcnow(),
            "is_active": True,
        }
        result = await users_collection.insert_one(user)
        user["_id"] = result.inserted_id
        # mirror to role branch
        try:
            role_coll = get_user_role_collection("citizen")
            await role_coll.insert_one({**user})
        except Exception:
            pass
    # sanitize and issue token
    user_out = dict(user)
    uid = user_out.pop("_id", None)
    user_out["_id"] = str(uid) if uid else None
    user_out.pop("password", None)
    if isinstance(user_out.get("created_at"), datetime):
        user_out["created_at"] = user_out["created_at"].isoformat()
    token = create_access_token({"sub": user_out["_id"]})
    return {"message": "OTP verified", "token": token, "user": user_out}


# ---- TOTP Authentication (App-based OTP like Google Authenticator) ----

@app.post("/api/auth/totp/setup/start")
async def totp_setup_start(user=Depends(get_current_user)):
    """Begin TOTP setup for the current user. Returns otpauth URI and QR as data URL."""
    try:
        import pyotp
        import base64
        from io import BytesIO
        import qrcode
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Missing TOTP dependencies: {e}")

    # Generate new secret and provisioning URI
    secret = pyotp.random_base32()
    label = user.get("email") or user.get("phone") or user.get("name") or "user"
    totp = pyotp.TOTP(secret, interval=TOTP_INTERVAL, digits=TOTP_DIGITS)
    otpauth_uri = totp.provisioning_uri(name=label, issuer_name=TOTP_ISSUER)

    # Generate QR data URL
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(otpauth_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    # Store encrypted secret disabled by default
    enc = _enc_secret(secret)
    await users_collection.update_one(
        {"_id": ObjectId(user["_id"])} if isinstance(user.get("_id"), str) else {"_id": user["_id"]},
        {"$set": {"totp": {
            "enabled": False,
            "secret_enc": enc,
            "provisioning_uri": otpauth_uri,
            "created_at": datetime.utcnow(),
            "last_timecode": None,
        }}}
    )
    return {"otpauth_uri": otpauth_uri, "qr_data_url": data_url, "issuer": TOTP_ISSUER, "label": label}


@app.post("/api/auth/totp/setup/verify")
async def totp_setup_verify(payload: dict, user=Depends(get_current_user)):
    """Verify the first TOTP code to enable TOTP for the user."""
    try:
        import pyotp
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Missing TOTP dependencies: {e}")
    code = str(payload.get("code") or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="code is required")
    doc = await users_collection.find_one({"_id": user["_id"]})
    if not doc or not doc.get("totp", {}).get("secret_enc"):
        raise HTTPException(status_code=400, detail="TOTP not initialized. Start setup first.")
    secret = _dec_secret(doc["totp"]["secret_enc"])
    totp = pyotp.TOTP(secret, interval=TOTP_INTERVAL, digits=TOTP_DIGITS)
    valid = False
    try:
        valid = totp.verify(code, valid_window=TOTP_VALID_WINDOW)
    except Exception:
        valid = False
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid TOTP code")
    # Save enabled and last timecode to prevent replay
    last_tc = totp.timecode(datetime.utcnow())
    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"totp.enabled": True, "totp.verified_at": datetime.utcnow(), "totp.last_timecode": last_tc}}
    )
    return {"success": True, "message": "TOTP enabled"}


@app.post("/api/auth/totp/verify")
async def totp_verify(payload: dict):
    """Verify a TOTP code for login. Accepts email or phone to identify the user."""
    try:
        import pyotp
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Missing TOTP dependencies: {e}")
    ident = (payload.get("email") or payload.get("phone") or "").strip()
    code = str(payload.get("code") or "").strip()
    if not ident or not code:
        raise HTTPException(status_code=400, detail="email/phone and code are required")
    # Find user by email or phone
    q = {"$or": [{"email": ident}, {"phone": ident}]}
    user = await users_collection.find_one(q)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    totp_info = user.get("totp") or {}
    if not totp_info.get("enabled") or not totp_info.get("secret_enc"):
        raise HTTPException(status_code=400, detail="TOTP is not enabled for this user")

    secret = _dec_secret(totp_info["secret_enc"])
    totp = pyotp.TOTP(secret, interval=TOTP_INTERVAL, digits=TOTP_DIGITS)
    current_tc = totp.timecode(datetime.utcnow())
    # Prevent replay of same timecode
    last_tc = totp_info.get("last_timecode")
    if last_tc is not None and int(current_tc) == int(last_tc):
        raise HTTPException(status_code=401, detail="Code already used. Please wait for the next code.")
    valid = False
    try:
        valid = totp.verify(code, valid_window=TOTP_VALID_WINDOW)
    except Exception:
        valid = False
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid TOTP code")
    # Update last_timecode and issue JWT
    await users_collection.update_one({"_id": user["_id"]}, {"$set": {"totp.last_timecode": int(current_tc)}})
    # Sanitize user
    user_out = dict(user)
    uid = user_out.pop("_id", None)
    user_out["_id"] = str(uid) if uid else None
    user_out.pop("password", None)
    if isinstance(user_out.get("created_at"), datetime):
        user_out["created_at"] = user_out["created_at"].isoformat()
    token = create_access_token({"sub": user_out["_id"]})
    return {"message": "TOTP verified", "token": token, "user": user_out}


# ---- CSV Export ----

@app.get("/api/admin/export/issues.csv")
async def export_issues_csv(gram_panchayat: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, user = Depends(require_role(["admin", "officer", "panchayat"]))):
    """Export issues as CSV. Optionally filtered by gram_panchayat."""
    import csv
    from io import StringIO
    query = {}
    if gram_panchayat:
        query["gram_panchayat"] = gram_panchayat
    # Date filters
    def parse_dt(s):
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None
    dt_start = parse_dt(start_date) if start_date else None
    dt_end = parse_dt(end_date) if end_date else None
    if dt_start or dt_end:
        query["created_at"] = {}
        if dt_start:
            query["created_at"]["$gte"] = dt_start
        if dt_end:
            query["created_at"]["$lte"] = dt_end
    cursor = issues_collection.find(query).sort("created_at", -1)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "category",
        "description",
        "gram_panchayat",
        "status",
        "priority_votes",
        "created_at",
        "resolved_at",
    ])
    async for doc in cursor:
        writer.writerow([
            str(doc.get("_id")),
            doc.get("category", ""),
            (doc.get("description", "") or "").replace("\n", " ").strip(),
            doc.get("gram_panchayat", ""),
            doc.get("status", ""),
            doc.get("priority_votes", 0),
            doc.get("created_at").isoformat() if isinstance(doc.get("created_at"), datetime) else doc.get("created_at"),
            doc.get("resolved_at").isoformat() if isinstance(doc.get("resolved_at"), datetime) else (doc.get("resolved_at") or ""),
        ])
    output.seek(0)
    headers = {
        "Content-Disposition": "attachment; filename=issues.csv"
    }
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)


@app.get("/api/issues/{issue_id}/status_history")
async def get_status_history(issue_id: str):
    """Get status update history for an issue"""
    if not ObjectId.is_valid(issue_id):
        raise HTTPException(status_code=400, detail="Invalid issue ID")
    cursor = status_updates_collection.find({"issue_id": issue_id}).sort("updated_at", 1)
    history = []
    async for su in cursor:
        su["_id"] = str(su["_id"]) if "_id" in su else None
        if isinstance(su.get("updated_at"), datetime):
            su["updated_at"] = su["updated_at"].isoformat()
        history.append(su)
    return {"history": history}


# Device token registration removed (Firebase messaging removed)


@app.post("/api/issues/{issue_id}/vote")
async def vote_issue(issue_id: str, voter_phone: str = Form(...)):
    """Vote for an issue to increase priority"""
    
    if not ObjectId.is_valid(issue_id):
        raise HTTPException(status_code=400, detail="Invalid issue ID")
    
    issue = await issues_collection.find_one({"_id": ObjectId(issue_id)})
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Check if user already voted
    if voter_phone in issue.get("voters", []):
        raise HTTPException(status_code=400, detail="You have already voted for this issue")
    
    # Add vote
    result = await issues_collection.update_one(
        {"_id": ObjectId(issue_id)},
        {
            "$inc": {"priority_votes": 1},
            "$push": {"voters": voter_phone}
        }
    )
    # Mirror vote to category collection
    try:
        cat_coll = get_issue_category_collection(issue.get("category"))
        await cat_coll.update_one(
            {"_id": ObjectId(issue_id)},
            {"$inc": {"priority_votes": 1}, "$push": {"voters": voter_phone}}
        )
    except Exception:
        pass
    
    return {
        "message": "Vote recorded successfully",
        "issue_id": issue_id,
        "total_votes": issue["priority_votes"] + 1
    }


# ---- Simple Chatbot Endpoint ----

@app.post("/api/chatbot/message")
async def chatbot_message(payload: dict):
    """Chatbot endpoint. Uses GROQ_API_KEY for chatbot, falls back to rule-based replies."""
    user_msg = (payload.get("message") or "").strip()
    if not user_msg:
        return {"reply": "Please type your question or say hi."}

    # Try Groq LLM first if configured
    if GROQ_API_KEY:
        try:
            from groq import Groq
            model = os.getenv("GROQ_CHAT_MODEL", "llama-3.1-8b-instant")
            client = get_groq_client(use_voice_key=False)  # Use chatbot key
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are GramaBot, a helpful assistant for a rural issue reporting app called GramaFix. Keep answers concise and friendly. If a user asks for harmful or illegal content, reply: 'Sorry, I can't assist with that.'"},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2,
                max_tokens=256,
            )
            reply = completion.choices[0].message.content.strip()
            return {"reply": reply}
        except Exception as e:
            # Fallback to rule-based
            pass

    # Rule-based fallback
    msg = user_msg.lower()
    def contains(*words):
        return any(w in msg for w in words)
    if contains("hi", "hello", "hey"):
        return {"reply": "Hi! I'm GramaBot. I can help you report issues, check status, or learn how to register. What would you like to do?"}
    if contains("report"):
        return {"reply": "To report an issue: go to the Report page, choose a category, add a description and photos, and submit."}
    if contains("status", "track"):
        return {"reply": "To check status: open Reports, find your issue, and view its current status and history."}
    if contains("register", "signup", "sign up"):
        return {"reply": "To register: open the Register page, enter your details, and create an account. You can enable Authenticator (TOTP) in Profile."}
    if contains("totp", "authenticator", "otp"):
        return {"reply": "In your Profile, enable Authenticator to get a QR code. Scan it with Google Authenticator or Authy, then enter the 6-digit code to verify."}
    return {"reply": "I didn't catch that. Ask about reporting an issue, checking status, registration, or Authenticator (TOTP)."}


@app.get("/api/analytics")
async def get_analytics(gram_panchayat: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, trend_days: int = 14):
    """Get analytics data for dashboard"""
    
    query = {}
    if gram_panchayat:
        query["gram_panchayat"] = gram_panchayat
    # Date filters
    def parse_dt(s):
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None
    dt_start = parse_dt(start_date) if start_date else None
    dt_end = parse_dt(end_date) if end_date else None
    if dt_start or dt_end:
        query["created_at"] = {}
        if dt_start:
            query["created_at"]["$gte"] = dt_start
        if dt_end:
            query["created_at"]["$lte"] = dt_end
    
    # Total issues
    total_issues = await issues_collection.count_documents(query)
    
    # Issues by status
    received = await issues_collection.count_documents({**query, "status": "Received"})
    in_progress = await issues_collection.count_documents({**query, "status": "In Progress"})
    resolved = await issues_collection.count_documents({**query, "status": "Resolved"})
    
    # Issues by category
    category_stats = []
    for cat in CATEGORIES:
        count = await issues_collection.count_documents({**query, "category": cat["name"]})
        category_stats.append({"category": cat["name"], "icon": cat["icon"], "count": count})
    
    # Most voted issues
    top_issues = []
    cursor = issues_collection.find(query).sort("priority_votes", -1).limit(5)
    async for issue in cursor:
        top_issues.append({
            "id": str(issue["_id"]),
            "category": issue["category"],
            "description": issue["description"][:100],
            "votes": issue["priority_votes"]
        })
    
    # Trend data: counts per day
    trend = []
    try:
        from datetime import timezone
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        async for row in issues_collection.aggregate(pipeline):
            trend.append({"date": row.get("_id"), "count": row.get("count", 0)})
        # Optionally limit to last trend_days entries
        if trend_days and len(trend) > trend_days:
            trend = trend[-trend_days:]
    except Exception:
        trend = []

    return {
        "total_issues": total_issues,
        "status_breakdown": {
            "received": received,
            "in_progress": in_progress,
            "resolved": resolved
        },
        "category_breakdown": category_stats,
        "top_priority_issues": top_issues,
        "resolution_rate": round((resolved / total_issues * 100) if total_issues > 0 else 0, 2),
        "trend": trend,
    }


@app.get("/api/issues")
async def get_issues(
    gram_panchayat: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get all issues with optional filters and date range"""
    query = {}
    if gram_panchayat:
        query["gram_panchayat"] = gram_panchayat
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    def parse_dt(s):
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None
    dt_start = parse_dt(start_date) if start_date else None
    dt_end = parse_dt(end_date) if end_date else None
    if dt_start or dt_end:
        query["created_at"] = {}
        if dt_start:
            query["created_at"]["$gte"] = dt_start
        if dt_end:
            query["created_at"]["$lte"] = dt_end

    cursor = issues_collection.find(query).sort("created_at", -1).limit(limit)
    issues = []
    async for issue in cursor:
        issue["_id"] = str(issue["_id"])
        if isinstance(issue.get("created_at"), datetime):
            issue["created_at"] = issue["created_at"].isoformat()
        if isinstance(issue.get("updated_at"), datetime):
            issue["updated_at"] = issue["updated_at"].isoformat()
        if issue.get("resolved_at") and isinstance(issue.get("resolved_at"), datetime):
            issue["resolved_at"] = issue["resolved_at"].isoformat()
        issues.append(issue)

    return {"issues": issues, "count": len(issues)}


@app.post("/api/users")
async def create_user(
    name: str = Form(...),
    phone: str = Form(...),
    role: str = Form("citizen"),
    gram_panchayat: str = Form(...)
):
    """Create a new user"""
    
    # Check if user already exists
    existing = await users_collection.find_one({"phone": phone})
    if existing:
        raise HTTPException(status_code=400, detail="User with this phone number already exists")
    
    user = {
        "name": name,
        "phone": phone,
        "role": role,
        "gram_panchayat": gram_panchayat,
        "created_at": datetime.utcnow()
    }
    
    result = await users_collection.insert_one(user)
    
    return {
        "message": "User created successfully",
        "user_id": str(result.inserted_id)
    }
