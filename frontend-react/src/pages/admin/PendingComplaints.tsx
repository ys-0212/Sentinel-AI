import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAllComplaints, formatDate, getSeverityColor, type Complaint } from '../../api/client';

export default function PendingComplaints() {
    const navigate = useNavigate();
    const [complaints, setComplaints] = useState<Complaint[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadComplaints();
    }, []);

    async function loadComplaints() {
        try {
            const data = await getAllComplaints('pending', 100);
            setComplaints(data.complaints || []);
        } catch (error) {
            console.error('Error loading complaints:', error);
        } finally {
            setLoading(false);
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
            <h1 className="mb-3">Pending Complaints</h1>
            <div className="alert alert-warning">
                <strong>⚠️ Attention Required:</strong> {complaints.length} complaints are awaiting review.
            </div>

            <div className="card">
                <div className="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Date</th>
                                <th>Crime Type</th>
                                <th>Financial Loss</th>
                                <th>Severity</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {complaints.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="text-center text-muted">No pending complaints</td>
                                </tr>
                            ) : (
                                complaints.map(c => {
                                    const score = c.severity_score || 0;
                                    const color = getSeverityColor(score);
                                    return (
                                        <tr key={c.complaint_id}>
                                            <td>#{c.complaint_id}</td>
                                            <td>{formatDate(c.created_at)}</td>
                                            <td>{c.crime_type || 'N/A'}</td>
                                            <td>₹{(c.financial_loss || 0).toLocaleString('en-IN')}</td>
                                            <td>
                                                <span className="badge" style={{ background: `${color}20`, color, border: `1px solid ${color}` }}>
                                                    {score.toFixed(1)}/5
                                                </span>
                                            </td>
                                            <td>
                                                <button className="btn btn-sm btn-primary" onClick={() => navigate(`/admin/complaints/${c.complaint_id}`)}>
                                                    View
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </>
    );
}
