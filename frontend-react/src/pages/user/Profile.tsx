import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { getUserProfile, updateUserProfile, uploadUserGovId, type UserProfile } from '../../api/client';

const GOV_ID_TYPES = [
    { value: '', label: 'Select ID Type' },
    { value: 'aadhaar', label: 'Aadhaar Card' },
    { value: 'pan', label: 'PAN Card' },
    { value: 'passport', label: 'Passport' },
    { value: 'voter_id', label: 'Voter ID' },
    { value: 'driving_license', label: 'Driving License' },
];

const GENDER_OPTIONS = [
    { value: '', label: 'Select Gender' },
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' },
    { value: 'other', label: 'Other' },
];

const INDIAN_STATES = [
    '', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
    'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana',
    'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Delhi', 'Other'
];

export default function Profile() {
    const { user } = useAuth();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);

    const [profile, setProfile] = useState<Partial<UserProfile>>({
        full_name: '',
        date_of_birth: '',
        gender: '',
        address: '',
        city: '',
        state: '',
        pincode: '',
        gov_id_type: '',
        gov_id_number: '',
    });

    const [hasProfile, setHasProfile] = useState(false);

    useEffect(() => {
        loadProfile();
    }, [user]);

    async function loadProfile() {
        if (!user?.user_id) return;
        setLoading(true);
        try {
            const result = await getUserProfile(user.user_id);
            if (result.exists && result.profile) {
                setProfile({
                    full_name: result.profile.full_name || '',
                    date_of_birth: result.profile.date_of_birth || '',
                    gender: result.profile.gender || '',
                    address: result.profile.address || '',
                    city: result.profile.city || '',
                    state: result.profile.state || '',
                    pincode: result.profile.pincode || '',
                    gov_id_type: result.profile.gov_id_type || '',
                    gov_id_number: result.profile.gov_id_number || '',
                });
                setHasProfile(true);
                // Set uploaded file name if gov_id_path exists
                if (result.profile.gov_id_path) {
                    const pathParts = result.profile.gov_id_path.split('/');
                    setUploadedFileName(pathParts[pathParts.length - 1] || 'document_uploaded.file');
                }
            }
        } catch (error) {
            console.error('Error loading profile:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleSave() {
        if (!user?.user_id) return;
        setSaving(true);
        setMessage(null);
        
        try {
            await updateUserProfile(user.user_id, profile);
            setMessage({ type: 'success', text: 'Profile saved successfully!' });
            setHasProfile(true);
        } catch (error) {
            setMessage({ type: 'error', text: 'Failed to save profile' });
        } finally {
            setSaving(false);
        }
    }

    async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0];
        if (!file || !user?.user_id) return;

        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
        if (!validTypes.includes(file.type)) {
            setMessage({ type: 'error', text: 'Please upload a valid image (JPG, PNG) or PDF file' });
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            setMessage({ type: 'error', text: 'File size must be less than 5MB' });
            return;
        }

        setUploading(true);
        setMessage(null);

        try {
            await uploadUserGovId(user.user_id, file);
            setUploadedFileName(file.name);
            setMessage({ type: 'success', text: 'ID document uploaded successfully!' });
        } catch (error) {
            setMessage({ type: 'error', text: 'Failed to upload ID document' });
        } finally {
            setUploading(false);
            // Reset file input so the same file can be selected again
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    }

    function handleReupload() {
        fileInputRef.current?.click();
    }

    function handleChange(field: keyof UserProfile, value: string) {
        setProfile(prev => ({ ...prev, [field]: value }));
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
            <h1 className="mb-3">My Profile</h1>
            <p className="text-muted mb-4">
                Complete your profile to enable full access to all features. 
                {!hasProfile && <strong> Please fill in your details and upload a government ID.</strong>}
            </p>

            {message && (
                <div className={`alert ${message.type === 'success' ? 'alert-success' : 'alert-danger'}`}>
                    {message.text}
                </div>
            )}

            <div className="grid grid-2">
                {/* Personal Information */}
                <div className="card">
                    <h3 className="card-title mb-3">👤 Personal Information</h3>

                    <div className="form-group">
                        <label className="form-label">Full Name *</label>
                        <input
                            type="text"
                            className="form-input"
                            value={profile.full_name}
                            onChange={e => handleChange('full_name', e.target.value)}
                            placeholder="Enter your full name"
                        />
                    </div>

                    <div className="grid grid-2" style={{ gap: '1rem' }}>
                        <div className="form-group">
                            <label className="form-label">Date of Birth</label>
                            <input
                                type="date"
                                className="form-input"
                                value={profile.date_of_birth}
                                onChange={e => handleChange('date_of_birth', e.target.value)}
                            />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Gender</label>
                            <select
                                className="form-select"
                                value={profile.gender}
                                onChange={e => handleChange('gender', e.target.value)}
                            >
                                {GENDER_OPTIONS.map(opt => (
                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Address</label>
                        <textarea
                            className="form-textarea"
                            rows={2}
                            value={profile.address}
                            onChange={e => handleChange('address', e.target.value)}
                            placeholder="Enter your address"
                        />
                    </div>

                    <div className="grid grid-3" style={{ gap: '1rem' }}>
                        <div className="form-group">
                            <label className="form-label">City</label>
                            <input
                                type="text"
                                className="form-input"
                                value={profile.city}
                                onChange={e => handleChange('city', e.target.value)}
                                placeholder="City"
                            />
                        </div>
                        <div className="form-group">
                            <label className="form-label">State</label>
                            <select
                                className="form-select"
                                value={profile.state}
                                onChange={e => handleChange('state', e.target.value)}
                            >
                                {INDIAN_STATES.map(state => (
                                    <option key={state} value={state}>{state || 'Select State'}</option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group">
                            <label className="form-label">Pincode</label>
                            <input
                                type="text"
                                className="form-input"
                                value={profile.pincode}
                                onChange={e => handleChange('pincode', e.target.value)}
                                placeholder="6-digit"
                                maxLength={6}
                            />
                        </div>
                    </div>
                </div>

                {/* ID Verification */}
                <div className="card">
                    <h3 className="card-title mb-3">🪪 Government ID Verification</h3>
                    <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
                        Upload at least one government-issued ID for verification. This helps us process your complaints faster.
                    </p>

                    <div className="form-group">
                        <label className="form-label">ID Type *</label>
                        <select
                            className="form-select"
                            value={profile.gov_id_type}
                            onChange={e => handleChange('gov_id_type', e.target.value)}
                        >
                            {GOV_ID_TYPES.map(opt => (
                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="form-label">ID Number *</label>
                        <input
                            type="text"
                            className="form-input"
                            value={profile.gov_id_number}
                            onChange={e => handleChange('gov_id_number', e.target.value)}
                            placeholder="Enter your ID number"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Upload ID Document *</label>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*,.pdf"
                            onChange={handleFileUpload}
                            style={{ display: 'none' }}
                        />
                        {uploadedFileName ? (
                            /* Uploaded state - show file info and reupload button */
                            <div 
                                style={{
                                    border: '2px solid var(--primary)',
                                    borderRadius: '8px',
                                    padding: '1.5rem',
                                    background: 'rgba(16, 185, 129, 0.1)',
                                    transition: 'all 0.2s'
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                        <div style={{ fontSize: '2rem' }}>✅</div>
                                        <div>
                                            <p style={{ margin: 0, fontWeight: 600, color: 'var(--primary)' }}>Document Uploaded</p>
                                            <p className="text-muted" style={{ margin: 0, fontSize: '0.85rem', wordBreak: 'break-all' }}>
                                                {uploadedFileName}
                                            </p>
                                        </div>
                                    </div>
                                    <button
                                        type="button"
                                        className="btn btn-secondary"
                                        onClick={handleReupload}
                                        style={{ whiteSpace: 'nowrap' }}
                                    >
                                        🔄 Reupload
                                    </button>
                                </div>
                            </div>
                        ) : (
                            /* Not uploaded state - show upload prompt */
                            <div 
                                className="file-upload-area"
                                onClick={() => fileInputRef.current?.click()}
                                style={{
                                    border: '2px dashed var(--border-color)',
                                    borderRadius: '8px',
                                    padding: '2rem',
                                    textAlign: 'center',
                                    cursor: 'pointer',
                                    background: 'var(--glass-bg)',
                                    transition: 'all 0.2s'
                                }}
                            >
                                {uploading ? (
                                    <div className="spinner" style={{ margin: '0 auto' }} />
                                ) : (
                                    <>
                                        <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📄</div>
                                        <p className="text-muted" style={{ margin: 0 }}>
                                            Click to upload your ID document<br />
                                            <small>Supports: JPG, PNG, PDF (max 5MB)</small>
                                        </p>
                                    </>
                                )}
                            </div>
                        )}
                    </div>

                    <div className="alert alert-info" style={{ marginTop: '1rem' }}>
                        <strong>🔒 Privacy Note:</strong> Your ID documents are securely stored and only accessible to authorized officials for verification purposes.
                    </div>
                </div>
            </div>

            <div className="card" style={{ marginTop: '1rem' }}>
                <button 
                    className="btn btn-primary btn-lg btn-block"
                    onClick={handleSave}
                    disabled={saving}
                >
                    {saving ? <div className="spinner" /> : '💾 Save Profile'}
                </button>
            </div>
        </>
    );
}
