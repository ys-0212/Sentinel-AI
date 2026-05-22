# FastAPI Main Application
# Unified API for all cybersecurity modules

import os
import sys
import shutil
import tempfile
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Loaded environment variables from .env")
except ImportError:
    print("⚠ python-dotenv not installed. Using system environment variables only.")

# Configuration from environment variables
API_HOST = os.getenv("HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", "8000"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

# Add module directories to path for correct imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "IAP_AI_Malicious_Detector"))
sys.path.insert(0, os.path.join(BASE_DIR, "TypingIPVPNDetector"))
sys.path.insert(0, os.path.join(BASE_DIR, "call_scam_detector"))
sys.path.insert(0, os.path.join(BASE_DIR, "chatbot"))
sys.path.insert(0, os.path.join(BASE_DIR, "summarizer"))

# Import core modules using importlib for dynamic loading
import importlib.util

def load_module_from_path(module_name: str, file_path: str):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Load core modules dynamically
malicious_core = load_module_from_path(
    "malicious_core", 
    os.path.join(BASE_DIR, "IAP_AI_Malicious_Detector", "core.py")
)
typing_core = load_module_from_path(
    "typing_core",
    os.path.join(BASE_DIR, "TypingIPVPNDetector", "core.py")
)
scam_core = load_module_from_path(
    "scam_core",
    os.path.join(BASE_DIR, "call_scam_detector", "core.py")
)
chatbot_core = load_module_from_path(
    "chatbot_core_module",
    os.path.join(BASE_DIR, "chatbot", "core.py")
)
summarizer_core = load_module_from_path(
    "summarizer_core",
    os.path.join(BASE_DIR, "summarizer", "core.py")
)

# Extract functions from loaded modules
analyze_malicious_text = malicious_core.analyze_text
analyze_login_behavior = typing_core.analyze_login_behavior
analyze_ip_address = typing_core.analyze_ip_address
analyze_audio_for_scam = scam_core.analyze_audio_for_scam
analyze_text_for_scam = scam_core.analyze_text_for_scam
query_chatbot = chatbot_core.query_chatbot
summarize_complaint = summarizer_core.summarize_complaint
get_severity_color = summarizer_core.get_severity_color

# Import and initialize database
API_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, API_DIR)

from database import (
    init_db, authenticate_user, authenticate_admin, create_user, create_admin,
    create_complaint, get_user_complaints, get_all_complaints,
    update_complaint_status, get_complaint_stats, save_login_history,
    get_user_login_history, create_notification, get_user_notifications,
    get_all_login_history, get_admin_notifications, get_current_timestamp,
    get_user_profile, create_or_update_user_profile,
    get_admin_profile, create_or_update_admin_profile,
    verify_admin_deletion_password, delete_complaint as db_delete_complaint,
    get_deletion_audit, check_ip_disparity, get_user_previous_ip,
    update_admin_deletion_password, get_complaint_by_id,
    generate_otp, save_otp, verify_otp, get_user_by_email, get_user_by_username,
    check_profile_complete
)
init_db()  # Initialize database on startup

# Create FastAPI app
app = FastAPI(
    title="Cybersecurity App API",
    description="Unified API for cybersecurity detection modules",
    version="1.0.0"
)

# CORS middleware - allow all origins for development
# In production, set CORS_ORIGINS in .env to restrict
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins == "*":
    allow_origins = ["*"]
else:
    allow_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True if cors_origins != "*" else False,  # credentials require specific origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static files (legacy HTML frontend)
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
FRONTEND_EXISTS = os.path.exists(FRONTEND_DIR) and os.path.exists(os.path.join(FRONTEND_DIR, "login.html"))
if FRONTEND_EXISTS:
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")

# Mount React frontend build (new)
REACT_BUILD_DIR = os.path.join(BASE_DIR, "frontend-react", "dist")
REACT_ASSETS_DIR = os.path.join(REACT_BUILD_DIR, "assets")
if os.path.exists(REACT_ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=REACT_ASSETS_DIR), name="react_assets")

# Check if React build exists
USE_REACT = os.path.exists(os.path.join(REACT_BUILD_DIR, "index.html"))

# Check if running in API-only mode (Docker - frontend served by Nginx)
API_ONLY_MODE = not USE_REACT and not FRONTEND_EXISTS


def serve_react_or_legacy(legacy_file: str):
    """Serve React SPA if available, otherwise serve legacy HTML.
    In Docker API-only mode, returns JSON redirect instruction."""
    if API_ONLY_MODE:
        # In Docker, frontend is served by Nginx on port 80
        # Return JSON for API health check compatibility
        from fastapi.responses import JSONResponse
        return JSONResponse({
            "message": "API is running. Frontend is served on port 80.",
            "api_docs": "/docs",
            "status": "ok"
        })
    if USE_REACT:
        return FileResponse(os.path.join(REACT_BUILD_DIR, "index.html"))
    return FileResponse(os.path.join(FRONTEND_DIR, legacy_file))


