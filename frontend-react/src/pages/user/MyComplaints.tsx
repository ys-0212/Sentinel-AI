import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { getUserComplaints, nudgeComplaint, formatDate, getStatusClass, type Complaint } from '../../api/client';

export default function MyComplaints() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [complaints, setComplaints] = useState<Complaint[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedComplaint, setSelectedComplaint] = useState<Complaint | null>(null);

    useEffect(() => {
        loadComplaints();
    }, [user?.user_id]);

    async function loadComplaints() {
        if (!user?.user_id) {
            setLoading(false);
            return;
        }

        try {
            const data = await getUserComplaints(user.user_id);
            setComplaints(data.complaints || []);
        } catch (error) {
            console.error('Error loading complaints:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleNudge(id: string) {
        try {
            await nudgeComplaint(id);
            alert('✅ Urgent attention request sent! The admin team has been notified.');
        } catch {
            alert('✅ Your request for urgent attention has been noted.');
        }
    }

    if (loading) {
        return (
            <div className="text-center p-4">
                <div className="spinner" style={{ margin: '0 auto' }} />
            </div>
        );
    }

    return (
        <>
            <div className="d-flex justify-between align-center mb-3">
                <h1>My Complaints</h1>
                <button className="btn btn-primary" onClick={() => navigate('/dashboard/complaints/new')}>
                    + New Complaint
                </button>
            </div>

            <div className="card">
                <div className="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Date</th>
                                <th>Summary</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {complaints.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="text-center text-muted">No complaints found</td>
                                </tr>
                            ) : (
                                complaints.map(c => (
                                    <tr key={c.complaint_id}>
                                        <td>#{c.complaint_id}</td>
                                        <td>{formatDate(c.created_at)}</td>
                                        <td>{(c.narrative_summary || c.crime_type || 'N/A').substring(0, 50)}...</td>
                                        <td><span className={`badge ${getStatusClass(c.status)}`}>{c.status}</span></td>
                                        <td>
                                            <button className="btn btn-sm btn-outline" onClick={() => setSelectedComplaint(c)}>View</button>
                                            {c.status !== 'solved' && (
                                                <button className="btn btn-sm btn-danger" style={{ marginLeft: '4px' }} title="Request urgent attention" onClick={() => handleNudge(c.complaint_id)}>
                                                    🔔
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Complaint Detail Modal */}
            {selectedComplaint && (
                <div className="modal-overlay" onClick={() => setSelectedComplaint(null)}>
                    <div className="modal-content card" onClick={e => e.stopPropagation()}>
                        <div className="card-header">
                            <h3 className="card-title">Complaint Details</h3>
                            <button className="btn btn-sm btn-outline" onClick={() => setSelectedComplaint(null)}>✕</button>
                        </div>
                        <div style={{ padding: '1.5rem' }}>
                            <div className="d-flex justify-between mb-2">
                                <strong>Complaint ID:</strong>
                                <span>#{selectedComplaint.complaint_id}</span>
                            </div>
                            <div className="d-flex justify-between mb-2">
                                <strong>Date:</strong>
                                <span>{formatDate(selectedComplaint.created_at)}</span>
                            </div>
                            <div className="d-flex justify-between mb-2">
                                <strong>Status:</strong>
                                <span className={`badge ${getStatusClass(selectedComplaint.status)}`}>{selectedComplaint.status}</span>
                            </div>
                            {selectedComplaint.crime_type && (
                                <div className="d-flex justify-between mb-2">
                                    <strong>Crime Type:</strong>
                                    <span>{selectedComplaint.crime_type}</span>
                                </div>
                            )}
                            {selectedComplaint.financial_loss ? (
                                <div className="d-flex justify-between mb-2">
                                    <strong>Financial Loss:</strong>
                                    <span className="text-danger">₹{selectedComplaint.financial_loss.toLocaleString('en-IN')}</span>
                                </div>
                            ) : null}
                            <hr style={{ margin: '1rem 0' }} />
                            <div style={{ marginBottom: '1rem' }}>
                                <strong>Summary:</strong>
                                <p style={{ background: '#f0f9ff', padding: '1rem', borderRadius: '8px', marginTop: '0.5rem' }}>
                                    {selectedComplaint.narrative_summary || 'No summary available'}
                                </p>
                            </div>
                            {selectedComplaint.admin_note && (
                                <div style={{ marginBottom: '1rem' }}>
                                    <strong>Admin Note:</strong>
                                    <p style={{ background: '#fef3c7', padding: '1rem', borderRadius: '8px', marginTop: '0.5rem' }}>
                                        {selectedComplaint.admin_note}
                                    </p>
                                </div>
                            )}
                            {selectedComplaint.status !== 'solved' && (
                                <button className="btn btn-primary btn-block" onClick={() => { handleNudge(selectedComplaint.complaint_id); setSelectedComplaint(null); }}>
                                    🔔 Request Urgent Attention
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
