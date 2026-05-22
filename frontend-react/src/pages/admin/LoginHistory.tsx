import { useState, useEffect } from 'react';
import { getLoginHistory, formatDate, type LoginHistory as LoginHistoryType } from '../../api/client';

export default function LoginHistory() {
    const [history, setHistory] = useState<LoginHistoryType[]>([]);
    const [loading, setLoading] = useState(true);
    const [userTypeFilter, setUserTypeFilter] = useState('');
    const [expandedRow, setExpandedRow] = useState<number | null>(null);

    useEffect(() => {
        loadHistory();
    }, [userTypeFilter]);

    async function loadHistory() {
        setLoading(true);
        try {
            const data = await getLoginHistory(userTypeFilter || undefined, 100);
            setHistory(data.login_history || []);
        } catch (error) {
            console.error('Error loading login history:', error);
        } finally {
            setLoading(false);
        }
    }

    function toggleExpand(id: number) {
        setExpandedRow(expandedRow === id ? null : id);
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
            <h1 className="mb-3">Login History</h1>
            <p className="text-muted mb-4">View all login attempts with typing biometrics, IP tracking, and security analysis.</p>

            <div className="card mb-3">
                <div className="d-flex gap-2">
                    <select
                        className="form-select"
                        style={{ width: 'auto' }}
                        value={userTypeFilter}
                        onChange={e => setUserTypeFilter(e.target.value)}
                    >
                        <option value="">All Users</option>
                        <option value="user">Users Only</option>
                        <option value="admin">Admins Only</option>
                    </select>
                </div>
            </div>

            <div className="card">
                <div className="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th></th>
                                <th>Time</th>
                                <th>User</th>
                                <th>Type</th>
                                <th>Typing Speed</th>
                                <th>IP Address</th>
                                <th>IP Change</th>
                                <th>VPN</th>
                                <th>Location</th>
                                <th>Risk Score</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {history.length === 0 ? (
                                <tr>
                                    <td colSpan={11} className="text-center text-muted">No login history found</td>
                                </tr>
                            ) : (
                                history.map(login => {
                                    const riskClass = login.risk_score >= 0.7 ? 'badge-danger' : login.risk_score >= 0.4 ? 'badge-pending' : 'badge-solved';
                                    const isExpanded = expandedRow === login.id;
                                    return (
                                        <>
                                            <tr key={login.id} onClick={() => toggleExpand(login.id)} style={{ cursor: 'pointer' }}>
                                                <td style={{ width: '30px' }}>
                                                    <span style={{ fontSize: '0.8rem' }}>{isExpanded ? '▼' : '▶'}</span>
                                                </td>
                                                <td>{formatDate(login.login_time)}</td>
                                                <td>{login.user_name || 'Unknown'}</td>
                                                <td>
                                                    <span className={`badge ${login.user_type === 'admin' ? 'badge-pending' : 'badge-ongoing'}`}>
                                                        {login.user_type}
                                                    </span>
                                                </td>
                                                <td>
                                                    {login.typing_speed || 0} WPM
                                                    {login.captcha_typing_speed ? (
                                                        <span className="text-muted" style={{ fontSize: '0.75rem', display: 'block' }}>
                                                            CAPTCHA: {login.captcha_typing_speed} WPM
                                                        </span>
                                                    ) : null}
                                                </td>
                                                <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{login.ip_address || 'N/A'}</td>
                                                <td>
                                                    {login.ip_disparity ? (
                                                        <span className="badge badge-danger" title={`Previous: ${login.previous_ip}`}>
                                                            ⚠️ Changed
                                                        </span>
                                                    ) : (
                                                        <span className="badge badge-solved">Same</span>
                                                    )}
                                                </td>
                                                <td>
                                                    <span className={`badge ${login.vpn_detected ? 'badge-danger' : 'badge-solved'}`}>
                                                        {login.vpn_detected ? 'Yes' : 'No'}
                                                    </span>
                                                </td>
                                                <td>{login.location || 'Unknown'}</td>
                                                <td>
                                                    <span className={`badge ${riskClass}`}>
                                                        {(login.risk_score * 100).toFixed(0)}%
                                                    </span>
                                                </td>
                                                <td>
                                                    <span className={`badge ${login.is_anomaly ? 'badge-danger' : 'badge-solved'}`}>
                                                        {login.is_anomaly ? 'Anomaly' : 'Normal'}
                                                    </span>
                                                </td>
                                            </tr>
                                            {isExpanded && (
                                                <tr key={`${login.id}-details`} className="expanded-row">
                                                    <td colSpan={11}>
                                                        <div className="login-details-panel">
                                                            <div className={`grid ${login.ip_disparity && login.previous_ip ? 'grid-3' : 'grid-2'}`} style={{ gap: '1rem', padding: '1rem', background: 'var(--glass-bg)', borderRadius: '8px' }}>
                                                                <div>
                                                                    <strong>Session Details</strong>
                                                                    <p className="text-muted" style={{ fontSize: '0.85rem', margin: '0.5rem 0 0' }}>
                                                                        Form Time: {login.form_completion_time || 0}s<br />
                                                                        Device: {login.device_fingerprint || 'web-client'}
                                                                    </p>
                                                                </div>
                                                                {login.ip_disparity && login.previous_ip ? (
                                                                    <div>
                                                                        <strong>IP Disparity Detected</strong>
                                                                        <p style={{ fontSize: '0.85rem', margin: '0.5rem 0 0' }}>
                                                                            <span className="text-muted">Previous IP:</span>{' '}
                                                                            <code style={{ color: 'var(--danger)' }}>{login.previous_ip}</code><br />
                                                                            <span className="text-muted">Current IP:</span>{' '}
                                                                            <code>{login.ip_address}</code>
                                                                        </p>
                                                                    </div>
                                                                ) : null}
                                                                <div>
                                                                    <strong>Security Analysis</strong>
                                                                    <p className="text-muted" style={{ fontSize: '0.85rem', margin: '0.5rem 0 0' }}>
                                                                        VPN/Proxy: {login.vpn_detected ? '⚠️ Detected' : '✓ Not detected'}<br />
                                                                        Risk Level: {login.risk_score >= 0.7 ? '🔴 High' : login.risk_score >= 0.4 ? '🟡 Medium' : '🟢 Low'}
                                                                    </p>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </td>
                                                </tr>
                                            )}
                                        </>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="card mt-3">
                <h3 className="card-title">Legend</h3>
                <div className="d-flex gap-3 flex-wrap" style={{ marginTop: '1rem' }}>
                    <div><span className="badge badge-solved">Same IP</span> - IP address matches previous logins</div>
                    <div><span className="badge badge-danger">⚠️ Changed</span> - New IP detected (potential security risk)</div>
                    <div><span className="badge badge-danger">VPN: Yes</span> - VPN/Proxy usage detected</div>
                </div>
            </div>
        </>
    );
}
