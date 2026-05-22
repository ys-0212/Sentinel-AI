import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import { registerUserEnhanced } from '../api/client';

export default function Register() {
    const navigate = useNavigate();
    const { theme, toggleTheme } = useTheme();

    // Form state
    const [fullName, setFullName] = useState('');
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [phone, setPhone] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    const formStartRef = useRef(Date.now());

    useEffect(() => {
        formStartRef.current = Date.now();
    }, []);

    function validateForm(): boolean {
        if (!fullName.trim()) {
            setError('Please enter your full name');
            return false;
        }
        if (!username.trim() || username.length < 3) {
            setError('Username must be at least 3 characters');
            return false;
        }
        if (!email.includes('@')) {
            setError('Please enter a valid email');
            return false;
        }
        if (!phone.match(/^\d{10}$/)) {
            setError('Please enter a valid 10-digit phone number');
            return false;
        }
        if (password.length < 6) {
            setError('Password must be at least 6 characters');
            return false;
        }
        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return false;
        }
        return true;
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!validateForm()) return;
        
        setLoading(true);
        setError('');
        
        try {
            const result = await registerUserEnhanced(
                fullName,
                username,
                email,
                phone,
                password
            );
            
            if (result.success) {
                setSuccess(true);
            } else {
                setError(result.message || 'Registration failed');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Registration failed');
        } finally {
            setLoading(false);
        }
    }

    if (success) {
        return (
            <div className="login-container">
                <div className="login-card" style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>✅</div>
                    <h1 style={{ color: 'var(--success)', marginBottom: '1rem' }}>Registration Successful!</h1>
                    <p className="text-muted" style={{ marginBottom: '2rem' }}>
                        Your account has been created and your profile is ready.
                    </p>
                    <button 
                        className="btn btn-primary btn-lg"
                        onClick={() => navigate('/login')}
                    >
                        Proceed to Login
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="login-container">
            {/* Theme toggle */}
            <button
                onClick={toggleTheme}
                className="btn btn-outline"
                style={{
                    position: 'absolute',
                    top: '1rem',
                    right: '1rem',
                    background: 'rgba(255,255,255,0.15)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    color: 'white',
                    padding: '0.5rem 1rem',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    zIndex: 10
                }}
            >
                {theme === 'light' ? '🌙' : '☀️'}
            </button>

            <div className="login-card">
                <div className="login-logo">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    </svg>
                    <h1>CyberSafe</h1>
                    <p className="text-muted">Create Your Account</p>
                </div>

                {error && <div className="alert alert-danger">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Full Name *</label>
                        <input
                            type="text"
                            className="form-input"
                            value={fullName}
                            onChange={e => setFullName(e.target.value)}
                            placeholder="Enter your full name"
                            required
                        />
                        <div className="form-hint">Your name as per official documents</div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Username *</label>
                        <input
                            type="text"
                            className="form-input"
                            value={username}
                            onChange={e => setUsername(e.target.value.toLowerCase().replace(/\s/g, ''))}
                            placeholder="Choose a username for login"
                            required
                        />
                        <div className="form-hint">Used for logging in (no spaces)</div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Email *</label>
                        <input
                            type="email"
                            className="form-input"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            placeholder="your.email@example.com"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Phone Number *</label>
                        <input
                            type="tel"
                            className="form-input"
                            value={phone}
                            onChange={e => setPhone(e.target.value.replace(/\D/g, ''))}
                            placeholder="10-digit mobile number"
                            maxLength={10}
                            required
                        />
                    </div>

                    <div className="grid grid-2" style={{ gap: '1rem' }}>
                        <div className="form-group">
                            <label className="form-label">Password *</label>
                            <input
                                type="password"
                                className="form-input"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                placeholder="Min 6 characters"
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label className="form-label">Confirm Password *</label>
                            <input
                                type="password"
                                className="form-input"
                                value={confirmPassword}
                                onChange={e => setConfirmPassword(e.target.value)}
                                placeholder="Confirm password"
                                required
                            />
                        </div>
                    </div>

                    <button type="submit" className="btn btn-primary btn-lg btn-block" disabled={loading}>
                        {loading ? <div className="spinner" /> : 'Create Account'}
                    </button>
                </form>

                <p className="text-center mt-3">
                    Already have an account?{' '}
                    <a href="/login" onClick={e => { e.preventDefault(); navigate('/login'); }}>
                        Login here
                    </a>
                </p>
            </div>
        </div>
    );
}
