import { Link } from 'react-router-dom';

export default function Footer() {
    return (
        <footer style={{
            background: 'var(--footer-bg, #f7fafc)',
            color: 'var(--footer-text, #4a5568)',
            padding: '40px 20px',
            textAlign: 'center',
            borderTop: '1px solid var(--border-color, #e2e8f0)'
        }}>
            <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
                <div style={{ marginBottom: '20px' }}>
                    <h3 style={{ fontSize: '1.3rem', marginBottom: '12px', color: 'var(--heading-color, #2d3748)' }}>
                        🛡️ CyberSafe Platform
                    </h3>
                    <p style={{ color: 'var(--muted-text, #718096)', maxWidth: '500px', margin: '0 auto', fontSize: '0.95rem' }}>
                        Cybercrime reporting and detection platform
                    </p>
                </div>
                <div style={{
                    margin: '24px 0',
                    padding: '16px 0',
                    borderTop: '1px solid var(--border-color, #e2e8f0)',
                    borderBottom: '1px solid var(--border-color, #e2e8f0)'
                }}>
                    <Link
                        to="/about"
                        style={{
                            color: 'var(--link-color, #3182ce)',
                            textDecoration: 'none',
                            fontWeight: 600,
                            fontSize: '1rem'
                        }}
                    >
                        📖 About Us
                    </Link>
                </div>
                <div style={{ color: 'var(--muted-text, #718096)', fontSize: '0.85rem' }}>
                    <p>© {new Date().getFullYear()} CyberSafe Platform | Version 2.0</p>
                </div>
            </div>
        </footer>
    );
}

