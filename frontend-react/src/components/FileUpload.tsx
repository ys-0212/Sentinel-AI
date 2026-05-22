import { useRef } from 'react';

interface FileUploadProps {
    label: string;
    accept: string;
    file: File | null;
    onFileSelect: (file: File | null) => void;
    icon?: string;
}

export default function FileUpload({ label, accept, file, onFileSelect, icon = '📄' }: FileUploadProps) {
    const inputRef = useRef<HTMLInputElement>(null);

    function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
        const selectedFile = e.target.files?.[0] || null;
        onFileSelect(selectedFile);
    }

    function handleRemove() {
        onFileSelect(null);
        if (inputRef.current) {
            inputRef.current.value = '';
        }
    }

    function handleClick() {
        inputRef.current?.click();
    }

    function formatFileSize(bytes: number): string {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function getFileIcon(fileName: string): string {
        const ext = fileName.split('.').pop()?.toLowerCase() || '';
        if (['pdf'].includes(ext)) return '📕';
        if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext)) return '🖼️';
        if (['mp3', 'wav', 'ogg', 'm4a', 'aac'].includes(ext)) return '🎵';
        if (['mp4', 'mov', 'avi', 'mkv', 'webm'].includes(ext)) return '🎬';
        return icon;
    }

    return (
        <div className="form-group">
            <label className="form-label">{label}</label>
            
            <input
                ref={inputRef}
                type="file"
                accept={accept}
                onChange={handleChange}
                style={{ display: 'none' }}
            />

            {!file ? (
                // Upload area when no file selected
                <div
                    onClick={handleClick}
                    style={{
                        border: '2px dashed var(--border-color)',
                        borderRadius: '12px',
                        padding: '1.5rem',
                        textAlign: 'center',
                        cursor: 'pointer',
                        background: 'var(--glass-bg)',
                        transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = 'var(--primary)';
                        e.currentTarget.style.background = 'rgba(var(--primary-rgb), 0.05)';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = 'var(--border-color)';
                        e.currentTarget.style.background = 'var(--glass-bg)';
                    }}
                >
                    <div style={{ fontSize: '2rem', marginBottom: '0.5rem', opacity: 0.6 }}>
                        {icon}
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        Click to upload
                    </div>
                </div>
            ) : (
                // File preview when file is selected
                <div
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        padding: '0.75rem 1rem',
                        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
                        border: '1px solid var(--success)',
                        borderRadius: '12px'
                    }}
                >
                    <div style={{ fontSize: '1.75rem' }}>
                        {getFileIcon(file.name)}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ 
                            fontWeight: 500, 
                            color: 'var(--success)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            fontSize: '0.9rem'
                        }}>
                            {file.name}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            {formatFileSize(file.size)}
                        </div>
                    </div>
                    <div className="d-flex gap-1">
                        <button
                            type="button"
                            onClick={handleClick}
                            className="btn btn-sm btn-outline"
                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                            title="Replace file"
                        >
                            🔄
                        </button>
                        <button
                            type="button"
                            onClick={handleRemove}
                            className="btn btn-sm"
                            style={{ 
                                padding: '0.25rem 0.5rem', 
                                fontSize: '0.75rem',
                                background: 'var(--danger)',
                                color: 'white',
                                border: 'none'
                            }}
                            title="Remove file"
                        >
                            ✕
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
