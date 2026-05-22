import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { getAdminProfile, updateAdminProfile, uploadAdminProfessionalId, type AdminProfile } from '../../api/client';

export default function AdminProfilePage() {
    const { user } = useAuth();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);

    const [profile, setProfile] = useState<Partial<AdminProfile>>({
        full_name: '',
        designation: '',
        department: '',
        office_address: '',
        employee_id: '',
    });

    const [hasProfile, setHasProfile] = useState(false);

    useEffect(() => {
        loadProfile();
    }, [user]);

    async function loadProfile() {
        if (!user?.user_id) return;
        setLoading(true);
        try {
            const result = await getAdminProfile(user.user_id);
            if (result.exists && result.profile) {
                setProfile({
                    full_name: result.profile.full_name || '',
                    designation: result.profile.designation || '',
                    department: result.profile.department || '',
                    office_address: result.profile.office_address || '',
                    employee_id: result.profile.employee_id || '',
                });
                setHasProfile(true);
                // Set uploaded file name if professional_id_path exists
                if (result.profile.professional_id_path) {
                    const pathParts = result.profile.professional_id_path.split('/');
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
            await updateAdminProfile(user.user_id, profile);
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
            await uploadAdminProfessionalId(user.user_id, file);
            setUploadedFileName(file.name);
            setMessage({ type: 'success', text: 'Professional ID uploaded successfully!' });
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

    function handleChange(field: keyof AdminProfile, value: string) {
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
            <h1 className="mb-3">Admin Profile</h1>
            <p className="text-muted mb-4">
                Complete your administrative profile for proper identification.
                {!hasProfile && <strong> Please fill in your professional details and upload your admin ID.</strong>}
            </p>

            {message && (
                <div className={`alert ${message.type === 'success' ? 'alert-success' : 'alert-danger'}`}>
                    {message.text}
                </div>
            )}

            <div className="grid grid-2">
                {/* Professional Information */}
                <div className="card">
                    <h3 className="card-title mb-3">👔 Professional Information</h3>

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

                    <div className="form-group">
                        <label className="form-label">Designation *</label>
                        <input
                            type="text"
                            className="form-input"
                            value={profile.designation}
                            onChange={e => handleChange('designation', e.target.value)}
                            placeholder="e.g., Senior Cyber Crime Officer"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Department *</label>
                        <input
                            type="text"
                            className="form-input"
                            value={profile.department}
                            onChange={e => handleChange('department', e.target.value)}
                            placeholder="e.g., Cyber Crime Cell, Mumbai Police"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Employee ID *</label>
                        <input
                            type="text"
                            className="form-input"
                            value={profile.employee_id}
                            onChange={e => handleChange('employee_id', e.target.value)}
                            placeholder="Enter your employee ID"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Office Address</label>
                        <textarea
                            className="form-textarea"
                            rows={3}
                            value={profile.office_address}
                            onChange={e => handleChange('office_address', e.target.value)}
                            placeholder="Enter your office address"
                        />
                    </div>
                </div>

                {/* ID Verification */}
                <div className="card">
                    <h3 className="card-title mb-3">🪪 Professional ID Verification</h3>
                    <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
                        Upload your official administrative/police ID card for verification. This is mandatory for complaint deletion privileges.
                    </p>

                    <div className="form-group">
                        <label className="form-label">Upload Professional ID *</label>
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
                                            <p style={{ margin: 0, fontWeight: 600, color: 'var(--primary)' }}>ID Uploaded</p>
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
                                        <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🪪</div>
                                        <p className="text-muted" style={{ margin: 0 }}>
                                            Click to upload your official ID<br />
                                            <small>Supports: JPG, PNG, PDF (max 5MB)</small>
                                        </p>
                                    </>
                                )}
                            </div>
                        )}
                    </div>

                    <div className="alert alert-warning" style={{ marginTop: '1rem' }}>
                        <strong>⚠️ Important:</strong> Your professional ID is required for:
                        <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.5rem' }}>
                            <li>Deleting complaints</li>
                            <li>Accessing sensitive user data</li>
                            <li>Audit trail verification</li>
                        </ul>
                    </div>

                    <div className="alert alert-info" style={{ marginTop: '1rem' }}>
                        <strong>🔐 Deletion Password:</strong> Your default deletion password is <code>delete123</code>. 
                        It's recommended to change this from the security settings.
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
