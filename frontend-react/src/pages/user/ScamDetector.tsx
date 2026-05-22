import { useState } from 'react';
import { analyzeScamText, analyzeScamAudio } from '../../api/client';

export default function ScamDetector() {
    const [mode, setMode] = useState<'audio' | 'text'>('text');
    const [textInput, setTextInput] = useState('');
    const [audioFile, setAudioFile] = useState<File | null>(null);
    const [language, setLanguage] = useState('en');
    const [loading, setLoading] = useState(false);
    const [analysisStatus, setAnalysisStatus] = useState('');
    const [result, setResult] = useState<{ classification: string; reason: string; transcript?: string } | null>(null);

    async function handleTextAnalysis() {
        if (!textInput.trim()) {
            alert('Please enter call transcript');
            return;
        }

        setLoading(true);
        setResult(null);
        setAnalysisStatus('Analyzing transcript for scam patterns...');

        try {
            const res = await analyzeScamText(textInput);
            setResult(res);
        } catch (err) {
            setResult({ classification: 'Error', reason: err instanceof Error ? err.message : 'Unknown error' });
        } finally {
            setLoading(false);
            setAnalysisStatus('');
        }
    }

    async function handleAudioAnalysis() {
        if (!audioFile) {
            alert('Please select an audio file');
            return;
        }

        setLoading(true);
        setResult(null);
        setAnalysisStatus('Uploading audio file...');

        try {
            setAnalysisStatus('Transcribing audio...');
            await new Promise(r => setTimeout(r, 500)); // Brief pause for UX
            setAnalysisStatus('Analyzing for scam indicators...');
            const res = await analyzeScamAudio(audioFile, language);
            setResult(res);
        } catch (err) {
            setResult({ classification: 'Error', reason: err instanceof Error ? err.message : 'Unknown error' });
        } finally {
            setLoading(false);
            setAnalysisStatus('');
        }
    }

    const isScam = result?.classification === 'Scam';
    const isError = result?.classification === 'Error';

    return (
        <>
            <h1 className="mb-2">📞 Call Scam Detector</h1>
            <p className="text-muted mb-4">
                Analyze suspicious phone calls to determine if they contain scam patterns or fraudulent intent.
            </p>

            {/* Info Section */}
            <div className="info-section">
                <div className="info-section-title">🔍 What We Analyze</div>
                <ul className="info-list">
                    <li>Urgency tactics and pressure language</li>
                    <li>Requests for personal information or OTPs</li>
                    <li>Impersonation of banks, government, or officials</li>
                    <li>Threats or scare tactics</li>
                    <li>Too-good-to-be-true offers or lottery claims</li>
                </ul>
            </div>

            {/* Mode Selector */}
            <div className="card mb-3">
                <div className="d-flex gap-1 mb-3">
                    <button 
                        className={`btn ${mode === 'text' ? 'btn-primary' : 'btn-outline'}`}
                        onClick={() => setMode('text')}
                    >
                        📝 Text Transcript
                    </button>
                    <button 
                        className={`btn ${mode === 'audio' ? 'btn-primary' : 'btn-outline'}`}
                        onClick={() => setMode('audio')}
                    >
                        🎤 Audio Recording
                    </button>
                </div>

                {mode === 'text' ? (
                    <div>
                        <div className="form-group">
                            <label className="form-label">Call Transcript</label>
                            <textarea
                                className="form-textarea"
                                rows={6}
                                value={textInput}
                                onChange={e => setTextInput(e.target.value)}
                                placeholder="Paste what the caller said here...&#10;&#10;Example: 'This is from your bank. Your account has been compromised. Please share your OTP to verify your identity.'"
                                disabled={loading}
                            />
                            <p className="form-hint">Tip: Include as much detail as possible for accurate analysis</p>
                        </div>
                        <button 
                            className="btn btn-primary btn-lg" 
                            onClick={handleTextAnalysis} 
                            disabled={loading || !textInput.trim()}
                        >
                            {loading ? 'Analyzing...' : '🔍 Analyze Transcript'}
                        </button>
                    </div>
                ) : (
                    <div>
                        <div className="form-group">
                            <label className="form-label">Upload Call Recording</label>
                            <input
                                type="file"
                                className="form-input"
                                accept="audio/*"
                                onChange={e => setAudioFile(e.target.files?.[0] || null)}
                                disabled={loading}
                            />
                            <p className="form-hint">Supported: MP3, WAV, M4A (max 10MB)</p>
                        </div>
                        <div className="form-group">
                            <label className="form-label">Audio Language</label>
                            <select 
                                className="form-select" 
                                value={language} 
                                onChange={e => setLanguage(e.target.value)}
                                disabled={loading}
                            >
                                <option value="en">English</option>
                                <option value="hi">Hindi</option>
                            </select>
                        </div>
                        <button 
                            className="btn btn-primary btn-lg" 
                            onClick={handleAudioAnalysis} 
                            disabled={loading || !audioFile}
                        >
                            {loading ? 'Processing...' : '🔍 Analyze Recording'}
                        </button>
                    </div>
                )}
            </div>

            {/* Loading State */}
            {loading && (
                <div className="analysis-progress">
                    <div className="spinner" />
                    <div>
                        <div className="analysis-status">{analysisStatus}</div>
                        <div className="analysis-substatus">This may take a few moments...</div>
                    </div>
                </div>
            )}

            {/* Results */}
            {result && !loading && (
                <div className="result-card">
                    <div className={`result-header ${isScam ? 'danger' : isError ? 'warning' : 'safe'}`}>
                        <span style={{ fontSize: '1.5rem' }}>
                            {isScam ? '🚨' : isError ? '❌' : '✅'}
                        </span>
                        <div>
                            <strong style={{ fontSize: '1.1rem' }}>{result.classification}</strong>
                            {result.classification === 'Scam' && (
                                <span style={{ display: 'block', fontSize: '0.85rem', color: 'var(--danger)' }}>
                                    High probability of fraudulent call
                                </span>
                            )}
                            {result.classification === 'Legitimate' && (
                                <span style={{ display: 'block', fontSize: '0.85rem', color: 'var(--success)' }}>
                                    No scam indicators detected
                                </span>
                            )}
                        </div>
                    </div>
                    <div className="result-body">
                        {result.transcript && (
                            <div className="mb-2">
                                <strong>Transcription:</strong>
                                <p style={{ marginTop: '0.5rem', padding: '1rem', background: 'var(--gray-50)', borderRadius: 'var(--radius-md)' }}>
                                    {result.transcript}
                                </p>
                            </div>
                        )}
                        <div>
                            <strong>Analysis:</strong>
                            <p style={{ marginTop: '0.5rem' }}>{result.reason}</p>
                        </div>

                        {isScam && (
                            <div className="next-steps">
                                <div className="next-steps-title">📋 Recommended Actions</div>
                                <ul className="info-list" style={{ marginTop: '0.5rem' }}>
                                    <li>Do not respond to or call back this number</li>
                                    <li>Never share OTPs, passwords, or bank details</li>
                                    <li>Block the caller's number</li>
                                    <li>Report to the National Cyber Crime Portal</li>
                                </ul>
                                <button 
                                    className="btn btn-primary mt-2"
                                    onClick={() => window.location.href = '/dashboard/complaints/new'}
                                >
                                    📝 File a Complaint
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </>
    );
}
