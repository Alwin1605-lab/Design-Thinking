from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import re
from datetime import datetime
from typing import List, Optional
from models import Issue, User, StatusUpdate, Category
import json
from groq import Groq
from dotenv import load_dotenv
from jose import jwt, JWTError
from passlib.context import CryptContext

# Load environment variables from .env file
load_dotenv()

# Import notifications after env is loaded so it can read configuration
from notifications import notify_issue_created, notify_status_updated

# ---- App Setup ----
app = FastAPI(title="GramaFix API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# ---- File Upload Config ----
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

# ---- Groq Configuration for Whisper ----
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Set your Groq API key in environment
TRANSCRIBE_MODEL = "whisper-large-v3"
ENABLE_SYMBOL_NORMALIZATION = True

def get_groq_client():
    """Initialize and return Groq client"""
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Groq API key not configured")
    return Groq(api_key=GROQ_API_KEY)

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
        (r"\bbackslash\b", "\\"),
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
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_minutes: int = 60 * 24 * 7):
    to_encode = data.copy()
    # Optionally add exp; omitted for simplicity but recommended in production
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

async def init_indexes():
    # Helpful indexes for queries used in app
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index("phone", unique=True)
    await issues_collection.create_index([("created_at", -1)])
    await issues_collection.create_index("gram_panchayat")
    await issues_collection.create_index("category")
    await issues_collection.create_index("status")
    await status_updates_collection.create_index("issue_id")

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
    Automatically normalizes spoken programming symbols (like "open parenthesis" -> "(")
    """
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
        temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{datetime.now().timestamp()}_{file.filename}")
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        
        print(f"   Saved to: {temp_path}")
        
        # Transcribe using Groq Whisper
        print("🎤 Starting Groq Whisper transcription...")
        client = get_groq_client()
        with open(temp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(file.filename, audio_file, file.content_type or "audio/webm"),
                model=TRANSCRIBE_MODEL,  # "whisper-large-v3"
                response_format="text"
            )
        
        print(f"✅ Transcription received: {transcription[:100]}...")
        transcript = transcription.strip()
        
        # Normalize spoken symbols if enabled
        if ENABLE_SYMBOL_NORMALIZATION:
            transcript = normalize_spoken_symbols(transcript)
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
        return JSONResponse(content={
            "success": True,
            "transcript": transcript
        })
        
    except Exception as e:
        # Clean up temp file on error
        if 'temp_path' in locals():
            try:
                os.remove(temp_path)
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
    user_dict["_id"] = str(result.inserted_id)
    
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
        
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": updates}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
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
                safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", img.filename)
                timestamped = f"{datetime.now().timestamp()}_{safe_name}"
                file_path = os.path.join(UPLOAD_FOLDER, timestamped)
                with open(file_path, "wb") as buffer:
                    buffer.write(await img.read())
                # Always expose path relative to static mount
                image_paths.append(f"uploads/{timestamped}")

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
    # Notify asynchronously
    background_tasks.add_task(notify_issue_created, issue)
    
    # TODO: Send SMS notification to reporter
    
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
        "updated_at": datetime.utcnow()
    }
    await status_updates_collection.insert_one(status_log)
    # Load issue for notifications
    updated_issue = await issues_collection.find_one({"_id": ObjectId(issue_id)})
    if updated_issue:
        background_tasks.add_task(notify_status_updated, updated_issue, status, remarks, updated_by)
    
    # TODO: Send SMS to reporter about status change
    
    return {
        "message": "Status updated successfully",
        "issue_id": issue_id,
        "new_status": status
    }


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
    
    return {
        "message": "Vote recorded successfully",
        "issue_id": issue_id,
        "total_votes": issue["priority_votes"] + 1
    }


@app.get("/api/analytics")
async def get_analytics(gram_panchayat: Optional[str] = None):
    """Get analytics data for dashboard"""
    
    query = {}
    if gram_panchayat:
        query["gram_panchayat"] = gram_panchayat
    
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
    
    return {
        "total_issues": total_issues,
        "status_breakdown": {
            "received": received,
            "in_progress": in_progress,
            "resolved": resolved
        },
        "category_breakdown": category_stats,
        "top_priority_issues": top_issues,
        "resolution_rate": round((resolved / total_issues * 100) if total_issues > 0 else 0, 2)
    }


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
