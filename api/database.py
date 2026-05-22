# database.py - SQLite Database for Cybersecurity App
# Tables: users, admins, complaints, login_history, user_profiles, admin_profiles, deletion_audit

import sqlite3
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Database path - can be overridden by DB_PATH environment variable
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DB_PATH", os.path.join(_CURRENT_DIR, "cybersafe.db"))

# Indian Standard Time (IST) is UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))


def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format with Indian Standard Time (IST)."""
    return datetime.now(IST).isoformat()


def init_db():
    """Initialize database with all required tables."""
    conn = get_db()
    cur = conn.cursor()
    
    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Admins table with deletion_password
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            security_code TEXT NOT NULL,
            deletion_password TEXT DEFAULT 'delete123',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add deletion_password column if not exists
    try:
        cur.execute("ALTER TABLE admins ADD COLUMN deletion_password TEXT DEFAULT 'delete123'")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # User Profiles table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            profile_id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE NOT NULL,
            full_name TEXT,
            date_of_birth TEXT,
            gender TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            gov_id_type TEXT,
            gov_id_number TEXT,
            gov_id_path TEXT,
            is_verified INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """)
    
    # Admin Profiles table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_profiles (
            profile_id TEXT PRIMARY KEY,
            admin_id TEXT UNIQUE NOT NULL,
            full_name TEXT,
            designation TEXT,
            department TEXT,
            office_address TEXT,
            employee_id TEXT,
            professional_id_path TEXT,
            is_verified INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES admins (admin_id) ON DELETE CASCADE
        )
    """)
    
    # Deletion Audit table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deletion_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id TEXT NOT NULL,
            complaint_id TEXT NOT NULL,
            complaint_summary TEXT,
            reason TEXT,
            deleted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES admins (admin_id)
        )
    """)
    
    # Complaints table with cascade delete and is_anonymous flag
    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            complaint_text TEXT NOT NULL,
            narrative_summary TEXT,
            incident_details TEXT,
            crime_type TEXT,
            financial_loss REAL DEFAULT 0,
            severity_score REAL DEFAULT 0,
            severity_color TEXT DEFAULT 'yellow',
            classification TEXT,
            status TEXT DEFAULT 'pending',
            admin_note TEXT,
            has_contradiction INTEGER DEFAULT 0,
            similar_complaints TEXT,
            embedding BLOB,
            is_anonymous INTEGER DEFAULT 0,
            pdf_path TEXT,
            image_path TEXT,
            audio_path TEXT,
            video_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """)
    
    # Add is_anonymous column if not exists
    try:
        cur.execute("ALTER TABLE complaints ADD COLUMN is_anonymous INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Login history / behavior tracking with cascade delete and IP disparity tracking
    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            user_type TEXT DEFAULT 'user',
            login_time TEXT DEFAULT CURRENT_TIMESTAMP,
            typing_speed INTEGER DEFAULT 0,
            captcha_typing_speed INTEGER DEFAULT 0,
            form_completion_time INTEGER DEFAULT 0,
            typing_pattern TEXT,
            ip_address TEXT,
            location TEXT,
            vpn_detected INTEGER DEFAULT 0,
            device_fingerprint TEXT,
            risk_score REAL DEFAULT 0,
            is_anomaly INTEGER DEFAULT 0,
            anomaly_reasons TEXT,
            ip_disparity INTEGER DEFAULT 0,
            previous_ip TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """)
    
    # Add new columns if not exists
    for col, default in [("captcha_typing_speed", "0"), ("ip_disparity", "0"), ("previous_ip", "NULL")]:
        try:
            cur.execute(f"ALTER TABLE login_history ADD COLUMN {col} {'INTEGER DEFAULT ' + default if default != 'NULL' else 'TEXT'}")
        except sqlite3.OperationalError:
            pass
    
    # Notifications table with cascade delete
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            admin_id TEXT,
            complaint_id TEXT,
            message TEXT NOT NULL,
            notification_type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
            FOREIGN KEY (admin_id) REFERENCES admins (admin_id) ON DELETE CASCADE,
            FOREIGN KEY (complaint_id) REFERENCES complaints (complaint_id) ON DELETE CASCADE
        )
    """)
    
    # Create performance indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_complaints_user ON complaints(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_complaints_created ON complaints(created_at DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_complaints_severity ON complaints(severity_score DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_complaints_crime_type ON complaints(crime_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_login_history_user ON login_history(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_login_history_time ON login_history(login_time DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_login_history_type ON login_history(user_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_login_history_ip ON login_history(ip_address)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_admin ON notifications(admin_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_user_profiles_user ON user_profiles(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_admin_profiles_admin ON admin_profiles(admin_id)")
    
    # Insert default admin if not exists
    cur.execute("SELECT 1 FROM admins WHERE username='admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO admins (admin_id, username, password, security_code, deletion_password) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "admin", "admin123", "123456", "delete123")
        )
    
    # Insert admin2 if not exists
    cur.execute("SELECT 1 FROM admins WHERE username='admin2'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO admins (admin_id, username, password, security_code, deletion_password) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "admin2", "admin123", "123456", "delete123")
        )
    
    # Insert test user if not exists
    cur.execute("SELECT 1 FROM users WHERE username='test'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (user_id, username, email, phone, password) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), "test", "test@example.com", "9876543210", "test123")
        )
    
    # Add full_name column to users if not exists
    try:
        cur.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
    except sqlite3.OperationalError:
        pass
    
    # Create OTP table for email verification
    cur.execute("""
        CREATE TABLE IF NOT EXISTS otp_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            purpose TEXT DEFAULT 'verification',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT NOT NULL,
            is_used INTEGER DEFAULT 0
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")
    print("✓ Tables created (including user_profiles, admin_profiles, deletion_audit, otp_tokens)")
    print("✓ Indexes created for performance")
    print("✓ Anonymous complaint support added")
    print("✓ IP disparity tracking added")
    print("✓ Admin2 credentials added")


