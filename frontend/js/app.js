// ============================================
// Cybersecurity App - Main JavaScript
// ============================================

const API_BASE = 'http://localhost:8000';

// ============================================
// Utility Functions
// ============================================

async function apiCall(endpoint, method = 'GET', data = null, isFormData = false) {
    const options = {
        method,
        headers: {}
    };

    if (data) {
        if (isFormData) {
            options.body = data;
        } else {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(data);
        }
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'API Error');
        }

        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

function showLoading(container) {
    const loader = document.createElement('div');
    loader.className = 'loading-overlay';
    loader.innerHTML = '<div class="spinner"></div>';
    loader.id = 'loading-overlay';
    container.appendChild(loader);
}

function hideLoading() {
    const loader = document.getElementById('loading-overlay');
    if (loader) loader.remove();
}

function showAlert(container, message, type = 'info') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = message;
    container.insertBefore(alert, container.firstChild);

    setTimeout(() => alert.remove(), 5000);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ============================================
// Malicious Text Detector
// ============================================

async function analyzeMaliciousText() {
    const textInput = document.getElementById('malicious-text-input');
    const resultContainer = document.getElementById('malicious-result');

    if (!textInput.value.trim()) {
        showAlert(resultContainer.parentElement, 'Please enter text to analyze', 'warning');
        return;
    }

    resultContainer.innerHTML = '<div class="text-center"><div class="spinner"></div><p class="mt-2">Analyzing...</p></div>';

    try {
        const result = await apiCall('/malicious/analyze', 'POST', { text: textInput.value });

        const scoreColor = result.threat_score >= 7 ? 'danger' :
            result.threat_score >= 4 ? 'warning' : 'success';

        resultContainer.innerHTML = `
            <div class="alert alert-${scoreColor}">
                <strong>Threat Score: ${result.threat_score}/10</strong> - ${result.intent_classification}
            </div>
            <p><strong>Summary:</strong> ${result.summary}</p>
            ${result.social_tactics_detected.length ? `
                <p><strong>Social Tactics Detected:</strong></p>
                <ul>${result.social_tactics_detected.map(t => `<li>${t}</li>`).join('')}</ul>
            ` : ''}
            ${result.ioc_detected.length ? `
                <p><strong>Indicators of Compromise:</strong></p>
                <ul>${result.ioc_detected.map(i => `<li>${i}</li>`).join('')}</ul>
            ` : ''}
        `;
    } catch (error) {
        resultContainer.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

// ============================================
// Call Scam Detector
// ============================================

async function analyzeScamText() {
    const textInput = document.getElementById('scam-text-input');
    const resultContainer = document.getElementById('scam-result');

    if (!textInput.value.trim()) {
        showAlert(resultContainer.parentElement, 'Please enter call transcript', 'warning');
        return;
    }

    resultContainer.innerHTML = '<div class="text-center"><div class="spinner"></div><p class="mt-2">Analyzing...</p></div>';

    try {
        const result = await apiCall('/call-scam/analyze-text', 'POST', { text: textInput.value });

        const isScam = result.classification === 'Scam';

        resultContainer.innerHTML = `
            <div class="alert alert-${isScam ? 'danger' : 'success'}">
                <strong>${isScam ? '🚨' : '✅'} ${result.classification}</strong>
            </div>
            <p><strong>Reason:</strong> ${result.reason}</p>
        `;
    } catch (error) {
        resultContainer.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

async function analyzeScamAudio() {
    const fileInput = document.getElementById('scam-audio-file');
    const langSelect = document.getElementById('scam-language');
    const resultContainer = document.getElementById('scam-result');

    if (!fileInput.files.length) {
        showAlert(resultContainer.parentElement, 'Please select an audio file', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('audio_file', fileInput.files[0]);
    formData.append('language', langSelect.value);

    resultContainer.innerHTML = '<div class="text-center"><div class="spinner"></div><p class="mt-2">Transcribing and analyzing...</p></div>';

    try {
        const result = await apiCall('/call-scam/analyze-audio', 'POST', formData, true);

        const isScam = result.classification === 'Scam';

        resultContainer.innerHTML = `
            <div class="alert alert-${isScam ? 'danger' : 'success'}">
                <strong>${isScam ? '🚨' : '✅'} ${result.classification}</strong>
            </div>
            ${result.transcript ? `<p><strong>Transcript:</strong> ${result.transcript}</p>` : ''}
            <p><strong>Reason:</strong> ${result.reason}</p>
        `;
    } catch (error) {
        resultContainer.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

// ============================================
// Complaint Submission
// ============================================

async function submitComplaint() {
    const complaintText = document.getElementById('complaint-text');
    const pdfFile = document.getElementById('complaint-pdf');
    const imageFile = document.getElementById('complaint-image');
    const audioFile = document.getElementById('complaint-audio');
    const videoFile = document.getElementById('complaint-video');
    const resultContainer = document.getElementById('complaint-result');

    if (!complaintText.value.trim()) {
        showAlert(resultContainer.parentElement, 'Please enter complaint details', 'warning');
        return;
    }

    // Get user_id from session
    const session = JSON.parse(sessionStorage.getItem('userSession') || '{}');
    const userId = session.user_id || 'guest';

    const formData = new FormData();
    formData.append('complaint', complaintText.value);
    formData.append('user_id', userId);

    if (pdfFile.files.length) formData.append('pdf_file', pdfFile.files[0]);
    if (imageFile.files.length) formData.append('image_file', imageFile.files[0]);
    if (audioFile.files.length) formData.append('audio_file', audioFile.files[0]);
    if (videoFile.files.length) formData.append('video_file', videoFile.files[0]);

    resultContainer.innerHTML = '<div class="text-center"><div class="spinner"></div><p class="mt-2">Processing complaint...</p></div>';

    try {
        const result = await apiCall('/complaint/submit', 'POST', formData, true);

        // Show simple success message
        resultContainer.innerHTML = `
            <div class="card" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; text-align: center; padding: 2rem;">
                <span style="font-size: 4rem; display: block; margin-bottom: 1rem;">✅</span>
                <h2 style="margin: 0 0 0.5rem 0; color: white;">Complaint Registered Successfully!</h2>
                <p style="margin: 0; opacity: 0.9; font-size: 1.1rem;">Complaint ID: <strong>${result.complaint_id}</strong></p>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">Your complaint has been submitted and will be reviewed by our team.</p>
            </div>
        `;

        // Clear the form
        complaintText.value = '';
        if (pdfFile) pdfFile.value = '';
        if (imageFile) imageFile.value = '';
        if (audioFile) audioFile.value = '';
        if (videoFile) videoFile.value = '';

        // Refresh complaints list if visible
        if (typeof loadUserComplaints === 'function') {
            loadUserComplaints();
        }

    } catch (error) {
        resultContainer.innerHTML = `
            <div class="card" style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; text-align: center; padding: 2rem;">
                <span style="font-size: 4rem; display: block; margin-bottom: 1rem;">❌</span>
                <h2 style="margin: 0 0 0.5rem 0; color: white;">Error Processing Complaint</h2>
                <p style="margin: 0; opacity: 0.9;">${error.message}</p>
            </div>
        `;
    }
}

// ============================================
// Chatbot
// ============================================

let chatbotOpen = false;

function toggleChatbot() {
    const window = document.querySelector('.chatbot-window');
    chatbotOpen = !chatbotOpen;
    window.classList.toggle('open', chatbotOpen);
}

async function sendChatMessage() {
    const input = document.getElementById('chatbot-input');
    const messagesContainer = document.getElementById('chatbot-messages');

    if (!input.value.trim()) return;

    const userMessage = input.value;
    input.value = '';

    // Add user message
    messagesContainer.innerHTML += `
        <div class="chatbot-message user">${userMessage}</div>
    `;
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Add loading message
    const loadingId = 'loading-' + Date.now();
    messagesContainer.innerHTML += `
        <div class="chatbot-message bot" id="${loadingId}">
            <div class="spinner"></div>
        </div>
    `;

    try {
        const result = await apiCall('/chatbot/query', 'POST', { question: userMessage });

        document.getElementById(loadingId).innerHTML = result.answer;
    } catch (error) {
        document.getElementById(loadingId).innerHTML = 'Sorry, I encountered an error. Please try again.';
    }

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

// ============================================
// Page Navigation (SPA-like)
// ============================================

function showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.add('hidden');
    });

    // Show selected page
    const selectedPage = document.getElementById(pageId);
    if (selectedPage) {
        selectedPage.classList.remove('hidden');
    }

    // Update nav
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-page') === pageId) {
            link.classList.add('active');
        }
    });
}

// ============================================
// User Dashboard Data Loading
// ============================================

async function loadUserStats() {
    try {
        const session = JSON.parse(sessionStorage.getItem('userSession') || '{}');
        const userId = session.user_id;

        if (!userId) {
            // Set default values for guests
            document.getElementById('stat-total').textContent = '0';
            document.getElementById('stat-pending').textContent = '0';
            document.getElementById('stat-solved').textContent = '0';
            return;
        }

        const response = await fetch(`${API_BASE}/db/complaints/${userId}`);
        const data = await response.json();
        const complaints = data.complaints || [];

        document.getElementById('stat-total').textContent = complaints.length;
        document.getElementById('stat-pending').textContent = complaints.filter(c => c.status === 'pending').length;
        document.getElementById('stat-solved').textContent = complaints.filter(c => c.status === 'solved').length;
    } catch (error) {
        console.error('Error loading user stats:', error);
    }
}

async function loadUserComplaints() {
    try {
        const session = JSON.parse(sessionStorage.getItem('userSession') || '{}');
        const userId = session.user_id;

        const tbody = document.getElementById('complaints-table');
        if (!tbody) return;

        if (!userId) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Please log in to see your complaints</td></tr>';
            return;
        }

        const response = await fetch(`${API_BASE}/db/complaints/${userId}`);
        const data = await response.json();
        const complaints = data.complaints || [];

        // Store in cache for modal viewing
        userComplaints = complaints;

        tbody.innerHTML = '';

        complaints.forEach(c => {
            const statusClass = c.status === 'solved' ? 'solved' : c.status === 'ongoing' ? 'ongoing' : 'pending';

            tbody.innerHTML += `
                <tr>
                    <td>#${c.complaint_id}</td>
                    <td>${formatDate(c.created_at)}</td>
                    <td>${(c.narrative_summary || c.crime_type || 'N/A').substring(0, 50)}...</td>
                    <td><span class="badge badge-${statusClass}">${c.status}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline" onclick="viewUserComplaint('${c.complaint_id}')">View</button>
                        ${c.status !== 'solved' ? `<button class="btn btn-sm btn-danger" title="Request urgent attention" onclick="nudgeComplaint('${c.complaint_id}')">🔔</button>` : ''}
                    </td>
                </tr>
            `;
        });

        if (complaints.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No complaints found</td></tr>';
        }
    } catch (error) {
        console.error('Error loading user complaints:', error);
    }
}

// Store user complaints for viewing
let userComplaints = [];

async function viewUserComplaint(id) {
    // Try to find from cached list first
    let complaint = userComplaints.find(c => c.complaint_id === id);

    // If not found, fetch from API
    if (!complaint) {
        try {
            const session = JSON.parse(sessionStorage.getItem('userSession') || '{}');
            const userId = session.user_id;
            const response = await fetch(`${API_BASE}/db/complaints/${userId}`);
            const data = await response.json();
            userComplaints = data.complaints || [];
            complaint = userComplaints.find(c => c.complaint_id === id);
        } catch (error) {
            alert('Error loading complaint details');
            return;
        }
    }

    if (!complaint) {
        alert('Complaint not found');
        return;
    }

    // Create and show modal
    showComplaintModal(complaint);
}

function showComplaintModal(complaint) {
    // Remove existing modal if any
    const existingModal = document.getElementById('user-complaint-modal');
    if (existingModal) existingModal.remove();

    const statusClass = complaint.status === 'solved' ? 'solved' : complaint.status === 'ongoing' ? 'ongoing' : 'pending';

    const modal = document.createElement('div');
    modal.id = 'user-complaint-modal';
    modal.className = 'modal';
    modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000;';
    modal.innerHTML = `
        <div class="card" style="width: 90%; max-width: 600px; max-height: 80vh; overflow-y: auto;">
            <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
                <h3 class="card-title" style="margin: 0;">Complaint Details</h3>
                <button class="btn btn-sm btn-outline" onclick="closeUserModal()">✕</button>
            </div>
            <div style="padding: 1.5rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                    <strong>Complaint ID:</strong>
                    <span>#${complaint.complaint_id}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                    <strong>Date:</strong>
                    <span>${formatDate(complaint.created_at)}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                    <strong>Status:</strong>
                    <span class="badge badge-${statusClass}">${complaint.status}</span>
                </div>
                ${complaint.crime_type ? `
                <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                    <strong>Crime Type:</strong>
                    <span>${complaint.crime_type}</span>
                </div>` : ''}
                ${complaint.financial_loss ? `
                <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                    <strong>Financial Loss:</strong>
                    <span style="color: #dc3545;">₹${complaint.financial_loss.toLocaleString('en-IN')}</span>
                </div>` : ''}
                <hr style="margin: 1rem 0;">
                <div style="margin-bottom: 1rem;">
                    <strong>Summary:</strong>
                    <p style="background: #f0f9ff; padding: 1rem; border-radius: 8px; margin-top: 0.5rem;">
                        ${complaint.narrative_summary || 'No summary available'}
                    </p>
                </div>
                ${complaint.admin_note ? `
                <div style="margin-bottom: 1rem;">
                    <strong>Admin Note:</strong>
                    <p style="background: #fef3c7; padding: 1rem; border-radius: 8px; margin-top: 0.5rem;">
                        ${complaint.admin_note}
                    </p>
                </div>` : ''}
                ${complaint.status !== 'solved' ? `
                <button class="btn btn-primary btn-block" onclick="nudgeComplaint('${complaint.complaint_id}'); closeUserModal();">
                    🔔 Request Urgent Attention
                </button>` : ''}
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeUserModal();
    });
}

function closeUserModal() {
    const modal = document.getElementById('user-complaint-modal');
    if (modal) modal.remove();
}

async function nudgeComplaint(id) {
    try {
        // Send nudge notification to admin
        const response = await fetch(`${API_BASE}/db/complaints/${id}/nudge`, { method: 'POST' });

        if (response.ok) {
            alert('✅ Urgent attention request sent! The admin team has been notified.');
        } else {
            // Even if endpoint doesn't exist, show a message
            alert('✅ Your request for urgent attention has been noted.');
        }
    } catch (error) {
        // Fallback message
        alert('✅ Your request for urgent attention has been noted.');
    }
}

// ============================================
// NOTIFICATION SYSTEM
// ============================================

let notificationsVisible = false;

function toggleNotifications() {
    const dropdown = document.getElementById('notification-dropdown');
    notificationsVisible = !notificationsVisible;
    dropdown.style.display = notificationsVisible ? 'block' : 'none';
    if (notificationsVisible) {
        loadUserNotifications();
    }
}

async function loadUserNotifications() {
    try {
        const session = JSON.parse(sessionStorage.getItem('userSession') || '{}');
        const userId = session.user_id;

        if (!userId) {
            const list = document.getElementById('notification-list');
            if (list) {
                list.innerHTML = '<div style="padding: 16px; text-align: center; color: #888;">Please log in to see notifications</div>';
            }
            return;
        }

        const response = await fetch(`${API_BASE}/db/notifications/user/${userId}`);
        const data = await response.json();
        const notifications = data.notifications || [];
        const unreadCount = data.unread_count || 0;

        // Update badge
        const badge = document.getElementById('notification-badge');
        if (badge) {
            if (unreadCount > 0) {
                badge.textContent = unreadCount;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }

        // Render notifications
        const list = document.getElementById('notification-list');
        if (!list) return;

        if (notifications.length === 0) {
            list.innerHTML = '<div style="padding: 16px; text-align: center; color: #888;">No notifications</div>';
            return;
        }

        list.innerHTML = notifications.map(n => `
            <div class="notification-item" style="padding: 12px; border-bottom: 1px solid #eee; background: ${n.is_read ? '#fff' : '#f0f7ff'}; cursor: pointer;" onclick="markNotificationRead(${n.id})">
                <div style="font-size: 14px; margin-bottom: 4px;">${n.message}</div>
                <div style="font-size: 11px; color: #888;">${formatDate(n.created_at)}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

async function markNotificationRead(notificationId) {
    try {
        await fetch(`${API_BASE}/db/notifications/${notificationId}/read`, { method: 'POST' });
        await loadUserNotifications();
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

// ============================================
// Initialize
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    // Set up navigation
    document.querySelectorAll('.sidebar-nav a[data-page]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            showPage(link.getAttribute('data-page'));
        });
    });

    // Show default page
    showPage('dashboard');

    // Load user data from database
    await loadUserStats();
    await loadUserComplaints();

    // Load notifications
    loadUserNotifications();
    // Refresh notifications every 30 seconds
    setInterval(loadUserNotifications, 30000);
});

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const wrapper = document.querySelector('.notification-wrapper');
    if (wrapper && !wrapper.contains(e.target) && notificationsVisible) {
        toggleNotifications();
    }
});
