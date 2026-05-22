import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { getUserComplaints, type Complaint } from '../../api/client';

export default function UserDashboard() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [stats, setStats] = useState({ total: 0, pending: 0, solved: 0, ongoing: 0 });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadStats();
    }, [user?.user_id]);

    async function loadStats() {
        if (!user?.user_id) {
            setLoading(false);
            return;
        }

        try {
            const data = await getUserComplaints(user.user_id);
            const complaints = data.complaints || [];
            setStats({
                total: complaints.length,
                pending: complaints.filter((c: Complaint) => c.status === 'pending').length,
                ongoing: complaints.filter((c: Complaint) => c.status === 'ongoing').length,
                solved: complaints.filter((c: Complaint) => c.status === 'solved').length,
            });
        } catch (error) {
            console.error('Error loading stats:', error);
        } finally {
            setLoading(false);
        }
    }

    if (loading) {
        return (
            <div className="dashboard-loading">
                <div className="skeleton-grid">
                    <div className="skeleton skeleton-stat"></div>
                    <div className="skeleton skeleton-stat"></div>
                    <div className="skeleton skeleton-stat"></div>
                </div>
                <div className="skeleton skeleton-card"></div>
            </div>
        );
    }

    const hasComplaints = stats.total > 0;

    return (
        <>
            {/* Stats Section */}
            <div className="grid grid-3 mb-4">
                <div className="stat-card primary">
                    <div className="stat-value">{stats.total}</div>
                    <div className="stat-label">Total Complaints</div>
                    <div className="stat-subtext">All reports submitted by you</div>
                </div>
                <div className="stat-card warning">
                    <div className="stat-value">{stats.pending + stats.ongoing}</div>
                    <div className="stat-label">In Progress</div>
                    <div className="stat-subtext">Being reviewed by authorities</div>
                </div>
                <div className="stat-card success">
                    <div className="stat-value">{stats.solved}</div>
                    <div className="stat-label">Resolved</div>
                    <div className="stat-subtext">Successfully addressed cases</div>
                </div>
            </div>

            {/* Primary Action - Report a Cybercrime */}
            <div className="card card-highlight mb-3">
                <div className="card-content-centered">
                    <div className="card-icon">🛡️</div>
                    <h2>Report a Cybercrime Incident</h2>
                    <p className="text-muted mb-2">
                        File a detailed complaint about fraud, hacking, identity theft, or other cyber offenses.
                    </p>
                    <button 
                        className="btn btn-primary btn-lg" 
                        onClick={() => navigate('/dashboard/complaints/new')}
                    >
                        📝 Register New Complaint
                    </button>
                </div>
            </div>

            {/* Quick Actions - Secondary */}
            <div className="grid grid-2 mb-4">
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">My Complaints</h3>
                    </div>
                    {hasComplaints ? (
                        <>
                            <p className="text-muted mb-2">
                                You have {stats.pending} pending and {stats.ongoing} ongoing complaints.
                            </p>
                            <button 
                                className="btn btn-secondary" 
                                onClick={() => navigate('/dashboard/complaints')}
                            >
                                📋 View All Complaints
                            </button>
                        </>
                    ) : (
                        <div className="empty-state">
                            <div className="empty-state-icon">📋</div>
                            <p>No complaints yet</p>
                            <span className="text-muted">Your submitted complaints will appear here</span>
                        </div>
                    )}
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Security Tools</h3>
                    </div>
                    <p className="text-muted mb-2">
                        Analyze suspicious calls, messages, or emails for potential scams.
                    </p>
                    <div className="d-flex gap-1" style={{ flexWrap: 'wrap' }}>
                        <button 
                            className="btn btn-outline btn-sm" 
                            onClick={() => navigate('/dashboard/scam-detector')}
                        >
                            📞 Call Scam Check
                        </button>
                        <button 
                            className="btn btn-outline btn-sm" 
                            onClick={() => navigate('/dashboard/malicious-detector')}
                        >
                            ⚠️ Message Analysis
                        </button>
                    </div>
                </div>
            </div>

            {/* Tips Section */}
            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">🔐 Stay Safe Online</h3>
                </div>
                <div className="tips-grid">
                    <div className="tip-item">
                        <strong>Never share OTPs</strong>
                        <span>Banks never ask for OTPs or passwords via call/SMS</span>
                    </div>
                    <div className="tip-item">
                        <strong>Verify caller identity</strong>
                        <span>Always call back on official numbers before sharing info</span>
                    </div>
                    <div className="tip-item">
                        <strong>Check URLs carefully</strong>
                        <span>Look for HTTPS and correct spelling in website addresses</span>
                    </div>
                </div>
            </div>
        </>
    );
}
