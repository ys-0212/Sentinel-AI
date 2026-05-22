import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAllComplaints, formatDate, getSeverityColor, getStatusClass, type Complaint } from '../../api/client';

type SortField = 'date' | 'severity' | 'loss' | 'status';
type SortOrder = 'asc' | 'desc';

export default function AllComplaints() {
    const navigate = useNavigate();
    const [complaints, setComplaints] = useState<Complaint[]>([]);
    const [filteredComplaints, setFilteredComplaints] = useState<Complaint[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchText, setSearchText] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [severityFilter, setSeverityFilter] = useState('');
    
    // Sorting state
    const [sortField, setSortField] = useState<SortField>('date');
    const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

    useEffect(() => {
        loadComplaints();
    }, []);

    useEffect(() => {
        applyFiltersAndSort();
    }, [complaints, searchText, statusFilter, severityFilter, sortField, sortOrder]);

    async function loadComplaints() {
        try {
            const data = await getAllComplaints(undefined, 100);
            setComplaints(data.complaints || []);
        } catch (error) {
            console.error('Error loading complaints:', error);
        } finally {
            setLoading(false);
        }
    }

    function applyFiltersAndSort() {
        let filtered = [...complaints];

        // Text search
        if (searchText) {
            const search = searchText.toLowerCase();
            filtered = filtered.filter(c =>
                c.complaint_id?.toLowerCase().includes(search) ||
                c.user_id?.toLowerCase().includes(search) ||
                c.crime_type?.toLowerCase().includes(search)
            );
        }

        // Status filter
        if (statusFilter) {
            filtered = filtered.filter(c => c.status === statusFilter);
        }

        // Severity filter
        if (severityFilter) {
            filtered = filtered.filter(c => {
                const score = c.severity_score || 0;
                if (severityFilter === 'high') return score >= 4;
                if (severityFilter === 'medium') return score >= 2 && score < 4;
                if (severityFilter === 'low') return score < 2;
                return true;
            });
        }

        // Sorting
        filtered.sort((a, b) => {
            let comparison = 0;
            
            switch (sortField) {
                case 'date':
                    comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
                    break;
                case 'severity':
                    comparison = (a.severity_score || 0) - (b.severity_score || 0);
                    break;
                case 'loss':
                    comparison = (a.financial_loss || 0) - (b.financial_loss || 0);
                    break;
                case 'status':
                    const statusOrder = { pending: 0, ongoing: 1, solved: 2 };
                    comparison = (statusOrder[a.status as keyof typeof statusOrder] || 0) - 
                                (statusOrder[b.status as keyof typeof statusOrder] || 0);
                    break;
            }
            
            return sortOrder === 'asc' ? comparison : -comparison;
        });

        setFilteredComplaints(filtered);
    }

    function handleSortChange(field: SortField) {
        if (sortField === field) {
            // Toggle order
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortOrder('desc');
        }
    }

    function getSortIcon(field: SortField) {
        if (sortField !== field) return '⇅';
        return sortOrder === 'asc' ? '↑' : '↓';
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
            <h1 className="mb-3">All Complaints</h1>

            <div className="card mb-3">
                <div className="d-flex gap-2" style={{ flexWrap: 'wrap', alignItems: 'center' }}>
                    <input
                        type="text"
                        className="form-input"
                        placeholder="Search by ID or user..."
                        style={{ maxWidth: '300px' }}
                        value={searchText}
                        onChange={e => setSearchText(e.target.value)}
                    />
                    <select className="form-select" style={{ width: 'auto' }} value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                        <option value="">All Status</option>
                        <option value="pending">Pending</option>
                        <option value="ongoing">Ongoing</option>
                        <option value="solved">Solved</option>
                    </select>
                    <select className="form-select" style={{ width: 'auto' }} value={severityFilter} onChange={e => setSeverityFilter(e.target.value)}>
                        <option value="">All Severity</option>
                        <option value="high">High (4+)</option>
                        <option value="medium">Medium (2-4)</option>
                        <option value="low">Low (&lt;2)</option>
                    </select>
                    
                    {/* Sort options */}
                    <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span className="text-muted" style={{ fontSize: '0.85rem' }}>Sort by:</span>
                        <div className="d-flex gap-1">
                            <button 
                                className={`btn btn-sm ${sortField === 'date' ? 'btn-primary' : 'btn-outline'}`}
                                onClick={() => handleSortChange('date')}
                            >
                                Date {getSortIcon('date')}
                            </button>
                            <button 
                                className={`btn btn-sm ${sortField === 'severity' ? 'btn-primary' : 'btn-outline'}`}
                                onClick={() => handleSortChange('severity')}
                            >
                                Severity {getSortIcon('severity')}
                            </button>
                            <button 
                                className={`btn btn-sm ${sortField === 'loss' ? 'btn-primary' : 'btn-outline'}`}
                                onClick={() => handleSortChange('loss')}
                            >
                                Loss {getSortIcon('loss')}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="card">
                <div className="d-flex justify-between align-center mb-2">
                    <span className="text-muted">Showing {filteredComplaints.length} complaints</span>
                </div>
                <div className="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th style={{ cursor: 'pointer' }} onClick={() => handleSortChange('date')}>
                                    Date {getSortIcon('date')}
                                </th>
                                <th>User</th>
                                <th>Crime Type</th>
                                <th style={{ cursor: 'pointer' }} onClick={() => handleSortChange('loss')}>
                                    Financial Loss {getSortIcon('loss')}
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => handleSortChange('severity')}>
                                    Severity {getSortIcon('severity')}
                                </th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredComplaints.length === 0 ? (
                                <tr>
                                    <td colSpan={8} className="text-center text-muted">No complaints found</td>
                                </tr>
                            ) : (
                                filteredComplaints.map(c => {
                                    const score = c.severity_score || 0;
                                    const color = getSeverityColor(score);
                                    const isAnonymous = (c as any).is_anonymous;
                                    return (
                                        <tr key={c.complaint_id}>
                                            <td>
                                                #{c.complaint_id}
                                                {isAnonymous && <span title="Anonymous" style={{ marginLeft: '4px' }}>🔒</span>}
                                            </td>
                                            <td>{formatDate(c.created_at)}</td>
                                            <td>{isAnonymous ? '🔒 Anonymous' : c.user_id?.substring(0, 8) + '...'}</td>
                                            <td>{c.crime_type || 'N/A'}</td>
                                            <td>₹{(c.financial_loss || 0).toLocaleString('en-IN')}</td>
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
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </>
    );
}
