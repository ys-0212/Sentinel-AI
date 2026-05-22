import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../hooks/useTheme';
import { loginUser, loginAdmin, generateCaptcha } from '../api/client';

export default function Login() {
    const [activeTab, setActiveTab] = useState<'user' | 'admin'>('user');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [securityCode, setSecurityCode] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    // CAPTCHA state
    const [captchaText, setCaptchaText] = useState('');
    const [captchaInput, setCaptchaInput] = useState('');
    const [captchaTypingSpeed, setCaptchaTypingSpeed] = useState(0);
    const captchaStartRef = useRef(0);
    const captchaKeyCountRef = useRef(0);

    // Typing biometrics
    const [typingSpeed, setTypingSpeed] = useState(0);
    const [formStartTime, setFormStartTime] = useState(0);
    const typingStartRef = useRef(0);
    const keyCountRef = useRef(0);

    // Generate new CAPTCHA on mount and tab change
    useEffect(() => {
        setCaptchaText(generateCaptcha());
        setCaptchaInput('');
        captchaStartRef.current = 0;
        captchaKeyCountRef.current = 0;
        setCaptchaTypingSpeed(0);
    }, [activeTab]);

    useEffect(() => {
        setFormStartTime(Date.now());
    }, []);

    function handleKeyUp() {
        if (typingStartRef.current === 0) {
            typingStartRef.current = Date.now();
        }
        keyCountRef.current += 1;

        const elapsed = (Date.now() - typingStartRef.current) / 1000 / 60;
        if (elapsed > 0) {
            const words = keyCountRef.current / 5;
            setTypingSpeed(Math.round(words / elapsed));
        }
    }

    function handleCaptchaKeyUp() {
        if (captchaStartRef.current === 0) {
            captchaStartRef.current = Date.now();
        }
        captchaKeyCountRef.current += 1;

        const elapsed = (Date.now() - captchaStartRef.current) / 1000 / 60;
        if (elapsed > 0) {
            const words = captchaKeyCountRef.current / 5;
            setCaptchaTypingSpeed(Math.round(words / elapsed));
        }
    }

    function refreshCaptcha() {
        setCaptchaText(generateCaptcha());
        setCaptchaInput('');
        captchaStartRef.current = 0;
        captchaKeyCountRef.current = 0;
        setCaptchaTypingSpeed(0);
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError('');
        setLoading(true);

        const formCompletionTime = Math.round((Date.now() - formStartTime) / 1000);

        try {
            let result;
            
            if (activeTab === 'user') {
                result = await loginUser(
                    username, 
                    password, 
                    typingSpeed, 
                    formCompletionTime, 
                    '',
                    captchaText,
                    captchaInput,
                    captchaTypingSpeed
                );
            } else {
                result = await loginAdmin(
                    username, 
                    password, 
                    securityCode, 
                    typingSpeed, 
                    formCompletionTime,
                    captchaText,
                    captchaInput,
                    captchaTypingSpeed
                );
            }

            if (result.success) {
                login({
                    user_id: result.user_id!,
                    username: result.username!,
                    user_type: result.user_type as 'user' | 'admin',
                });
                navigate(result.user_type === 'admin' ? '/admin' : '/dashboard');
            } else {
                setError(result.message || 'Login failed');
                refreshCaptcha();
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Login failed');
            refreshCaptcha();
        } finally {
            setLoading(false);
        }
    }
    const { theme, toggleTheme } = useTheme();

    return (
        <div className="login-container">
            {/* Theme toggle in top-right corner */}
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
                title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            >
                {theme === 'light' ? '🌙' : '☀️'} {theme === 'light' ? 'Dark' : 'Light'}
            </button>

            <div className="login-card">
                <div className="login-logo">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    </svg>
                    <h1>CyberSafe</h1>
                    <p className="text-muted">Cybercrime Complaint Portal</p>
                </div>

                <div className="login-tabs">
                    <button
                        className={`login-tab ${activeTab === 'user' ? 'active' : ''}`}
                        onClick={() => setActiveTab('user')}
                    >
                        User Login
                    </button>
                    <button
                        className={`login-tab ${activeTab === 'admin' ? 'active' : ''}`}
                        onClick={() => setActiveTab('admin')}
                    >
                        Admin Login
                    </button>
                </div>

                {error && <div className="alert alert-danger">{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Username</label>
                        <input
                            type="text"
                            className="form-input"
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            onKeyUp={handleKeyUp}
                            placeholder="Enter your username"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input
                            type="password"
                            className="form-input"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            onKeyUp={handleKeyUp}
                            placeholder="Enter your password"
                            required
                        />
                    </div>

                    {activeTab === 'admin' && (
                        <div className="form-group">
                            <label className="form-label">Security Code</label>
                            <input
                                type="password"
                                className="form-input"
                                value={securityCode}
                                onChange={e => setSecurityCode(e.target.value)}
                                onKeyUp={handleKeyUp}
                                placeholder="Enter security code"
                                required
                            />
                        </div>
                    )}

                    {/* CAPTCHA Section */}
                    <div className="form-group">
                        <label className="form-label">Security Verification</label>
                        <div className="captcha-container">
                            <div className="captcha-display">
                                <span className="captcha-text">{captchaText}</span>
                                <button 
                                    type="button" 
                                    className="captcha-refresh"
                                    onClick={refreshCaptcha}
                                    title="Refresh CAPTCHA"
                                >
                                    🔄
                                </button>
                            </div>
                            <input
                                type="text"
                                className="form-input"
                                value={captchaInput}
                                onChange={e => setCaptchaInput(e.target.value.toUpperCase())}
                                onKeyUp={handleCaptchaKeyUp}
                                placeholder="Enter the code above"
                                required
                                maxLength={6}
                                style={{ textTransform: 'uppercase', letterSpacing: '0.2em' }}
                            />
                        </div>
                        <div className="form-hint">Type the characters shown above</div>
                    </div>

                    <button 
                        type="submit" 
                        className="btn btn-primary btn-lg btn-block" 
                        disabled={loading}
                    >
                        {loading ? <div className="spinner" /> : 'Login'}
                    </button>
                </form>

                {activeTab === 'user' && (
                    <p className="text-center mt-3">
                        Don't have an account?{' '}
                        <a href="/register" onClick={e => { e.preventDefault(); navigate('/register'); }}>
                            Register here
                        </a>
                    </p>
                )}

                <div className="text-center mt-2 text-muted" style={{ fontSize: '0.75rem' }}>
                    🔒 Your typing patterns are analyzed for security
                </div>
            </div>
        </div>
    );
}
