import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeMaliciousText } from '../../api/client';

interface MaliciousResult {
    threat_score: number;
    intent_classification: string;
    social_tactics_detected: string[];
    ioc_detected: string[];
    summary: string;
}

export default function MaliciousDetector() {
    const navigate = useNavigate();
    const [textInput, setTextInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<MaliciousResult | null>(null);

    async function handleAnalysis() {
        if (!textInput.trim()) {
            alert('Please enter text to analyze');
            return;
        }

        setLoading(true);
        setResult(null);

        try {
            const res = await analyzeMaliciousText(textInput);
            setResult(res);
        } catch (err) {
            alert(err instanceof Error ? err.message : 'Error analyzing text');
        } finally {
            setLoading(false);
        }
    }

    const getThreatLevel = (score: number) => {
        if (score >= 7) return { level: 'High', class: 'danger', icon: '🚨' };
        if (score >= 4) return { level: 'Medium', class: 'warning', icon: '⚠️' };
        return { level: 'Low', class: 'safe', icon: '✅' };
    };

    const threat = result ? getThreatLevel(result.threat_score) : null;

    return (
        <>
            <h1 className="mb-2">⚠️ Malicious Text Detector</h1>
            <p className="text-muted mb-4">
                Analyze suspicious messages, emails, or chat conversations for phishing, scam attempts, or malicious content.
            </p>

            {/* Info Section */}
            <div className="info-section">
                <div className="info-section-title">🛡️ What We Analyze</div>
                <ul className="info-list">
                    <li>Phishing links and deceptive URLs</li>
                    <li>Social engineering tactics (urgency, fear, authority)</li>
                    <li>Requests for sensitive information</li>
                    <li>Impersonation attempts</li>
                    <li>Malware indicators and suspicious attachments</li>
                </ul>
            </div>

            <div className="card">
                <div className="form-group">
                    <label className="form-label">Suspicious Message</label>
                    <textarea
                        className="form-textarea"
                        rows={8}
                        value={textInput}
                        onChange={e => setTextInput(e.target.value)}
                        placeholder="Paste the suspicious email, SMS, WhatsApp message, or chat here...&#10;&#10;Example: 'Congratulations! You have won Rs. 50 lakhs in our lucky draw. Click here to claim: bit.ly/claim-prize. Share your bank details for instant transfer.'"
                        disabled={loading}
                    />
                    <p className="form-hint">Include the complete message including any links for accurate analysis.</p>
                </div>
                <button 
                    className="btn btn-primary btn-lg" 
                    onClick={handleAnalysis} 
                    disabled={loading || !textInput.trim()}
                >
                    {loading ? (
                        <>
                            <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }} />
                            <span style={{ marginLeft: '8px' }}>Analyzing...</span>
                        </>
                    ) : '🔍 Analyze for Threats'}
                </button>
            </div>

            {/* Loading State */}
            {loading && (
                <div className="analysis-progress mt-3">
                    <div className="spinner" />
                    <div>
                        <div className="analysis-status">Scanning for threats...</div>
                        <div className="analysis-substatus">Checking for phishing, social engineering, and malware indicators</div>
                    </div>
                </div>
            )}

            {/* Results */}
            {result && !loading && threat && (
                <div className="result-card">
                    <div className={`result-header ${threat.class}`}>
                        <span style={{ fontSize: '1.5rem' }}>{threat.icon}</span>
                        <div style={{ flex: 1 }}>
                            <strong style={{ fontSize: '1.1rem' }}>
                                Threat Score: {result.threat_score}/10 — {threat.level} Risk
                            </strong>
                            <span style={{ display: 'block', fontSize: '0.85rem', marginTop: '4px' }}>
                                {result.intent_classification}
                            </span>
                        </div>
                    </div>
                    <div className="result-body">
                        <div className="mb-3">
                            <strong>Analysis Summary:</strong>
                            <p style={{ marginTop: '0.5rem', lineHeight: '1.6' }}>{result.summary}</p>
                        </div>

                        {result.social_tactics_detected.length > 0 && (
                            <div className="mb-3">
                                <strong style={{ color: 'var(--warning)' }}>⚠️ Social Engineering Tactics Detected:</strong>
                                <ul style={{ marginTop: '0.5rem', paddingLeft: '1.25rem' }}>
                                    {result.social_tactics_detected.map((t, i) => (
                                        <li key={i} style={{ marginBottom: '4px', color: 'var(--text-secondary)' }}>{t}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {result.ioc_detected.length > 0 && (
                            <div className="mb-3">
                                <strong style={{ color: 'var(--danger)' }}>🔴 Indicators of Compromise:</strong>
                                <ul style={{ marginTop: '0.5rem', paddingLeft: '1.25rem' }}>
                                    {result.ioc_detected.map((ioc, idx) => (
                                        <li key={idx} style={{ marginBottom: '4px', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>{ioc}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Next Steps based on threat level */}
                        <div className="next-steps">
                            <div className="next-steps-title">📋 Recommended Actions</div>
                            {result.threat_score >= 7 ? (
                                <ul className="info-list" style={{ marginTop: '0.5rem' }}>
                                    <li>Do NOT click any links in this message</li>
                                    <li>Do NOT reply or provide any information</li>
                                    <li>Block the sender immediately</li>
                                    <li>Report this to the National Cyber Crime Portal</li>
                                    <li>If you've already clicked links, change passwords immediately</li>
                                </ul>
                            ) : result.threat_score >= 4 ? (
                                <ul className="info-list" style={{ marginTop: '0.5rem' }}>
                                    <li>Verify the sender through official channels before responding</li>
                                    <li>Do not share sensitive information via this channel</li>
                                    <li>Be cautious of any links or attachments</li>
                                    <li>Contact the organization directly using known contact info</li>
                                </ul>
                            ) : (
                                <ul className="info-list" style={{ marginTop: '0.5rem' }}>
                                    <li>No immediate threats detected, but stay vigilant</li>
                                    <li>Verify sender identity for unusual requests</li>
                                    <li>Keep your security software up to date</li>
                                </ul>
                            )}
                            
                            {result.threat_score >= 7 && (
                                <button 
                                    className="btn btn-primary mt-3"
                                    onClick={() => navigate('/dashboard/complaints/new')}
                                >
                                    📝 Report This & File Complaint
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