# Serve frontend HTML pages - supports both React SPA and legacy HTML
@app.get("/", response_class=FileResponse)
async def serve_login():
    """Serve login page as root."""
    return serve_react_or_legacy("login.html")

@app.get("/login", response_class=FileResponse)
async def serve_login_page():
    """Serve login page."""
    return serve_react_or_legacy("login.html")

@app.get("/login.html")
async def serve_login_html():
    """Serve login page (with .html extension)."""
    return serve_react_or_legacy("login.html")


@app.get("/register", response_class=FileResponse)
async def serve_register():
    """Serve registration page."""
    return serve_react_or_legacy("register.html")

@app.get("/register.html")
async def serve_register_html():
    """Serve registration page (with .html extension)."""
    return serve_react_or_legacy("register.html")

@app.get("/dashboard", response_class=FileResponse)
async def serve_dashboard():
    """Serve user dashboard."""
    return serve_react_or_legacy("index.html")

# React SPA sub-routes (must return index.html for client-side routing)
@app.get("/dashboard/{path:path}")
async def serve_dashboard_subroutes(path: str):
    """Serve user dashboard sub-routes (SPA)."""
    return serve_react_or_legacy("index.html")

@app.get("/admin", response_class=FileResponse)
async def serve_admin():
    """Serve admin dashboard."""
    return serve_react_or_legacy("admin.html")

# React SPA admin sub-routes
@app.get("/admin/{path:path}")
async def serve_admin_subroutes(path: str):
    """Serve admin dashboard sub-routes (SPA)."""
    return serve_react_or_legacy("admin.html")

# ============================================================================
# Pydantic Models
# ============================================================================

class MaliciousTextRequest(BaseModel):
    """Request model for malicious text analysis."""
    text: str


class MaliciousTextResponse(BaseModel):
    """Response model for malicious text analysis."""
    threat_score: int
    intent_classification: str
    social_tactics_detected: List[str]
    ioc_detected: List[str]
    summary: str
    error: Optional[str] = None


class ScamTextRequest(BaseModel):
    """Request model for call scam text analysis."""
    text: str


class ScamAnalysisResponse(BaseModel):
    """Response model for scam analysis."""
    transcript: Optional[str] = None
    language: Optional[str] = None
    classification: str
    reason: str
    error: Optional[str] = None


class ChatbotRequest(BaseModel):
    """Request model for chatbot query."""
    question: str


class ChatbotResponse(BaseModel):
    """Response model for chatbot query."""
    answer: str
    source_type: str
    sources: List[str]
    error: Optional[str] = None


class SessionData(BaseModel):
    """Session data for behavior analysis."""
    typing_speed: int = 0
    mouse_movements: int = 0
    location: str = ""
    ip_address: str = ""
    vpn_detected: bool = False
    device_fingerprint: str = ""
    form_completion_time: int = 0
    typing_dna_confidence: int = 100


class BehaviorAnalysisRequest(BaseModel):
    """Request model for behavior analysis."""
    current_session: SessionData
    historical_sessions: Optional[List[SessionData]] = None


class BehaviorAnalysisResponse(BaseModel):
    """Response model for behavior analysis."""
    is_anomaly: bool
    risk_score: float
    reasons: List[str]


class IPAnalysisRequest(BaseModel):
    """Request model for IP analysis."""
    ip_address: str


class IPAnalysisResponse(BaseModel):
    """Response model for IP analysis."""
    ip_address: str
    location: str
    vpn_detected: bool
    proxy_detected: bool
    fraud_score: float
    geolocation_data: Optional[dict] = None
    fraud_data: Optional[dict] = None


class ComplaintSummaryResponse(BaseModel):
    """Response model for complaint summarization."""
    narrative_summary: str
    incident_details: dict
    classification: str
    severity_score: float
    severity_color: str
    contradiction: Optional[dict] = None
    evidence_extracted: Optional[dict] = None
    error: Optional[str] = None


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Cybersecurity API is running",
        "endpoints": {
            "malicious": "/malicious/analyze",
            "scam_text": "/call-scam/analyze-text",
            "scam_audio": "/call-scam/analyze-audio",
            "chatbot": "/chatbot/query",
            "complaint": "/complaint/summarize",
            "behavior": "/auth/analyze-behavior",
            "ip": "/auth/analyze-ip"
        }
    }


