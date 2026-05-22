import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import { getStats, getAllComplaints, formatDate, getSeverityColor, getStatusClass, type Complaint, type Stats } from '../../api/client';

ChartJS.register(ArcElement, Tooltip, Legend);

export default function AdminDashboard() {
    const navigate = useNavigate();
    const [stats, setStats] = useState<Stats>({ total: 0, pending: 0, ongoing: 0, solved: 0 });
    const [complaints, setComplaints] = useState<Complaint[]>([]);
    const [timeframe, setTimeframe] = useState('all');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, [timeframe]);

    async function loadData() {
        setLoading(true);
        try {
            const [statsData, complaintsData] = await Promise.all([
                getStats(timeframe),
                getAllComplaints(undefined, 100),
            ]);
            setStats(statsData);
            setComplaints(complaintsData.complaints || []);
        } catch (error) {
            console.error('Error loading data:', error);
        } finally {
            setLoading(false);
        }
    }

    // Calculate summary stats
    const highSeverity = complaints.filter(c => (c.severity_score || 0) >= 4).length;
    const mediumSeverity = complaints.filter(c => (c.severity_score || 0) >= 2 && (c.severity_score || 0) < 4).length;
    const lowSeverity = complaints.filter(c => (c.severity_score || 0) < 2).length;
    const totalLoss = complaints.reduce((sum, c) => sum + (c.financial_loss || 0), 0);
    const resolutionRate = stats.total > 0 ? Math.round((stats.solved / stats.total) * 100) : 0;

    const chartData = {
        labels: ['Pending', 'Ongoing', 'Solved'],
        datasets: [{
            data: [stats.pending, stats.ongoing, stats.solved],
            backgroundColor: ['#ffc107', '#0dcaf0', '#198754'],
        }],
    };

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
                <div>
                    <h1>Admin Dashboard</h1>
                </div>
                <select className="form-select" style={{ width: 'auto' }} value={timeframe} onChange={e => setTimeframe(e.target.value)}>
                    <option value="month">Last Month</option>
                    <option value="2months">Last 2 Months</option>
                    <option value="6months">Last 6 Months</option>
                    <option value="year">Last Year</option>
                    <option value="all">All Time</option>
                </select>
            </div>

            <div className="grid grid-4 mb-4">
                <div className="stat-card primary">
                    <div className="stat-value">{stats.total}</div>
                    <div className="stat-label">Total Complaints</div>
                </div>
                <div className="stat-card warning">
                    <div className="stat-value">{stats.pending}</div>
                    <div className="stat-label">Pending</div>
                </div>
                <div className="stat-card info">
                    <div className="stat-value">{stats.ongoing}</div>
                    <div className="stat-label">Ongoing</div>
                </div>
                <div className="stat-card success">
                    <div className="stat-value">{stats.solved}</div>
                    <div className="stat-label">Solved</div>
                </div>
            </div>

            <div className="grid grid-2 mb-4">
                <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2rem' }}>
                    <div className="card-header" style={{ width: '100%', textAlign: 'center' }}>
                        <h3 className="card-title">Status Distribution</h3>
                    </div>
                    <div style={{ maxWidth: '280px', margin: '1rem auto' }}>
                        <Doughnut data={chartData} />
                    </div>
                </div>
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">⚡ Quick Summary</h3>
                    </div>
                    <div style={{ padding: '1rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #eee' }}>
                            <span style={{ color: '#666' }}>🔴 High Severity (4+)</span>
                            <strong style={{ color: '#dc3545' }}>{highSeverity}</strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #eee' }}>
                            <span style={{ color: '#666' }}>🟠 Medium Severity (2-4)</span>
                            <strong style={{ color: '#fd7e14' }}>{mediumSeverity}</strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #eee' }}>
                            <span style={{ color: '#666' }}>🟢 Low Severity (&lt;2)</span>
                            <strong style={{ color: '#198754' }}>{lowSeverity}</strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #eee' }}>
                            <span style={{ color: '#666' }}>💰 Total Financial Loss</span>
                            <strong style={{ color: '#0d6efd' }}>₹{totalLoss.toLocaleString('en-IN')}</strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0' }}>
                            <span style={{ color: '#666' }}>📈 Resolution Rate</span>
                            <strong style={{ color: '#198754' }}>{resolutionRate}%</strong>
                        </div>
                    </div>
                </div>
            </div>

            <div className="card">
                <div className="card-header">
                    <h3 className="card-title">Recent Complaints (By Severity)</h3>
                </div>
                <div className="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Date</th>
                                <th>User</th>
                                <th>Summary</th>
                                <th>Severity</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {complaints.slice(0, 10).map(c => {
                                const score = c.severity_score || 0;
                                const color = getSeverityColor(score);
                                return (
                                    <tr key={c.complaint_id} style={{ borderLeft: `4px solid ${color}` }}>
                                        <td>#{c.complaint_id}</td>
                                        <td>{formatDate(c.created_at)}</td>
                                        <td>{c.user_id?.substring(0, 8)}...</td>
                                        <td>{(c.narrative_summary || c.crime_type || 'N/A').substring(0, 50)}...</td>
                                        <td>
                                            <span className="badge" style={{ background: `${color}20`, color, border: `1px solid ${color}` }}>
                                                {score.toFixed(1)}/5
                                            </span>
                                        </td>
                                        <td><span className={`badge ${getStatusClass(c.status)}`}>{c.status}</span></td>
                                        <td>
                                            <button className="btn btn-sm btn-primary" onClick={() => navigate(`/admin/complaints/${c.complaint_id}`)}>
                                                View
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </>
    );
}
