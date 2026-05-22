import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { submitComplaintAnonymous, checkProfileComplete } from '../../api/client';
import FileUpload from '../../components/FileUpload';

export default function RegisterComplaint() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [complaintText, setComplaintText] = useState('');
    const [isAnonymous, setIsAnonymous] = useState(false);
    const [pdfFile, setPdfFile] = useState<File | null>(null);
    const [imageFile, setImageFile] = useState<File | null>(null);
    const [audioFile, setAudioFile] = useState<File | null>(null);
    const [videoFile, setVideoFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<{ success: boolean; complaint_id?: string; message?: string } | null>(null);
    
    // Profile check state
    const [profileComplete, setProfileComplete] = useState<boolean | null>(null);
    const [profileMissing, setProfileMissing] = useState<string[]>([]);
    const [checkingProfile, setCheckingProfile] = useState(true);

    useEffect(() => {
        checkProfile();
    }, [user]);

    async function checkProfile() {
        if (!user?.user_id) return;
        
        setCheckingProfile(true);
        try {
            const result = await checkProfileComplete(user.user_id, 'user');
            setProfileComplete(result.complete);
            setProfileMissing(result.missing || []);
        } catch (error) {
            console.error('Error checking profile:', error);
            // Allow access if check fails
            setProfileComplete(true);
        } finally {
            setCheckingProfile(false);
        }
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!complaintText.trim()) {
            alert('Please enter complaint details');
            return;
        }

        setLoading(true);
        setResult(null);

        try {
            const files: { pdf?: File; image?: File; audio?: File; video?: File } = {};
            if (pdfFile) files.pdf = pdfFile;
            if (imageFile) files.image = imageFile;
            if (audioFile) files.audio = audioFile;
            if (videoFile) files.video = videoFile;

            const response = await submitComplaintAnonymous(
                complaintText, 
                user?.user_id || 'guest', 
                isAnonymous,
                files
            );
            setResult(response);

            if (response.success) {
                // Clear form
                setComplaintText('');
                setIsAnonymous(false);
                setPdfFile(null);
                setImageFile(null);
                setAudioFile(null);
                setVideoFile(null);
                // Clear file inputs
                const inputs = document.querySelectorAll('input[type="file"]');
                inputs.forEach((input) => (input as HTMLInputElement).value = '');
            }
        } catch (err) {
            setResult({ success: false, message: err instanceof Error ? err.message : 'Error submitting complaint' });
        } finally {
            setLoading(false);
        }
    }

    if (checkingProfile) {
        return (
            <div className="text-center p-4">
                <div className="spinner" style={{ margin: '0 auto' }} />
                <p className="text-muted mt-2">Checking profile status...</p>
            </div>
        );
    }

    // Profile incomplete - show warning
    if (!profileComplete) {
        return (
            <>
                <h1 className="mb-3">Register a Complaint</h1>
                
                <div className="card" style={{
                    background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
                    border: '2px solid #f59e0b',
                    textAlign: 'center',
                    padding: '3rem'
                }}>
                    <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>⚠️</div>
                    <h2 style={{ color: '#92400e', marginBottom: '1rem' }}>Profile Incomplete</h2>
                    <p style={{ color: '#78350f', marginBottom: '1.5rem', fontSize: '1.1rem' }}>
                        You must complete your profile and upload a government ID before filing a complaint.
                    </p>
                    
                    <div className="alert alert-warning" style={{ textAlign: 'left', maxWidth: '400px', margin: '0 auto 1.5rem' }}>
                        <strong>Missing Information:</strong>
                        <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.25rem' }}>
                            {profileMissing.includes('profile') && <li>Profile not created</li>}
                            {profileMissing.includes('full_name') && <li>Full Name</li>}
                            {profileMissing.includes('gov_id') && <li>Government ID Upload</li>}
                        </ul>
                    </div>
                    
                    <button 
                        className="btn btn-primary btn-lg"
                        onClick={() => navigate('/dashboard/profile')}
                    >
                        Complete My Profile →
                    </button>
                </div>
            </>
        );
    }

    return (
        <>
            <h1 className="mb-3">Register a Complaint</h1>
            <p className="text-muted mb-4">Provide details about the cybercrime incident. Attach any evidence you have.</p>

            <div className="card">
                <form onSubmit={handleSubmit}>
                    {/* Anonymous Toggle */}
                    <div className="anonymous-toggle-section" style={{
                        background: isAnonymous ? 'linear-gradient(135deg, #1e3a5f 0%, #2d4a6f 100%)' : 'var(--glass-bg)',
                        border: `2px solid ${isAnonymous ? 'var(--primary)' : 'var(--border-color)'}`,
                        borderRadius: '12px',
                        padding: '1.25rem',
                        marginBottom: '1.5rem',
                        transition: 'all 0.3s ease'
                    }}>
                        <div className="d-flex align-center gap-3">
                            <label className="toggle-switch" style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                                <input
                                    type="checkbox"
                                    checked={isAnonymous}
                                    onChange={e => setIsAnonymous(e.target.checked)}
                                    style={{ display: 'none' }}
                                />
                                <div style={{
                                    width: '52px',
                                    height: '28px',
                                    background: isAnonymous ? 'var(--success)' : 'var(--gray-400)',
                                    borderRadius: '14px',
                                    position: 'relative',
                                    transition: 'all 0.3s ease'
                                }}>
                                    <div style={{
                                        width: '22px',
                                        height: '22px',
                                        background: 'white',
                                        borderRadius: '50%',
                                        position: 'absolute',
                                        top: '3px',
                                        left: isAnonymous ? '27px' : '3px',
                                        transition: 'all 0.3s ease',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                                    }} />
                                </div>
                            </label>
                            <div style={{ flex: 1 }}>
                                <div style={{ 
                                    fontWeight: '600', 
                                    fontSize: '1rem',
                                    color: isAnonymous ? 'white' : 'var(--text-primary)'
                                }}>
                                    🔒 File Anonymously
                                </div>
                                <p style={{ 
                                    margin: '0.25rem 0 0', 
                                    fontSize: '0.85rem',
                                    color: isAnonymous ? 'rgba(255,255,255,0.8)' : 'var(--text-muted)'
                                }}>
                                    {isAnonymous 
                                        ? 'Your identity will be hidden from admins. You can still track this complaint in "My Complaints".'
                                        : 'Your user information will be shared with investigating officers.'
                                    }
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Complaint Details *</label>
                        <textarea
                            className="form-textarea"
                            rows={6}
                            value={complaintText}
                            onChange={e => setComplaintText(e.target.value)}
                            placeholder="Describe the incident in detail. Include dates, amounts, names, and how it happened..."
                            required
                        />
                        <p className="form-hint">Be as detailed as possible. This helps in investigation.</p>
                    </div>

                    <h4 className="mb-2">Attach Evidence (Optional)</h4>

                    <div className="grid grid-2 mb-3">
                        <FileUpload
                            label="PDF Document"
                            accept=".pdf"
                            file={pdfFile}
                            onFileSelect={setPdfFile}
                            icon="📕"
                        />
                        <FileUpload
                            label="Image (Screenshot)"
                            accept="image/*"
                            file={imageFile}
                            onFileSelect={setImageFile}
                            icon="🖼️"
                        />
                        <FileUpload
                            label="Audio Recording"
                            accept="audio/*"
                            file={audioFile}
                            onFileSelect={setAudioFile}
                            icon="🎵"
                        />
                        <FileUpload
                            label="Video Evidence"
                            accept="video/*"
                            file={videoFile}
                            onFileSelect={setVideoFile}
                            icon="🎬"
                        />
                    </div>

                    <button type="submit" className="btn btn-primary btn-lg btn-block" disabled={loading}>
                        {loading ? <><div className="spinner" /> Processing...</> : (
                            isAnonymous ? '🔒 Submit Anonymous Complaint' : 'Submit Complaint'
                        )}
                    </button>
                </form>
            </div>

            {result && (
                <div className="card" style={{
                    background: result.success
                        ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                        : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                    color: 'white',
                    textAlign: 'center',
                    padding: '2rem'
                }}>
                    <span style={{ fontSize: '4rem', display: 'block', marginBottom: '1rem' }}>
                        {result.success ? '✅' : '❌'}
                    </span>
                    <h2 style={{ margin: '0 0 0.5rem 0', color: 'white' }}>
                        {result.success ? 'Complaint Registered Successfully!' : 'Error Processing Complaint'}
                    </h2>
                    {result.complaint_id && (
                        <p style={{ margin: 0, opacity: 0.9, fontSize: '1.1rem' }}>
                            Complaint ID: <strong>{result.complaint_id}</strong>
                        </p>
                    )}
                    <p style={{ margin: '0.5rem 0 0 0', opacity: 0.8 }}>
                        {result.success
                            ? 'Your complaint has been submitted and will be reviewed by our team.'
                            : result.message}
                    </p>
                </div>
            )}
        </>
    );
}
