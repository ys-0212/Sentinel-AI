// API Client for CyberSafe
// API Base URL from environment variable (set in .env file)
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Types
export interface User {
    user_id: string;
    username: string;
    email?: string;
    phone?: string;
}

export interface LoginResponse {
    success: boolean;
    user_id?: string;
    username?: string;
    user_type: string;
    message: string;
    risk_score?: number;
    is_anomaly?: boolean;
}

export interface Complaint {
    complaint_id: string;
    user_id: string;
    complaint_text: string;
    narrative_summary?: string;
    incident_details?: string;
    crime_type?: string;
    financial_loss?: number;
    severity_score?: number;
    severity_color?: string;
    classification?: string;
    status: 'pending' | 'ongoing' | 'solved';
    admin_note?: string;
    similar_complaints?: string;
    created_at: string;
    updated_at: string;
}

export interface Stats {
    total: number;
    pending: number;
    ongoing: number;
    solved: number;
}

export interface Notification {
    id: number;
    user_id?: string;
    admin_id?: string;
    complaint_id?: string;
    message: string;
    notification_type: string;
    is_read: boolean;
    created_at: string;
}

export interface SimilarComplaint {
    complaint_id: string;
    similarity_score: number;
    crime_type?: string;
    narrative_summary?: string;
    status: string;
}

export interface LoginHistory {
    id: number;
    user_id: string;
    user_type: string;
    login_time: string;
    typing_speed: number;
    captcha_typing_speed?: number;
    form_completion_time: number;
    ip_address?: string;
    location?: string;
    vpn_detected: boolean;
    device_fingerprint?: string;
    risk_score: number;
    is_anomaly: boolean;
    anomaly_reasons?: string;
    user_name?: string;
    ip_disparity?: boolean;
    previous_ip?: string;
}

export interface UserProfile {
    profile_id?: string;
    user_id: string;
    full_name?: string;
    date_of_birth?: string;
    gender?: string;
    address?: string;
    city?: string;
    state?: string;
    pincode?: string;
    gov_id_type?: string;
    gov_id_number?: string;
    gov_id_path?: string;
    is_verified?: boolean;
}

export interface AdminProfile {
    profile_id?: string;
    admin_id: string;
    full_name?: string;
    designation?: string;
    department?: string;
    office_address?: string;
    employee_id?: string;
    professional_id_path?: string;
    is_verified?: boolean;
}

// Generic API call function
async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            ...options.headers,
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || 'API Error');
    }

    return response.json();
}

// Auth APIs
export async function loginUser(
    username: string,
    password: string,
    typingSpeed: number = 0,
    formCompletionTime: number = 0,
    typingPattern: string = '',
    captchaText: string = '',
    captchaAnswer: string = '',
    captchaTypingSpeed: number = 0
): Promise<LoginResponse> {
    return apiCall('/auth/login/user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username,
            password,
            typing_speed: typingSpeed,
            form_completion_time: formCompletionTime,
            typing_pattern: typingPattern,
            captcha_text: captchaText,
            captcha_answer: captchaAnswer,
            captcha_typing_speed: captchaTypingSpeed,
        }),
    });
}

export async function loginAdmin(
    username: string,
    password: string,
    securityCode: string,
    typingSpeed: number = 0,
    formCompletionTime: number = 0,
    captchaText: string = '',
    captchaAnswer: string = '',
    captchaTypingSpeed: number = 0
): Promise<LoginResponse> {
    return apiCall('/auth/login/admin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username,
            password,
            security_code: securityCode,
            typing_speed: typingSpeed,
            form_completion_time: formCompletionTime,
            captcha_text: captchaText,
            captcha_answer: captchaAnswer,
            captcha_typing_speed: captchaTypingSpeed,
        }),
    });
}

export async function registerUser(
    username: string,
    email: string,
    phone: string,
    password: string
): Promise<{ success: boolean; user_id: string; message: string }> {
    return apiCall('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, phone, password }),
    });
}

export async function registerUserEnhanced(
    fullName: string,
    username: string,
    email: string,
    phone: string,
    password: string
): Promise<{ success: boolean; user_id: string; message: string }> {
    return apiCall('/auth/register/enhanced', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: fullName, username, email, phone, password }),
    });
}