# ============================================================================
# User Operations
# ============================================================================

def create_user(username: str, email: str, phone: str, password: str, full_name: str = "") -> Optional[str]:
    """Create a new user. Returns user_id or None if failed."""
    conn = get_db()
    cur = conn.cursor()
    try:
        user_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO users (user_id, username, email, phone, password, full_name) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, email, phone, password, full_name)
        )
        conn.commit()
        
        # Auto-create profile with registration data
        if full_name or email or phone:
            cur.execute("""
                INSERT INTO user_profiles (profile_id, user_id, full_name)
                VALUES (?, ?, ?)
            """, (str(uuid.uuid4()), user_id, full_name))
            conn.commit()
        
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def create_admin(username: str, password: str, security_code: str) -> Optional[str]:
    """Create a new admin. Returns admin_id or None if failed."""
    conn = get_db()
    cur = conn.cursor()
    try:
        admin_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO admins (admin_id, username, password, security_code) VALUES (?, ?, ?, ?)",
            (admin_id, username, password, security_code)
        )
        conn.commit()
        return admin_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user. Returns user dict or None."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, username, email, phone FROM users WHERE username=? AND password=?",
        (username, password)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def authenticate_admin(username: str, password: str, security_code: str) -> Optional[Dict]:
    """Authenticate admin. Returns admin dict or None."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT admin_id, username FROM admins WHERE username=? AND password=? AND security_code=?",
        (username, password, security_code)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


# ============================================================================
# Complaint Operations
# ============================================================================

def create_complaint(user_id: str, complaint_text: str, **kwargs) -> str:
    """Create a new complaint. Returns complaint_id."""
    conn = get_db()
    cur = conn.cursor()
    
    complaint_id = f"CYB-{datetime.now(IST).strftime('%Y')}-{str(uuid.uuid4())[:8].upper()}"
    current_time = get_current_timestamp()  # IST timestamp
    
    cur.execute("""
        INSERT INTO complaints (
            complaint_id, user_id, complaint_text, narrative_summary, incident_details,
            crime_type, financial_loss, severity_score, severity_color, classification,
            status, pdf_path, image_path, audio_path, video_path, is_anonymous,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        complaint_id, user_id, complaint_text,
        kwargs.get('narrative_summary', ''),
        kwargs.get('incident_details', ''),
        kwargs.get('crime_type', ''),
        kwargs.get('financial_loss', 0),
        kwargs.get('severity_score', 0),
        kwargs.get('severity_color', 'yellow'),
        kwargs.get('classification', ''),
        'pending',
        kwargs.get('pdf_path', ''),
        kwargs.get('image_path', ''),
        kwargs.get('audio_path', ''),
        kwargs.get('video_path', ''),
        kwargs.get('is_anonymous', 0),
        current_time,
        current_time
    ))
    
    conn.commit()
    conn.close()
    return complaint_id