# --- Malicious Text Detection ---
@app.post("/malicious/analyze", response_model=MaliciousTextResponse)
async def analyze_malicious(request: MaliciousTextRequest):
    """
    Analyze text (chat/email/SMS) for malicious intent.
    
    Detects phishing, scareware, social engineering, etc.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    result = analyze_malicious_text(request.text)
    return MaliciousTextResponse(**result)


# --- Call Scam Detection ---
@app.post("/call-scam/analyze-text", response_model=ScamAnalysisResponse)
async def analyze_scam_text(request: ScamTextRequest):
    """
    Analyze text (call transcript) for scam detection.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    result = analyze_text_for_scam(request.text)
    return ScamAnalysisResponse(**result)


@app.post("/call-scam/analyze-audio", response_model=ScamAnalysisResponse)
async def analyze_scam_audio(
    audio_file: UploadFile = File(...),
    language: str = Form(default="en")
):
    """
    Upload audio file and analyze for scam detection.
    
    Supports: en (English), hi (Hindi)
    """
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, audio_file.filename)
    
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(audio_file.file, f)
        
        result = analyze_audio_for_scam(temp_path, language)
        return ScamAnalysisResponse(**result)
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


# --- Chatbot ---
@app.post("/chatbot/query", response_model=ChatbotResponse)
async def chatbot_query(request: ChatbotRequest):
    """
    Query the cybersecurity chatbot.
    
    Answers questions about cybercrime laws, procedures, etc.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    result = query_chatbot(request.question)
    return ChatbotResponse(**result)


# --- Complaint Summarization ---
@app.post("/complaint/summarize", response_model=ComplaintSummaryResponse)
async def summarize_complaint_endpoint(
    complaint: str = Form(...),
    pdf_file: Optional[UploadFile] = File(default=None),
    image_file: Optional[UploadFile] = File(default=None),
    audio_file: Optional[UploadFile] = File(default=None),
    video_file: Optional[UploadFile] = File(default=None)
):
    """
    Summarize a cybercrime complaint with optional evidence files.
    
    Analyzes complaint text and evidence (PDF, image, audio, video)
    to generate summary, classification, and severity score.
    """
    if not complaint.strip():
        raise HTTPException(status_code=400, detail="Complaint text is required")
    
    # Save uploaded files temporarily
    temp_dir = tempfile.mkdtemp()
    file_paths = {
        "pdf_path": None,
        "image_path": None,
        "audio_path": None,
        "video_path": None
    }
    
    try:
        # Save each uploaded file
        for key, upload_file in [
            ("pdf_path", pdf_file),
            ("image_path", image_file),
            ("audio_path", audio_file),
            ("video_path", video_file)
        ]:
            if upload_file:
                path = os.path.join(temp_dir, upload_file.filename)
                with open(path, "wb") as f:
                    shutil.copyfileobj(upload_file.file, f)
                file_paths[key] = path
        
        # Process complaint
        result = summarize_complaint(
            complaint,
            pdf_path=file_paths["pdf_path"],
            image_path=file_paths["image_path"],
            audio_path=file_paths["audio_path"],
            video_path=file_paths["video_path"]
        )
        
        # Add severity color
        result["severity_color"] = get_severity_color(result.get("severity_score", 0))
        
        return ComplaintSummaryResponse(**result)
        
    finally:
        # Cleanup temp files
        for path in file_paths.values():
            if path and os.path.exists(path):
                os.remove(path)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


# --- Behavior Analysis ---
@app.post("/auth/analyze-behavior", response_model=BehaviorAnalysisResponse)
async def analyze_behavior(request: BehaviorAnalysisRequest):
    """
    Analyze user login behavior for anomalies.
    
    Compares current session against historical sessions
    to detect suspicious behavior patterns.
    """
    current = request.current_session.model_dump()
    historical = [s.model_dump() for s in request.historical_sessions] if request.historical_sessions else []
    
    result = analyze_login_behavior(current, historical)
    return BehaviorAnalysisResponse(**result)


@app.post("/auth/analyze-ip", response_model=IPAnalysisResponse)
async def analyze_ip(request: IPAnalysisRequest):
    """
    Analyze an IP address for VPN/proxy usage and fraud risk.
    """
    if not request.ip_address.strip():
        raise HTTPException(status_code=400, detail="IP address is required")
    
    result = analyze_ip_address(request.ip_address)
    return IPAnalysisResponse(**result)


# ============================================================================
# Authentication & Database Endpoints
# ============================================================================

class UserLoginRequest(BaseModel):
    username: str
    password: str
    typing_speed: int = 0
    form_completion_time: int = 0
    typing_pattern: str = ""
    captcha_text: str = ""  # The displayed CAPTCHA
    captcha_answer: str = ""  # User's input
    captcha_typing_speed: int = 0  # Typing speed for CAPTCHA only

class AdminLoginRequest(BaseModel):
    username: str
    password: str
    security_code: str
    typing_speed: int = 0
    form_completion_time: int = 0
    captcha_text: str = ""
    captcha_answer: str = ""
    captcha_typing_speed: int = 0

class UserRegisterRequest(BaseModel):
    username: str
    email: str
    phone: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    user_type: str = "user"
    message: str = ""
    risk_score: float = 0
    is_anomaly: bool = False
    ip_disparity: bool = False

class ComplaintCreateRequest(BaseModel):
    complaint_text: str
    is_anonymous: bool = False

class StatsResponse(BaseModel):
    total: int
    pending: int
    ongoing: int
    solved: int

# Profile Models
class UserProfileRequest(BaseModel):
    full_name: str = ""
    date_of_birth: str = ""
    gender: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""
    gov_id_type: str = ""
    gov_id_number: str = ""

class AdminProfileRequest(BaseModel):
    full_name: str = ""
    designation: str = ""
    department: str = ""
    office_address: str = ""
    employee_id: str = ""

# Deletion Models
class DeleteComplaintRequest(BaseModel):
    deletion_password: str
    reason: str = ""

# OTP Models
class SendOTPRequest(BaseModel):
    email: str
    purpose: str = "verification"

class VerifyOTPRequest(BaseModel):
    email: str
    otp_code: str
    purpose: str = "verification"

class OTPLoginRequest(BaseModel):
    username: str
    otp_code: str
    captcha_text: str = ""
    captcha_answer: str = ""

class EnhancedRegisterRequest(BaseModel):
    full_name: str
    username: str
    email: str
    phone: str
    password: str


@app.post("/auth/login/user", response_model=LoginResponse)
async def login_user(request: UserLoginRequest, req: Request):
    """Authenticate user with typing biometrics and CAPTCHA."""
    
    # Validate CAPTCHA first
    if request.captcha_text and request.captcha_answer:
        if request.captcha_text.upper() != request.captcha_answer.upper():
            return LoginResponse(success=False, message="Invalid CAPTCHA. Please try again.")
    
    user = authenticate_user(request.username, request.password)
    
    if not user:
        return LoginResponse(success=False, message="Invalid username or password")
    
    # Get client IP from request
    client_ip = req.client.host if req.client else "Unknown"
    # Check for forwarded IP (if behind proxy)
    forwarded_for = req.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    # Check IP disparity
    ip_disparity_info = check_ip_disparity(user['user_id'], client_ip)
    previous_ip = ip_disparity_info.get('previous_ip', '')
    
    # Analyze IP for VPN/location
    ip_info = {"location": "Unknown", "vpn_detected": False}
    
    # Check if it's a localhost/local network IP
    is_local_ip = client_ip in ["127.0.0.1", "localhost", "::1"] or client_ip.startswith("192.168.") or client_ip.startswith("10.")
    
    if is_local_ip:
        ip_info["location"] = "Local Network"
    else:
        try:
            ip_analysis = analyze_ip_address(client_ip)
            ip_info["location"] = ip_analysis.get("location", "Unknown")
            ip_info["vpn_detected"] = ip_analysis.get("vpn_detected", False) or ip_analysis.get("proxy_detected", False)
        except Exception as e:
            print(f"IP analysis error: {e}")
    
    # Get historical login data for behavior analysis
    history = get_user_login_history(user['user_id'])
    
    # Prepare session data for analysis (use CAPTCHA typing speed for better detection)
    effective_typing_speed = request.captcha_typing_speed if request.captcha_typing_speed > 0 else request.typing_speed
    current_session = {
        "typing_speed": effective_typing_speed,
        "form_completion_time": request.form_completion_time,
        "typing_dna_confidence": min(100, effective_typing_speed * 2),
        "device_fingerprint": "web-client",
        "location": ip_info["location"],
        "vpn_detected": ip_info["vpn_detected"],
        "mouse_movements": 0
    }
    
    # Convert history for analysis
    hist_sessions = [
        {
            "typing_speed": h.get('typing_speed', 0),
            "form_completion_time": h.get('form_completion_time', 0),
            "typing_dna_confidence": 80,
            "device_fingerprint": h.get('device_fingerprint', ''),
            "location": h.get('location', ''),
            "vpn_detected": h.get('vpn_detected', 0),
            "mouse_movements": 0
        }
        for h in history
    ]
    
    # Analyze behavior
    analysis = analyze_login_behavior(current_session, hist_sessions)
    
    # Add IP disparity to anomaly reasons if detected
    anomaly_reasons = analysis['reasons'].copy()
    if ip_disparity_info.get('is_disparity'):
        anomaly_reasons.append(f"IP change detected: {previous_ip} -> {client_ip}")
    
    # Save login history with IP info and disparity
    save_login_history(
        user['user_id'], 'user',
        typing_speed=request.typing_speed,
        captcha_typing_speed=request.captcha_typing_speed,
        form_completion_time=request.form_completion_time,
        typing_pattern=request.typing_pattern,
        ip_address=client_ip,
        location=ip_info["location"],
        vpn_detected=1 if ip_info["vpn_detected"] else 0,
        risk_score=analysis['risk_score'],
        is_anomaly=1 if analysis['is_anomaly'] else 0,
        anomaly_reasons=', '.join(anomaly_reasons),
        ip_disparity=1 if ip_disparity_info.get('is_disparity') else 0,
        previous_ip=previous_ip
    )
    
    return LoginResponse(
        success=True,
        user_id=user['user_id'],
        username=user['username'],
        user_type="user",
        message="Login successful",
        risk_score=analysis['risk_score'],
        is_anomaly=analysis['is_anomaly'],
        ip_disparity=ip_disparity_info.get('is_disparity', False)
    )



@app.post("/auth/login/admin", response_model=LoginResponse)
async def login_admin(request: AdminLoginRequest, req: Request):
    """Authenticate admin with CAPTCHA."""
    
    # Validate CAPTCHA first
    if request.captcha_text and request.captcha_answer:
        if request.captcha_text.upper() != request.captcha_answer.upper():
            return LoginResponse(success=False, message="Invalid CAPTCHA. Please try again.")
    
    admin = authenticate_admin(request.username, request.password, request.security_code)
    
    if not admin:
        return LoginResponse(success=False, message="Invalid credentials")
    
    # Get client IP from request
    client_ip = req.client.host if req.client else "Unknown"
    forwarded_for = req.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    # Check IP disparity
    ip_disparity_info = check_ip_disparity(admin['admin_id'], client_ip)
    previous_ip = ip_disparity_info.get('previous_ip', '')
    
    # Analyze IP for VPN/location
    ip_info = {"location": "Unknown", "vpn_detected": False}
    
    # Check if it's a localhost/local network IP
    is_local_ip = client_ip in ["127.0.0.1", "localhost", "::1"] or client_ip.startswith("192.168.") or client_ip.startswith("10.")
    
    if is_local_ip:
        ip_info["location"] = "Local Network"
    else:
        try:
            ip_analysis = analyze_ip_address(client_ip)
            ip_info["location"] = ip_analysis.get("location", "Unknown")
            ip_info["vpn_detected"] = ip_analysis.get("vpn_detected", False) or ip_analysis.get("proxy_detected", False)
        except Exception as e:
            print(f"IP analysis error: {e}")
    
    # Save login history with IP info and disparity
    save_login_history(
        admin['admin_id'], 'admin',
        typing_speed=request.typing_speed,
        captcha_typing_speed=request.captcha_typing_speed,
        form_completion_time=request.form_completion_time,
        ip_address=client_ip,
        location=ip_info["location"],
        vpn_detected=1 if ip_info["vpn_detected"] else 0,
        ip_disparity=1 if ip_disparity_info.get('is_disparity') else 0,
        previous_ip=previous_ip
    )
    
    return LoginResponse(
        success=True,
        user_id=admin['admin_id'],
        username=admin['username'],
        user_type="admin",
        message="Admin login successful",
        ip_disparity=ip_disparity_info.get('is_disparity', False)
    )


@app.post("/auth/register")
async def register_user_basic(request: UserRegisterRequest):
    """Register new user (basic, no OTP)."""
    user_id = create_user(request.username, request.email, request.phone, request.password)
    
    if not user_id:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    return {"success": True, "user_id": user_id, "message": "Registration successful"}


@app.post("/auth/register/enhanced")
async def register_user_enhanced(request: EnhancedRegisterRequest):
    """Register new user with full name (creates profile automatically)."""
    user_id = create_user(
        request.username, 
        request.email, 
        request.phone, 
        request.password,
        full_name=request.full_name
    )
    
    if not user_id:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    return {"success": True, "user_id": user_id, "message": "Registration successful. Profile created."}


# OTP Endpoints
@app.post("/auth/otp/send")
async def send_otp_endpoint(request: SendOTPRequest):
    """Send OTP to email using real email service."""
    from email_service import send_otp_email, is_email_configured
    
    # Generate OTP
    otp_code = generate_otp()
    
    # Save to database
    save_otp(request.email, otp_code, request.purpose)
    
    # Try to send real email
    if is_email_configured():
        email_sent = send_otp_email(request.email, otp_code, request.purpose)
        
        if email_sent:
            return {
                "success": True, 
                "message": f"OTP sent to {request.email}. Please check your inbox."
            }
        else:
            # Email failed but OTP is saved - return with demo fallback
            print(f"[OTP] Email failed. Fallback OTP: {otp_code}")
            return {
                "success": True, 
                "message": f"OTP generated (email delivery failed)",
                "demo_otp": otp_code  # Fallback for testing
            }
    else:
        # Email not configured - return demo OTP for development
        print(f"[OTP] Email not configured. Demo OTP: {otp_code} for {request.email}")
        return {
            "success": True, 
            "message": f"OTP generated (email not configured)",
            "demo_otp": otp_code,
            "email_configured": False
        }


@app.post("/auth/otp/verify")
async def verify_otp_endpoint(request: VerifyOTPRequest):
    """Verify OTP code."""
    is_valid = verify_otp(request.email, request.otp_code, request.purpose)
    
    if not is_valid:
        return {"success": False, "message": "Invalid or expired OTP"}
    
    return {"success": True, "message": "OTP verified successfully"}


@app.post("/auth/login/otp")
async def login_with_otp(request: OTPLoginRequest, req: Request):
    """Login using OTP instead of password."""
    
    # Validate CAPTCHA first
    if request.captcha_text and request.captcha_answer:
        if request.captcha_text.upper() != request.captcha_answer.upper():
            return LoginResponse(success=False, message="Invalid CAPTCHA. Please try again.")
    
    # Get user by username
    user = get_user_by_username(request.username)
    
    if not user:
        return LoginResponse(success=False, message="User not found")
    
    # Verify OTP
    is_valid = verify_otp(user.get('email', ''), request.otp_code, "login")
    
    if not is_valid:
        return LoginResponse(success=False, message="Invalid or expired OTP")
    
    # Get client IP
    client_ip = req.client.host if req.client else "Unknown"
    forwarded_for = req.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    # Save login history
    save_login_history(
        user['user_id'], 'user',
        typing_speed=0,
        form_completion_time=0,
        ip_address=client_ip,
        location="OTP Login"
    )
    
    return LoginResponse(
        success=True,
        user_id=user['user_id'],
        username=user['username'],
        user_type="user",
        message="OTP login successful"
    )


@app.get("/auth/profile-check/{user_id}")
async def check_profile_status(user_id: str, user_type: str = "user"):
    """Check if user/admin has completed their profile."""
    result = check_profile_complete(user_id, user_type)
    return result


class AdminRegisterRequest(BaseModel):
    username: str
    password: str
    security_code: str


@app.post("/auth/register/admin")
async def register_admin(request: AdminRegisterRequest):
    """Register new admin."""
    admin_id = create_admin(request.username, request.password, request.security_code)
    
    if not admin_id:
        raise HTTPException(status_code=400, detail="Admin username already exists")
    
    return {"success": True, "admin_id": admin_id, "message": "Admin registration successful"}


@app.get("/db/complaints/{user_id}")
async def get_complaints_for_user(user_id: str):
    """Get all complaints for a user."""
    complaints = get_user_complaints(user_id)
    return {"complaints": complaints}


@app.get("/db/complaints")
async def get_complaints_all(status: str = None, limit: int = 100):
    """Get all complaints (admin endpoint)."""
    complaints = get_all_complaints(status, limit)
    return {"complaints": complaints}


@app.post("/db/complaints/{complaint_id}/status")
async def update_status(complaint_id: str, status: str, note: str = None):
    """Update complaint status and notify user."""
    # Get the complaint to find the user_id
    complaints = get_all_complaints()
    complaint = next((c for c in complaints if c['complaint_id'] == complaint_id), None)
    
    success = update_complaint_status(complaint_id, status, note)
    if not success:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Create notification for the user
    if complaint:
        user_id = complaint.get('user_id')
        if user_id:
            message = f"Your complaint #{complaint_id} status has been updated to '{status}'."
            if note:
                message += f" Admin note: {note}"
            create_notification(
                message=message,
                notification_type="status_update",
                user_id=user_id,
                complaint_id=complaint_id
            )
    
    return {"success": True, "message": f"Status updated to {status}"}


@app.post("/db/complaints/{complaint_id}/nudge")
async def nudge_complaint(complaint_id: str):
    """Request urgent attention for a complaint."""
    # Create notification for admins
    try:
        create_notification(
            message=f"🔔 Urgent attention requested for complaint #{complaint_id}. Please review and take action.",
            notification_type="nudge",
            admin_id="all",
            complaint_id=complaint_id
        )
        return {"success": True, "message": "Urgent attention request sent"}
    except Exception as e:
        # Even if notification fails, return success to user
        return {"success": True, "message": "Request noted"}


@app.get("/db/stats", response_model=StatsResponse)
async def get_stats(timeframe: str = "all"):
    """Get complaint statistics."""
    stats = get_complaint_stats(timeframe)
    return StatsResponse(**stats)


@app.get("/db/complaints/{complaint_id}/similar")
async def get_similar_complaints(complaint_id: str, threshold: float = 0.6, limit: int = 5):
    """
    Find complaints similar to the given complaint using NLP similarity.
    Returns a list of similar complaints with similarity scores.
    """
    try:
        from database import get_db
        from similarity import find_similar_complaints
        
        conn = get_db()
        similar = find_similar_complaints(complaint_id, conn, threshold=threshold, limit=limit)
        conn.close()
        
        return {"similar": similar}
    except ImportError as e:
        # similarity module not available or sentence-transformers not installed
        return {"similar": [], "error": str(e)}
    except Exception as e:
        print(f"Error finding similar complaints: {e}")
        return {"similar": []}


@app.get("/db/notifications/user/{user_id}")
async def get_notifications_for_user(user_id: str, unread_only: bool = False):
    """Get notifications for a specific user."""
    notifications = get_user_notifications(user_id, unread_only)
    return {"notifications": notifications, "unread_count": len([n for n in notifications if not n.get('is_read')])}


@app.get("/db/notifications/admin")
async def get_notifications_for_admin(unread_only: bool = False):
    """Get notifications for admins (nudges, new complaints, etc)."""
    notifications = get_admin_notifications(unread_only)
    return {"notifications": notifications, "unread_count": len([n for n in notifications if not n.get('is_read')])}


@app.post("/db/notifications/{notification_id}/read")
async def mark_notification_as_read(notification_id: int):
    """Mark a notification as read."""
    from database import get_db
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE notifications SET is_read=1 WHERE id=?", (notification_id,))
    conn.commit()
    conn.close()
    return {"success": True}


@app.post("/complaint/submit")
async def submit_complaint(
    complaint: str = Form(...),
    user_id: str = Form(default="guest"),
    is_anonymous: str = Form(default="0"),
    pdf_file: Optional[UploadFile] = File(default=None),
    image_file: Optional[UploadFile] = File(default=None),
    audio_file: Optional[UploadFile] = File(default=None),
    video_file: Optional[UploadFile] = File(default=None)
):
    """
    Submit a complaint and save to database.
    Processes the complaint with AI and stores the result.
    """
    if not complaint.strip():
        raise HTTPException(status_code=400, detail="Complaint text is required")
    
    # Save uploaded files temporarily
    temp_dir = tempfile.mkdtemp()
    file_paths = {
        "pdf_path": None,
        "image_path": None,
        "audio_path": None,
        "video_path": None
    }
    
    try:
        # Save each uploaded file
        for key, upload_file in [
            ("pdf_path", pdf_file),
            ("image_path", image_file),
            ("audio_path", audio_file),
            ("video_path", video_file)
        ]:
            if upload_file:
                path = os.path.join(temp_dir, upload_file.filename)
                with open(path, "wb") as f:
                    shutil.copyfileobj(upload_file.file, f)
                file_paths[key] = path
        
        # Process complaint with AI
        result = summarize_complaint(
            complaint,
            pdf_path=file_paths["pdf_path"],
            image_path=file_paths["image_path"],
            audio_path=file_paths["audio_path"],
            video_path=file_paths["video_path"]
        )
        
        # Get incident details
        incident = result.get("incident_details", {})
        crime_type = incident.get("crime_type", "")
        if isinstance(crime_type, list):
            crime_type = ", ".join(crime_type)
        
        # Save to database with anonymous flag
        complaint_id = create_complaint(
            user_id=user_id,
            complaint_text=complaint,
            narrative_summary=result.get("narrative_summary", ""),
            incident_details=str(incident),
            crime_type=crime_type,
            financial_loss=incident.get("financial_loss_inr", 0),
            severity_score=result.get("severity_score", 0),
            severity_color=get_severity_color(result.get("severity_score", 0)),
            classification=result.get("classification", ""),
            pdf_path=file_paths.get("pdf_path", ""),
            image_path=file_paths.get("image_path", ""),
            audio_path=file_paths.get("audio_path", ""),
            video_path=file_paths.get("video_path", ""),
            is_anonymous=1 if is_anonymous in ("1", "true", "True") else 0
        )
        
        # Generate and save embedding for similar complaint detection
        try:
            from similarity import generate_embedding, save_complaint_embedding
            from database import get_db
            
            text_to_embed = result.get("narrative_summary", "") or complaint
            embedding = generate_embedding(text_to_embed)
            conn = get_db()
            save_complaint_embedding(complaint_id, embedding, conn)
            conn.close()
        except Exception as e:
            print(f"Error generating embedding: {e}")
        
        return {
            "success": True,
            "complaint_id": complaint_id,
            "message": "Complaint registered successfully"
        }
        
    finally:
        # Cleanup temp files
        for path in file_paths.values():
            if path and os.path.exists(path):
                os.remove(path)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/db/login-history")
async def get_login_history_all(user_type: str = None, limit: int = 100):
    """Get all login history for admin dashboard."""
    history = get_all_login_history(user_type, limit)
    return {"login_history": history}


# ============================================================================
# Profile Endpoints
# ============================================================================

@app.get("/profile/user/{user_id}")
async def get_user_profile_endpoint(user_id: str):
    """Get user profile."""
    profile = get_user_profile(user_id)
    return {"profile": profile, "exists": profile is not None}


@app.post("/profile/user/{user_id}")
async def update_user_profile_endpoint(user_id: str, request: UserProfileRequest):
    """Update user profile."""
    profile_id = create_or_update_user_profile(
        user_id,
        full_name=request.full_name,
        date_of_birth=request.date_of_birth,
        gender=request.gender,
        address=request.address,
        city=request.city,
        state=request.state,
        pincode=request.pincode,
        gov_id_type=request.gov_id_type,
        gov_id_number=request.gov_id_number
    )
    return {"success": True, "profile_id": profile_id}


@app.post("/profile/user/{user_id}/upload-id")
async def upload_user_gov_id(
    user_id: str,
    id_file: UploadFile = File(...)
):
    """Upload government ID for user verification."""
    # Create uploads directory
    upload_dir = os.path.join(API_DIR, "uploads", "gov_ids")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_ext = os.path.splitext(id_file.filename)[1]
    file_name = f"{user_id}_gov_id{file_ext}"
    file_path = os.path.join(upload_dir, file_name)
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(id_file.file, f)
    
    # Update profile with file path
    create_or_update_user_profile(user_id, gov_id_path=file_path)
    
    return {"success": True, "message": "ID uploaded successfully", "file_path": file_path}


@app.get("/profile/admin/{admin_id}")
async def get_admin_profile_endpoint(admin_id: str):
    """Get admin profile."""
    profile = get_admin_profile(admin_id)
    return {"profile": profile, "exists": profile is not None}


@app.post("/profile/admin/{admin_id}")
async def update_admin_profile_endpoint(admin_id: str, request: AdminProfileRequest):
    """Update admin profile."""
    profile_id = create_or_update_admin_profile(
        admin_id,
        full_name=request.full_name,
        designation=request.designation,
        department=request.department,
        office_address=request.office_address,
        employee_id=request.employee_id
    )
    return {"success": True, "profile_id": profile_id}


@app.post("/profile/admin/{admin_id}/upload-id")
async def upload_admin_professional_id(
    admin_id: str,
    id_file: UploadFile = File(...)
):
    """Upload professional ID for admin verification."""
    # Create uploads directory
    upload_dir = os.path.join(API_DIR, "uploads", "admin_ids")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_ext = os.path.splitext(id_file.filename)[1]
    file_name = f"{admin_id}_professional_id{file_ext}"
    file_path = os.path.join(upload_dir, file_name)
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(id_file.file, f)
    
    # Update profile with file path
    create_or_update_admin_profile(admin_id, professional_id_path=file_path)
    
    return {"success": True, "message": "ID uploaded successfully", "file_path": file_path}


# ============================================================================
# Complaint Deletion Endpoints
# ============================================================================

@app.delete("/db/complaints/{complaint_id}")
async def delete_complaint_endpoint(complaint_id: str, admin_id: str, request: DeleteComplaintRequest):
    """Delete a complaint (requires admin password and creates audit trail)."""
    
    # Verify admin's deletion password
    if not verify_admin_deletion_password(admin_id, request.deletion_password):
        raise HTTPException(status_code=403, detail="Invalid deletion password")
    
    # Delete the complaint
    success = db_delete_complaint(complaint_id, admin_id, request.reason)
    
    if not success:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    return {"success": True, "message": f"Complaint {complaint_id} deleted successfully"}


@app.get("/db/deletion-audit")
async def get_deletion_audit_endpoint(limit: int = 50):
    """Get deletion audit history (admin only)."""
    audit = get_deletion_audit(limit)
    return {"audit": audit}


@app.post("/admin/{admin_id}/update-deletion-password")
async def update_deletion_password_endpoint(admin_id: str, current_password: str, new_password: str):
    """Update admin's deletion password."""
    # Verify current password first
    if not verify_admin_deletion_password(admin_id, current_password):
        raise HTTPException(status_code=403, detail="Current password is incorrect")
    
    success = update_admin_deletion_password(admin_id, new_password)
    if not success:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    return {"success": True, "message": "Deletion password updated successfully"}


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

