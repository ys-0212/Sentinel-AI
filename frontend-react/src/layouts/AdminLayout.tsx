import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import { getAdminNotifications, markNotificationRead, formatDate, type Notification } from '../api/client';
import Footer from '../components/Footer';
import ThemeToggle from '../components/ThemeToggle';

export default function AdminLayout() {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [showNotifications, setShowNotifications] = useState(false);
    const notificationRef = useRef<HTMLDivElement>(null);

    // Click outside to close notifications
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
                setShowNotifications(false);
            }
        }
        if (showNotifications) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [showNotifications]);

    useEffect(() => {
        loadNotifications();
        const interval = setInterval(loadNotifications, 30000);
        return () => clearInterval(interval);
    }, []);

    async function loadNotifications() {
        try {
            const data = await getAdminNotifications();
            setNotifications(data.notifications);
            setUnreadCount(data.unread_count);
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }

    async function handleMarkRead(id: number) {
        await markNotificationRead(id);
        loadNotifications();
    }

    function handleLogout() {
        logout();
        navigate('/login');
    }

    return (
        <div className="page-wrapper">
            {/* Mobile Menu Button */}
            <button className="mobile-menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
                ☰
            </button>

            {/* Sidebar Overlay for Mobile */}
            <div className={`sidebar-overlay ${sidebarOpen ? 'open' : ''}`} onClick={() => setSidebarOpen(false)} />

            {/* Sidebar */}
            <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
                <div className="sidebar-logo">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    </svg>
                    CyberSafe Admin
                </div>

                <ul className="sidebar-nav">
                    <li>
                        <NavLink to="/admin" end onClick={() => setSidebarOpen(false)}>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <rect x="3" y="3" width="7" height="7" />
                                <rect x="14" y="3" width="7" height="7" />
                                <rect x="14" y="14" width="7" height="7" />
                                <rect x="3" y="14" width="7" height="7" />
                            </svg>
                            Dashboard
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/admin/complaints" onClick={() => setSidebarOpen(false)}>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                <polyline points="14 2 14 8 20 8" />
                                <line x1="16" y1="13" x2="8" y2="13" />
                                <line x1="16" y1="17" x2="8" y2="17" />
                            </svg>
                            All Complaints
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/admin/complaints/pending" onClick={() => setSidebarOpen(false)}>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="12" cy="12" r="10" />
                                <polyline points="12 6 12 12 16 14" />
                            </svg>
                            Pending
                        </NavLink>
                    </li>
                    <li>
                        <NavLink to="/admin/login-history" onClick={() => setSidebarOpen(false)}>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                                <polyline points="10 17 15 12 10 7" />
                                <line x1="15" y1="12" x2="3" y2="12" />
                            </svg>
                            Login History
                        </NavLink>
                    </li>
                </ul>

                <div className="sidebar-section">
                    <div className="sidebar-section-title">Settings</div>
                    <ul className="sidebar-nav">
                        <li>
                            <ThemeToggle />
                        </li>
                    </ul>
                </div>

                <div className="sidebar-section">
                    <div className="sidebar-section-title">Account</div>
                    <ul className="sidebar-nav">
                        <li>
                            <NavLink to="/admin/profile" onClick={() => setSidebarOpen(false)}>
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                    <circle cx="12" cy="7" r="4" />
                                </svg>
                                My Profile
                            </NavLink>
                        </li>
                        <li>
                            <button onClick={handleLogout}>
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                                    <polyline points="16 17 21 12 16 7" />
                                    <line x1="21" y1="12" x2="9" y2="12" />
                                </svg>
                                Logout
                            </button>
                        </li>
                    </ul>
                </div>
            </aside>

            {/* Main Content */}
            <main className="main-content">
                {/* Top bar with notifications and timeframe */}
                <div className="d-flex justify-between align-center mb-3">
                    <div>
                        <h1>Admin Dashboard</h1>
                        <p className="text-muted">Manage complaints and monitor security.</p>
                    </div>

                    <div className="d-flex align-center gap-2">
                        {/* Notification Bell */}
                        <div className="notification-wrapper" ref={notificationRef}>
                            <button 
                                className="btn btn-outline notification-btn" 
                                onClick={() => setShowNotifications(!showNotifications)}
                                aria-label="Notifications"
                                aria-expanded={showNotifications}
                            >
                                🔔
                                {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
                            </button>

                            {showNotifications && (
                                <div className="notification-dropdown">
                                    <div className="notification-header">
                                        🔔 Notifications
                                    </div>
                                    <div className="notification-list">
                                        {notifications.length === 0 ? (
                                            <div className="notification-empty">No notifications</div>
                                        ) : (
                                            notifications.map(n => (
                                                <div
                                                    key={n.id}
                                                    className={`notification-item ${n.is_read ? '' : 'unread'}`}
                                                    onClick={() => handleMarkRead(n.id)}
                                                    role="button"
                                                    tabIndex={0}
                                                    onKeyDown={(e) => e.key === 'Enter' && handleMarkRead(n.id)}
                                                >
                                                    <div className="notification-message">{n.message}</div>
                                                    <div className="notification-time">{formatDate(n.created_at)}</div>
                                                </div>
                                            ))
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Page Content (from nested routes) */}
                <div className="outlet-wrapper">
                    <Outlet />
                </div>

                {/* Spacer to push footer down - requires scroll to see */}
                <div style={{ minHeight: '200px' }}></div>

                <Footer />
            </main>
        </div>
    );
}