def get_user_complaints(user_id: str) -> List[Dict]:
    """Get all complaints for a user."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM complaints WHERE user_id=? ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_complaints(status: str = None, limit: int = 100) -> List[Dict]:
    """Get all complaints, optionally filtered by status."""
    conn = get_db()
    cur = conn.cursor()
    if status:
        cur.execute(
            "SELECT * FROM complaints WHERE status=? ORDER BY severity_score DESC, created_at DESC LIMIT ?",
            (status, limit)
        )
    else:
        cur.execute(
            "SELECT * FROM complaints ORDER BY severity_score DESC, created_at DESC LIMIT ?",
            (limit,)
        )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_complaint_status(complaint_id: str, status: str, admin_note: str = None) -> bool:
    """Update complaint status. Returns success."""
    conn = get_db()
    cur = conn.cursor()
    current_time = get_current_timestamp()  # IST timestamp
    if admin_note:
        cur.execute(
            "UPDATE complaints SET status=?, admin_note=?, updated_at=? WHERE complaint_id=?",
            (status, admin_note, current_time, complaint_id)
        )
    else:
        cur.execute(
            "UPDATE complaints SET status=?, updated_at=? WHERE complaint_id=?",
            (status, current_time, complaint_id)
        )
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return affected > 0


def get_complaint_stats(timeframe: str = 'all') -> Dict:
    """Get complaint statistics."""
    conn = get_db()
    cur = conn.cursor()
    
    # Build date filter
    date_filter = ""
    if timeframe == 'month':
        date_filter = "AND created_at >= datetime('now', '-1 month')"
    elif timeframe == '2months':
        date_filter = "AND created_at >= datetime('now', '-2 months')"
    elif timeframe == '6months':
        date_filter = "AND created_at >= datetime('now', '-6 months')"
    elif timeframe == 'year':
        date_filter = "AND created_at >= datetime('now', '-1 year')"
    
    # Total
    cur.execute(f"SELECT COUNT(*) as count FROM complaints WHERE 1=1 {date_filter}")
    total = cur.fetchone()['count']
    
    # By status
    cur.execute(f"SELECT COUNT(*) as count FROM complaints WHERE status='pending' {date_filter}")
    pending = cur.fetchone()['count']
    
    cur.execute(f"SELECT COUNT(*) as count FROM complaints WHERE status='ongoing' {date_filter}")
    ongoing = cur.fetchone()['count']
    
    cur.execute(f"SELECT COUNT(*) as count FROM complaints WHERE status='solved' {date_filter}")
    solved = cur.fetchone()['count']
    
    conn.close()
    
    return {
        'total': total,
        'pending': pending,
        'ongoing': ongoing,
        'solved': solved
    }


# ============================================================================
# Login History Operations
# ============================================================================

def save_login_history(user_id: str, user_type: str, **kwargs) -> int:
    """Save login attempt with behavior data. Returns id."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO login_history (
            user_id, user_type, login_time, typing_speed, captcha_typing_speed,
            form_completion_time, typing_pattern, ip_address, location, vpn_detected,
            device_fingerprint, risk_score, is_anomaly, anomaly_reasons,
            ip_disparity, previous_ip
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, user_type,
        get_current_timestamp(),
        kwargs.get('typing_speed', 0),
        kwargs.get('captcha_typing_speed', 0),
        kwargs.get('form_completion_time', 0),
        kwargs.get('typing_pattern', ''),
        kwargs.get('ip_address', ''),
        kwargs.get('location', ''),
        kwargs.get('vpn_detected', 0),
        kwargs.get('device_fingerprint', ''),
        kwargs.get('risk_score', 0),
        kwargs.get('is_anomaly', 0),
        kwargs.get('anomaly_reasons', ''),
        kwargs.get('ip_disparity', 0),
        kwargs.get('previous_ip', '')
    ))
    
    conn.commit()
    login_id = cur.lastrowid
    conn.close()
    return login_id


