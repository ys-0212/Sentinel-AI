import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { getAllComplaints, updateComplaintStatus, getSimilarComplaints, deleteComplaint, checkProfileComplete, formatDate, getSeverityColor, getStatusClass, type Complaint, type SimilarComplaint } from '../../api/client';

export default function ComplaintDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { user } = useAuth();
    const [complaint, setComplaint] = useState<Complaint | null>(null);
    const [similarComplaints, setSimilarComplaints] = useState<SimilarComplaint[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingSimilar, setLoadingSimilar] = useState(false);
    const [status, setStatus] = useState('');
    const [adminNote, setAdminNote] = useState('');
    const [updating, setUpdating] = useState(false);
    
    // Delete modal state
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [deletePassword, setDeletePassword] = useState('');
    const [deleteReason, setDeleteReason] = useState('');
    const [deleting, setDeleting] = useState(false);
    const [deleteError, setDeleteError] = useState('');
    
    // Profile check state
    const [profileComplete, setProfileComplete] = useState<boolean | null>(null);

    useEffect(() => {
        loadComplaint();
        checkAdminProfile();
    }, [id, user]);

    async function checkAdminProfile() {
        if (!user?.user_id) return;
        
        try {
            const result = await checkProfileComplete(user.user_id, 'admin');
            setProfileComplete(result.complete);
        } catch (error) {
            console.error('Error checking profile:', error);
            setProfileComplete(true);  // Allow access if check fails
        }
    }

    async function loadComplaint() {
        if (!id) return;

        try {
            const data = await getAllComplaints();
            const found = (data.complaints || []).find((c: Complaint) => c.complaint_id === id);
            if (found) {
                setComplaint(found);
                setStatus(found.status);
                setAdminNote(found.admin_note || '');

                // Load similar complaints
                setLoadingSimilar(true);
                try {
                    const similarData = await getSimilarComplaints(id);
                    setSimilarComplaints(similarData.similar || []);
                } catch {
                    setSimilarComplaints([]);
                } finally {
                    setLoadingSimilar(false);
                }
            }
        } catch (error) {
            console.error('Error loading complaint:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleUpdateStatus() {
        if (!id) return;
        
        // Check profile before allowing action
        if (profileComplete === false) {
            alert('Please complete your admin profile before updating complaints.');
            navigate('/admin/profile');
            return;
        }

        setUpdating(true);
        try {
            await updateComplaintStatus(id, status, adminNote);
            alert('Status updated successfully!');
            loadComplaint();
        } catch (error) {
            alert('Error updating status');
        } finally {
            setUpdating(false);
        }
    }

    async function handleDelete() {
        if (!id || !user?.user_id) return;
        
        // Check profile before allowing delete action
        if (profileComplete === false) {
            setDeleteError('Please complete your admin profile before deleting complaints.');
            return;
        }
        
        setDeleting(true);
        setDeleteError('');
        
        try {
            await deleteComplaint(id, user.user_id, deletePassword, deleteReason);
            alert('Complaint deleted successfully!');
            navigate('/admin/complaints');
        } catch (error) {
            setDeleteError(error instanceof Error ? error.message : 'Failed to delete');
        } finally {
            setDeleting(false);
        }
    }

    if (loading) {
        return (
            <div className="text-center p-4">
                <div className="spinner" style={{ margin: '0 auto' }} />
            </div>
        );
    }

    if (!complaint) {
        return (
            <div className="card">
                <p className="text-center text-muted">Complaint not found</p>
                <button className="btn btn-primary" onClick={() => navigate('/admin/complaints')}>
                    Back to Complaints
                </button>
            </div>
        );
    }

    const score = complaint.severity_score || 0;
    const severityColor = getSeverityColor(score);
    const isAnonymous = (complaint as any).is_anonymous;

    return (
        <>
            <div className="d-flex align-center gap-2 mb-3">
                <button className="btn btn-outline" onClick={() => navigate(-1)}>← Back</button>
                <h1 style={{ margin: 0 }}>Complaint #{complaint.complaint_id}</h1>
                {isAnonymous && (
                    <span className="badge badge-pending" style={{ marginLeft: '1rem' }}>
                        🔒 Anonymous
                    </span>
                )}
            </div>

            <div className="grid grid-2">
                {/* Main Details */}
                <div className="card">
                    <h3 className="card-title mb-3">Complaint Details</h3>

                    <div className="d-flex justify-between mb-2">
                        <strong>Date:</strong>
                        <span>{formatDate(complaint.created_at)}</span>
                    </div>
                    <div className="d-flex justify-between mb-2">
                        <strong>Status:</strong>
                        <span className={`badge ${getStatusClass(complaint.status)}`}>{complaint.status}</span>
                    </div>
                    <div className="d-flex justify-between mb-2">
                        <strong>User ID:</strong>
                        <span>{isAnonymous ? '🔒 Hidden (Anonymous)' : complaint.user_id?.substring(0, 8) + '...'}</span>
                    </div>
                    <div className="d-flex justify-between mb-2">
                        <strong>Crime Type:</strong>
                        <span>{complaint.crime_type || 'N/A'}</span>
                    </div>
                    <div className="d-flex justify-between mb-2">
                        <strong>Financial Loss:</strong>
                        <span className="text-danger">₹{(complaint.financial_loss || 0).toLocaleString('en-IN')}</span>
                    </div>
                    <div className="d-flex justify-between mb-2">
                        <strong>Severity:</strong>
                        <span className="badge" style={{ background: `${severityColor}20`, color: severityColor, border: `1px solid ${severityColor}` }}>
                            {score.toFixed(1)}/5
                        </span>
                    </div>

                    <hr style={{ margin: '1rem 0' }} />

                    <div style={{ marginBottom: '1rem' }}>
                        <strong>AI Summary:</strong>
                        <div className="alert alert-info" style={{ marginTop: '0.5rem' }}>
                            {complaint.narrative_summary || 'No summary available'}
                        </div>
                    </div>

                    <div style={{ marginBottom: '1rem' }}>
                        <strong>Full Complaint:</strong>
                        <div style={{ background: 'var(--gray-100)', padding: '12px', borderRadius: '8px', marginTop: '0.5rem', maxHeight: '150px', overflowY: 'auto' }}>
                            {complaint.complaint_text || 'N/A'}
                        </div>
                    </div>
                </div>

                {/* Update Status */}
                <div className="card">
                    <h3 className="card-title mb-3">Update Status</h3>

                    <div className="form-group">
                        <label className="form-label">New Status</label>
                        <select className="form-select" value={status} onChange={e => setStatus(e.target.value)}>
                            <option value="pending">Pending</option>
                            <option value="ongoing">Ongoing</option>
                            <option value="solved">Solved</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Admin Note</label>
                        <textarea
                            className="form-textarea"
                            rows={3}
                            value={adminNote}
                            onChange={e => setAdminNote(e.target.value)}
                            placeholder="Add a note for the user..."
                        />
                    </div>

                    <button className="btn btn-primary btn-block" onClick={handleUpdateStatus} disabled={updating}>
                        {updating ? <div className="spinner" /> : 'Save Changes'}
                    </button>

                    <hr style={{ margin: '1.5rem 0' }} />

                    {/* Delete Section */}
                    <div className="delete-section">
                        <h4 style={{ color: 'var(--danger)', marginBottom: '0.5rem' }}>⚠️ Danger Zone</h4>
                        <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
                            Deleting a complaint is permanent and cannot be undone.
                        </p>
                        <button 
                            className="btn btn-danger btn-block"
                            onClick={() => setShowDeleteModal(true)}
                        >
                            🗑️ Delete Complaint
                        </button>
                    </div>
                </div>
            </div>

            {/* Similar Complaints Section */}
            <div className="card similar-complaints">
                <div className="card-header">
                    <h3 className="card-title">🔍 Similar Complaints (NLP Analysis)</h3>
                </div>

                {loadingSimilar ? (
                    <div className="text-center p-3">
                        <div className="spinner" style={{ margin: '0 auto' }} />
                        <p className="text-muted mt-2">Analyzing similar complaints...</p>
                    </div>
                ) : similarComplaints.length === 0 ? (
                    <p className="text-muted text-center">No similar complaints found in the database.</p>
                ) : (
                    <div>
                        <p className="text-muted mb-3">
                            These past complaints have similar content and may help in resolving this case:
                        </p>
                        {similarComplaints.map(similar => (
                            <div
                                key={similar.complaint_id}
                                className="similar-complaint-card"
                                onClick={() => navigate(`/admin/complaints/${similar.complaint_id}`)}
                            >
                                <div className="d-flex justify-between align-center mb-1">
                                    <strong>#{similar.complaint_id}</strong>
                                    <span className="similarity-score" style={{
                                        background: similar.similarity_score >= 0.8 ? 'var(--success)' : 
                                                   similar.similarity_score >= 0.6 ? 'var(--warning)' : 'var(--gray-500)',
                                        color: 'white',
                                        padding: '2px 8px',
                                        borderRadius: '12px',
                                        fontSize: '0.75rem',
                                        fontWeight: 'bold'
                                    }}>
                                        {Math.round(similar.similarity_score * 100)}% match
                                    </span>
                                </div>
                                <div className="text-muted" style={{ fontSize: '0.875rem' }}>
                                    Crime Type: {similar.crime_type || 'N/A'} | Status: <span className={`badge ${getStatusClass(similar.status)}`}>{similar.status}</span>
                                </div>
                                {similar.narrative_summary && (
                                    <p style={{ fontSize: '0.875rem', marginTop: '0.5rem', color: 'var(--text-secondary)' }}>
                                        {similar.narrative_summary.substring(0, 150)}...
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Delete Confirmation Modal */}
            {showDeleteModal && (
                <div className="modal-overlay" onClick={() => setShowDeleteModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <h2 style={{ color: 'var(--danger)', marginBottom: '1rem' }}>🗑️ Delete Complaint</h2>
                        <p>You are about to permanently delete complaint <strong>#{complaint.complaint_id}</strong>.</p>
                        <p className="text-muted" style={{ fontSize: '0.85rem' }}>This action requires your deletion password and will be logged for audit purposes.</p>
                        
                        {deleteError && (
                            <div className="alert alert-danger" style={{ marginTop: '1rem' }}>
                                {deleteError}
                            </div>
                        )}

                        <div className="form-group" style={{ marginTop: '1rem' }}>
                            <label className="form-label">Deletion Password *</label>
                            <input
                                type="password"
                                className="form-input"
                                value={deletePassword}
                                onChange={e => setDeletePassword(e.target.value)}
                                placeholder="Enter your deletion password"
                                required
                            />
                            <div className="form-hint">Default: delete123</div>
                        </div>

                        <div className="form-group">
                            <label className="form-label">Reason for Deletion</label>
                            <textarea
                                className="form-textarea"
                                rows={2}
                                value={deleteReason}
                                onChange={e => setDeleteReason(e.target.value)}
                                placeholder="Why is this complaint being deleted? (optional)"
                            />
                        </div>

                        <div className="d-flex gap-2" style={{ marginTop: '1.5rem' }}>
                            <button 
                                className="btn btn-secondary" 
                                onClick={() => setShowDeleteModal(false)}
                                style={{ flex: 1 }}
                            >
                                Cancel
                            </button>
                            <button 
                                className="btn btn-danger" 
                                onClick={handleDelete}
                                disabled={deleting || !deletePassword}
                                style={{ flex: 1 }}
                            >
                                {deleting ? <div className="spinner" /> : 'Confirm Delete'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