// OTP APIs
export async function sendOTP(email: string, purpose: string = 'verification'): Promise<{ 
    success: boolean; 
    message: string; 
    demo_otp?: string;  // Only in demo mode
}> {
    return apiCall('/auth/otp/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, purpose }),
    });
}

export async function verifyOTP(email: string, otpCode: string, purpose: string = 'verification'): Promise<{ 
    success: boolean; 
    message: string; 
}> {
    return apiCall('/auth/otp/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp_code: otpCode, purpose }),
    });
}

export async function loginWithOTP(
    username: string,
    otpCode: string,
    captchaText: string = '',
    captchaAnswer: string = ''
): Promise<LoginResponse> {
    return apiCall('/auth/login/otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            username, 
            otp_code: otpCode,
            captcha_text: captchaText,
            captcha_answer: captchaAnswer
        }),
    });
}

export async function checkProfileComplete(userId: string, userType: string = 'user'): Promise<{
    complete: boolean;
    missing: string[];
}> {
    return apiCall(`/auth/profile-check/${userId}?user_type=${userType}`);
}

// Complaint APIs
export async function submitComplaint(
    complaintText: string,
    userId: string,
    files: { pdf?: File; image?: File; audio?: File; video?: File } = {}
): Promise<{ success: boolean; complaint_id: string; message: string }> {
    const formData = new FormData();
    formData.append('complaint', complaintText);
    formData.append('user_id', userId);

    if (files.pdf) formData.append('pdf_file', files.pdf);
    if (files.image) formData.append('image_file', files.image);
    if (files.audio) formData.append('audio_file', files.audio);
    if (files.video) formData.append('video_file', files.video);

    return apiCall('/complaint/submit', {
        method: 'POST',
        body: formData,
    });
}

export async function getUserComplaints(userId: string): Promise<{ complaints: Complaint[] }> {
    return apiCall(`/db/complaints/${userId}`);
}

export async function getAllComplaints(
    status?: string,
    limit: number = 100
): Promise<{ complaints: Complaint[] }> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());
    return apiCall(`/db/complaints?${params}`);
}

export async function updateComplaintStatus(
    complaintId: string,
    status: string,
    note?: string
): Promise<{ success: boolean; message: string }> {
    const params = new URLSearchParams({ status });
    if (note) params.append('note', note);
    return apiCall(`/db/complaints/${complaintId}/status?${params}`, { method: 'POST' });
}

export async function nudgeComplaint(complaintId: string): Promise<{ success: boolean; message: string }> {
    return apiCall(`/db/complaints/${complaintId}/nudge`, { method: 'POST' });
}

export async function getSimilarComplaints(complaintId: string): Promise<{ similar: SimilarComplaint[] }> {
    return apiCall(`/db/complaints/${complaintId}/similar`);
}

// Stats API
export async function getStats(timeframe: string = 'all'): Promise<Stats> {
    return apiCall(`/db/stats?timeframe=${timeframe}`);
}

// Notification APIs
export async function getUserNotifications(
    userId: string,
    unreadOnly: boolean = false
): Promise<{ notifications: Notification[]; unread_count: number }> {
    return apiCall(`/db/notifications/user/${userId}?unread_only=${unreadOnly}`);
}

export async function getAdminNotifications(
    unreadOnly: boolean = false
): Promise<{ notifications: Notification[]; unread_count: number }> {
    return apiCall(`/db/notifications/admin?unread_only=${unreadOnly}`);
}

export async function markNotificationRead(notificationId: number): Promise<{ success: boolean }> {
    return apiCall(`/db/notifications/${notificationId}/read`, { method: 'POST' });
}

// Login History API
export async function getLoginHistory(
    userType?: string,
    limit: number = 100
): Promise<{ login_history: LoginHistory[] }> {
    const params = new URLSearchParams();
    if (userType) params.append('user_type', userType);
    params.append('limit', limit.toString());
    return apiCall(`/db/login-history?${params}`);
}

// Malicious Text Detector API
export async function analyzeMaliciousText(text: string): Promise<{
    threat_score: number;
    intent_classification: string;
    social_tactics_detected: string[];
    ioc_detected: string[];
    summary: string;
}> {
    return apiCall('/malicious/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
    });
}

// Call Scam Detector APIs
export async function analyzeScamText(text: string): Promise<{
    classification: string;
    reason: string;
}> {
    return apiCall('/call-scam/analyze-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
    });
}