def get_user_login_history(user_id: str, limit: int = 20) -> List[Dict]:
    """Get login history for a user."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM login_history WHERE user_id=? ORDER BY login_time DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_login_history(user_type: str = None, limit: int = 100) -> List[Dict]:
    """Get all login history for admin view."""
    conn = get_db()
    cur = conn.cursor()
    
    if user_type:
        cur.execute(
            """SELECT lh.*, u.username as user_name, u.email as user_email 
               FROM login_history lh 
               LEFT JOIN users u ON lh.user_id = u.user_id 
               WHERE lh.user_type = ?
               ORDER BY lh.login_time DESC LIMIT ?""",
            (user_type, limit)
        )
    else:
        cur.execute(
            """SELECT lh.*, 
                      COALESCE(u.username, a.username) as user_name,
                      COALESCE(u.email, 'admin@cybersafe.com') as user_email
               FROM login_history lh 
               LEFT JOIN users u ON lh.user_id = u.user_id AND lh.user_type = 'user'
               LEFT JOIN admins a ON lh.user_id = a.admin_id AND lh.user_type = 'admin'
               ORDER BY lh.login_time DESC LIMIT ?""",
            (limit,)
        )
    
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ============================================================================
# Notification Operations
# ============================================================================

def create_notification(message: str, notification_type: str = 'info', **kwargs) -> int:
    """Create a notification."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO notifications (user_id, admin_id, complaint_id, message, notification_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        kwargs.get('user_id'),
        kwargs.get('admin_id'),
        kwargs.get('complaint_id'),
        message,
        notification_type,
        get_current_timestamp()  # IST timestamp
    ))
    
    conn.commit()
    notif_id = cur.lastrowid
    conn.close()
    return notif_id