export async function analyzeScamAudio(file: File, language: string = 'en'): Promise<{
    transcript?: string;
    language?: string;
    classification: string;
    reason: string;
}> {
    const formData = new FormData();
    formData.append('audio_file', file);
    formData.append('language', language);
    return apiCall('/call-scam/analyze-audio', {
        method: 'POST',
        body: formData,
    });
}

// Chatbot API
export async function queryChatbot(question: string): Promise<{
    answer: string;
    source_type: string;
    sources: string[];
}> {
    return apiCall('/chatbot/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
    });
}

// Profile APIs
export async function getUserProfile(userId: string): Promise<{ profile: UserProfile | null; exists: boolean }> {
    return apiCall(`/profile/user/${userId}`);
}

export async function updateUserProfile(userId: string, profile: Partial<UserProfile>): Promise<{ success: boolean; profile_id: string }> {
    return apiCall(`/profile/user/${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
    });
}

export async function uploadUserGovId(userId: string, file: File): Promise<{ success: boolean; message: string; file_path: string }> {
    const formData = new FormData();
    formData.append('id_file', file);
    return apiCall(`/profile/user/${userId}/upload-id`, {
        method: 'POST',
        body: formData,
    });
}

export async function getAdminProfile(adminId: string): Promise<{ profile: AdminProfile | null; exists: boolean }> {
    return apiCall(`/profile/admin/${adminId}`);
}

export async function updateAdminProfile(adminId: string, profile: Partial<AdminProfile>): Promise<{ success: boolean; profile_id: string }> {
    return apiCall(`/profile/admin/${adminId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
    });
}

export async function uploadAdminProfessionalId(adminId: string, file: File): Promise<{ success: boolean; message: string; file_path: string }> {
    const formData = new FormData();
    formData.append('id_file', file);
    return apiCall(`/profile/admin/${adminId}/upload-id`, {
        method: 'POST',
        body: formData,
    });
}

// Complaint Deletion API
export async function deleteComplaint(
    complaintId: string,
    adminId: string,
    deletionPassword: string,
    reason: string = ''
): Promise<{ success: boolean; message: string }> {
    return apiCall(`/db/complaints/${complaintId}?admin_id=${adminId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ deletion_password: deletionPassword, reason }),
    });
}

export async function getDeletionAudit(limit: number = 50): Promise<{ audit: Array<{
    id: number;
    admin_id: string;
    complaint_id: string;
    complaint_summary: string;
    reason: string;
    deleted_at: string;
    admin_name?: string;
}> }> {
    return apiCall(`/db/deletion-audit?limit=${limit}`);
}

// Complaint Submission with Anonymous Option
export async function submitComplaintAnonymous(
    complaintText: string,
    userId: string,
    isAnonymous: boolean = false,
    files: { pdf?: File; image?: File; audio?: File; video?: File } = {}
): Promise<{ success: boolean; complaint_id: string; message: string }> {
    const formData = new FormData();
    formData.append('complaint', complaintText);
    formData.append('user_id', userId);
    formData.append('is_anonymous', isAnonymous ? '1' : '0');

    if (files.pdf) formData.append('pdf_file', files.pdf);
    if (files.image) formData.append('image_file', files.image);
    if (files.audio) formData.append('audio_file', files.audio);
    if (files.video) formData.append('video_file', files.video);

    return apiCall('/complaint/submit', {
        method: 'POST',
        body: formData,
    });
}

// Utility functions
export function formatDate(dateString: string): string {
    if (!dateString) return 'N/A';
    // Parse the date string - handle both ISO format and SQLite format
    const date = new Date(dateString);
    // Check if valid date
    if (isNaN(date.getTime())) return dateString;
    
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Kolkata', // IST timezone
    });
}

export function getSeverityColor(score: number): string {
    if (score >= 4) return '#dc3545';
    if (score >= 3) return '#fd7e14';
    if (score >= 2) return '#ffc107';
    return '#198754';
}

export function getStatusClass(status: string): string {
    switch (status) {
        case 'solved': return 'badge-solved';
        case 'ongoing': return 'badge-ongoing';
        default: return 'badge-pending';
    }
}

// CAPTCHA Generator
export function generateCaptcha(): string {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let captcha = '';
    for (let i = 0; i < 6; i++) {
        captcha += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return captcha;
}