def get_user_notifications(user_id: str, unread_only: bool = False) -> List[Dict]:
    """Get notifications for a user."""
    conn = get_db()
    cur = conn.cursor()
    
    query = "SELECT * FROM notifications WHERE user_id=?"
    if unread_only:
        query += " AND is_read=0"
    query += " ORDER BY created_at DESC LIMIT 50"
    
    cur.execute(query, (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_admin_notifications(unread_only: bool = False) -> List[Dict]:
    """Get notifications for admins."""
    conn = get_db()
    cur = conn.cursor()
    
    query = "SELECT * FROM notifications WHERE admin_id IS NOT NULL OR notification_type='new_complaint'"
    if unread_only:
        query += " AND is_read=0"
    query += " ORDER BY created_at DESC LIMIT 50"
    
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ============================================================================
# Profile Operations
# ============================================================================

def get_user_profile(user_id: str) -> Optional[Dict]:
    """Get user profile by user_id."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_profiles WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def create_or_update_user_profile(user_id: str, **kwargs) -> str:
    """Create or update user profile. Returns profile_id."""
    conn = get_db()
    cur = conn.cursor()
    
    # Check if profile exists
    cur.execute("SELECT profile_id FROM user_profiles WHERE user_id=?", (user_id,))
    existing = cur.fetchone()
    
    if existing:
        # Update existing profile
        fields = []
        values = []
        for key, value in kwargs.items():
            if key not in ['profile_id', 'user_id', 'created_at']:
                fields.append(f"{key}=?")
                values.append(value)
        
        if fields:
            fields.append("updated_at=?")
            values.append(get_current_timestamp())
            values.append(user_id)
            cur.execute(f"UPDATE user_profiles SET {', '.join(fields)} WHERE user_id=?", values)
        
        profile_id = existing[0]
    else:
        # Create new profile
        profile_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO user_profiles (profile_id, user_id, full_name, date_of_birth, gender, 
                address, city, state, pincode, gov_id_type, gov_id_number, gov_id_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile_id, user_id,
            kwargs.get('full_name', ''),
            kwargs.get('date_of_birth', ''),
            kwargs.get('gender', ''),
            kwargs.get('address', ''),
            kwargs.get('city', ''),
            kwargs.get('state', ''),
            kwargs.get('pincode', ''),
            kwargs.get('gov_id_type', ''),
            kwargs.get('gov_id_number', ''),
            kwargs.get('gov_id_path', '')
        ))
    
    conn.commit()
    conn.close()
    return profile_id


def get_admin_profile(admin_id: str) -> Optional[Dict]:
    """Get admin profile by admin_id."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM admin_profiles WHERE admin_id=?", (admin_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def create_or_update_admin_profile(admin_id: str, **kwargs) -> str:
    """Create or update admin profile. Returns profile_id."""
    conn = get_db()
    cur = conn.cursor()
    
    # Check if profile exists
    cur.execute("SELECT profile_id FROM admin_profiles WHERE admin_id=?", (admin_id,))
    existing = cur.fetchone()
    
    if existing:
        # Update existing profile
        fields = []
        values = []
        for key, value in kwargs.items():
            if key not in ['profile_id', 'admin_id', 'created_at']:
                fields.append(f"{key}=?")
                values.append(value)
        
        if fields:
            fields.append("updated_at=?")
            values.append(get_current_timestamp())
            values.append(admin_id)
            cur.execute(f"UPDATE admin_profiles SET {', '.join(fields)} WHERE admin_id=?", values)
        
        profile_id = existing[0]
    else:
        # Create new profile
        profile_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO admin_profiles (profile_id, admin_id, full_name, designation, 
                department, office_address, employee_id, professional_id_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile_id, admin_id,
            kwargs.get('full_name', ''),
            kwargs.get('designation', ''),
            kwargs.get('department', ''),
            kwargs.get('office_address', ''),
            kwargs.get('employee_id', ''),
            kwargs.get('professional_id_path', '')
        ))
    
    conn.commit()
    conn.close()
    return profile_id


# ============================================================================
# Complaint Deletion Operations
# ============================================================================

def verify_admin_deletion_password(admin_id: str, deletion_password: str) -> bool:
    """Verify admin's deletion password."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT deletion_password FROM admins WHERE admin_id=?", (admin_id,))
    row = cur.fetchone()
    conn.close()
    
    if row and row[0] == deletion_password:
        return True
    return False


def delete_complaint(complaint_id: str, admin_id: str, reason: str = "") -> bool:
    """Delete a complaint and create audit trail. Returns success."""
    conn = get_db()
    cur = conn.cursor()
    
    # Get complaint summary before deletion
    cur.execute("SELECT narrative_summary, complaint_text FROM complaints WHERE complaint_id=?", (complaint_id,))
    complaint_row = cur.fetchone()
    
    if not complaint_row:
        conn.close()
        return False
    
    complaint_summary = complaint_row[0] or complaint_row[1][:200]
    
    # Create audit trail
    cur.execute("""
        INSERT INTO deletion_audit (admin_id, complaint_id, complaint_summary, reason, deleted_at)
        VALUES (?, ?, ?, ?, ?)
    """, (admin_id, complaint_id, complaint_summary, reason, get_current_timestamp()))
    
    # Delete the complaint (notifications will cascade)
    cur.execute("DELETE FROM complaints WHERE complaint_id=?", (complaint_id,))
    affected = cur.rowcount
    
    conn.commit()
    conn.close()
    return affected > 0


def get_deletion_audit(limit: int = 50) -> List[Dict]:
    """Get deletion audit history."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT da.*, a.username as admin_name 
        FROM deletion_audit da 
        LEFT JOIN admins a ON da.admin_id = a.admin_id
        ORDER BY da.deleted_at DESC LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ============================================================================
# IP Disparity Detection
# ============================================================================

def get_user_previous_ip(user_id: str) -> Optional[str]:
    """Get the most recent IP address for a user."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT ip_address FROM login_history 
        WHERE user_id=? AND ip_address IS NOT NULL AND ip_address != ''
        ORDER BY login_time DESC LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    return None


def check_ip_disparity(user_id: str, current_ip: str) -> Dict:
    """Check if current IP differs from user's previous IPs."""
    conn = get_db()
    cur = conn.cursor()
    
    # Get all unique IPs for this user
    cur.execute("""
        SELECT DISTINCT ip_address FROM login_history 
        WHERE user_id=? AND ip_address IS NOT NULL AND ip_address != ''
        ORDER BY login_time DESC LIMIT 10
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()
    
    previous_ips = [row[0] for row in rows]
    
    if not previous_ips:
        return {"is_disparity": False, "message": "First login - no previous IP"}
    
    if current_ip in previous_ips:
        return {"is_disparity": False, "message": "IP matches previous logins"}
    
    return {
        "is_disparity": True,
        "message": f"New IP detected. Previous: {previous_ips[0]}",
        "previous_ip": previous_ips[0],
        "all_previous_ips": previous_ips[:5]
    }


def update_admin_deletion_password(admin_id: str, new_password: str) -> bool:
    """Update admin's deletion password."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE admins SET deletion_password=? WHERE admin_id=?", (new_password, admin_id))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def get_complaint_by_id(complaint_id: str) -> Optional[Dict]:
    """Get a single complaint by ID."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM complaints WHERE complaint_id=?", (complaint_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


# ============================================================================
# OTP Operations
# ============================================================================

import random
import string

def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=6))


def save_otp(email: str, otp_code: str, purpose: str = "verification", expires_minutes: int = 10) -> int:
    """Save OTP to database. Returns OTP id."""
    conn = get_db()
    cur = conn.cursor()
    
    # Calculate expiry time in IST
    current_time = datetime.now(IST)
    expires_at = current_time + timedelta(minutes=expires_minutes)
    
    cur.execute("""
        INSERT INTO otp_tokens (email, otp_code, purpose, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?)
    """, (email, otp_code, purpose, current_time.isoformat(), expires_at.isoformat()))
    
    conn.commit()
    otp_id = cur.lastrowid
    conn.close()
    return otp_id


def verify_otp(email: str, otp_code: str, purpose: str = "verification") -> bool:
    """Verify OTP. Returns True if valid."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, expires_at FROM otp_tokens 
        WHERE email=? AND otp_code=? AND purpose=? AND is_used=0
        ORDER BY created_at DESC LIMIT 1
    """, (email, otp_code, purpose))
    
    row = cur.fetchone()
    
    if not row:
        conn.close()
        return False
    
    # Check if expired (compare in IST)
    try:
        expires_at = datetime.fromisoformat(row['expires_at'])
        # If expires_at doesn't have timezone info, assume IST
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=IST)
        if datetime.now(IST) > expires_at:
            conn.close()
            return False
    except:
        conn.close()
        return False
    
    # Mark as used
    cur.execute("UPDATE otp_tokens SET is_used=1 WHERE id=?", (row['id'],))
    conn.commit()
    conn.close()
    return True


def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def check_profile_complete(user_id: str, user_type: str = "user") -> Dict:
    """Check if user/admin has completed their profile with required ID."""
    conn = get_db()
    cur = conn.cursor()
    
    if user_type == "admin":
        cur.execute("SELECT * FROM admin_profiles WHERE admin_id=?", (user_id,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return {"complete": False, "missing": ["profile"]}
        
        profile = dict(row)
        missing = []
        if not profile.get('full_name'):
            missing.append("full_name")
        if not profile.get('professional_id_path'):
            missing.append("professional_id")
        
        return {"complete": len(missing) == 0, "missing": missing}
    else:
        cur.execute("SELECT * FROM user_profiles WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return {"complete": False, "missing": ["profile"]}
        
        profile = dict(row)
        missing = []
        if not profile.get('full_name'):
            missing.append("full_name")
        if not profile.get('gov_id_path'):
            missing.append("gov_id")
        
        return {"complete": len(missing) == 0, "missing": missing}


# Initialize database on import
if __name__ == "__main__":
    init_db()
    print("Database tables created successfully!")
    
    # Show stats
    stats = get_complaint_stats()
    print(f"Current stats: {stats}")
