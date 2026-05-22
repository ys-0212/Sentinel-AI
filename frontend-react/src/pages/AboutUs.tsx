import { Link } from 'react-router-dom';

export default function AboutUs() {
    return (
        <div style={{ background: '#ffffff', minHeight: '100vh' }}>
            {/* Navigation Bar */}
            <nav style={{
                background: '#1a365d',
                padding: '16px 40px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
            }}>
                <h2 style={{ color: 'white', margin: 0, fontSize: '1.4rem' }}>🛡️ CyberSafe</h2>
                <Link
                    to="/dashboard"
                    style={{
                        background: 'white',
                        color: '#1a365d',
                        padding: '10px 24px',
                        borderRadius: '6px',
                        textDecoration: 'none',
                        fontWeight: 600,
                        fontSize: '0.95rem'
                    }}
                >
                    ← Back to Dashboard
                </Link>
            </nav>

            <div style={{ maxWidth: '900px', margin: '0 auto', padding: '60px 20px' }}>
                {/* Header */}
                <header style={{ textAlign: 'center', marginBottom: '60px' }}>
                    <h1 style={{ fontSize: '2.2rem', color: '#1a365d', marginBottom: '16px', fontWeight: 600 }}>
                        About CyberSafe Platform
                    </h1>
                    <p style={{ fontSize: '1.1rem', color: '#4a5568', lineHeight: 1.7, maxWidth: '700px', margin: '0 auto' }}>
                        A comprehensive cybercrime reporting and detection platform developed to help citizens
                        report incidents efficiently and assist law enforcement in crime prevention.
                    </p>
                </header>

                {/* Mission Section */}
                <section style={{ marginBottom: '50px' }}>
                    <h2 style={{ fontSize: '1.5rem', color: '#2d3748', marginBottom: '16px', borderBottom: '2px solid #e2e8f0', paddingBottom: '10px' }}>
                        Our Mission
                    </h2>
                    <p style={{ color: '#4a5568', lineHeight: 1.8, fontSize: '1rem' }}>
                        CyberSafe aims to bridge the gap between citizens and law enforcement by providing
                        an accessible platform for reporting cybercrimes. We use modern technology including
                        natural language processing and machine learning to help analyze, categorize, and
                        prioritize complaints for faster resolution.
                    </p>
                </section>

                {/* Features Section */}
                <section style={{ marginBottom: '50px' }}>
                    <h2 style={{ fontSize: '1.5rem', color: '#2d3748', marginBottom: '24px', borderBottom: '2px solid #e2e8f0', paddingBottom: '10px' }}>
                        Platform Features
                    </h2>

                    <div style={{ display: 'grid', gap: '20px' }}>
                        {features.map((feature, idx) => (
                            <div key={idx} style={{
                                background: '#f7fafc',
                                padding: '20px 24px',
                                borderRadius: '8px',
                                borderLeft: '4px solid #3182ce'
                            }}>
                                <h3 style={{ color: '#2d3748', marginBottom: '8px', fontSize: '1.1rem' }}>
                                    {feature.title}
                                </h3>
                                <p style={{ color: '#718096', margin: 0, lineHeight: 1.6 }}>
                                    {feature.description}
                                </p>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Technology Section */}
                <section style={{ marginBottom: '50px' }}>
                    <h2 style={{ fontSize: '1.5rem', color: '#2d3748', marginBottom: '16px', borderBottom: '2px solid #e2e8f0', paddingBottom: '10px' }}>
                        Technology Stack
                    </h2>
                    <p style={{ color: '#4a5568', lineHeight: 1.8, marginBottom: '16px' }}>
                        The platform is built using industry-standard technologies:
                    </p>
                    <ul style={{ color: '#4a5568', lineHeight: 2, paddingLeft: '24px' }}>
                        <li><strong>Backend:</strong> Python FastAPI with SQLite database</li>
                        <li><strong>Frontend:</strong> React with TypeScript</li>
                        <li><strong>AI/ML:</strong> Groq LLM, Sentence Transformers, FAISS vector search</li>
                        <li><strong>Analysis:</strong> NLP for text analysis, speech recognition for audio</li>
                        <li><strong>Security:</strong> Behavioral analysis, VPN detection, anomaly detection</li>
                    </ul>
                </section>

                {/* Contact Section */}
                <section style={{ marginBottom: '50px' }}>
                    <h2 style={{ fontSize: '1.5rem', color: '#2d3748', marginBottom: '16px', borderBottom: '2px solid #e2e8f0', paddingBottom: '10px' }}>
                        Contact Information
                    </h2>
                    <p style={{ color: '#4a5568', lineHeight: 1.8 }}>
                        For support or inquiries, please reach out through the dashboard's chatbot assistant
                        or contact your local cybercrime cell.
                    </p>
                </section>

                {/* Back Button */}
                <div style={{ textAlign: 'center', marginTop: '40px' }}>
                    <Link
                        to="/dashboard"
                        style={{
                            display: 'inline-block',
                            background: '#1a365d',
                            color: 'white',
                            padding: '14px 32px',
                            borderRadius: '6px',
                            textDecoration: 'none',
                            fontWeight: 600
                        }}
                    >
                        ← Return to Dashboard
                    </Link>
                </div>
            </div>

            {/* Simple Footer */}
            <footer style={{
                background: '#1a365d',
                color: 'white',
                padding: '24px',
                textAlign: 'center',
                marginTop: '40px'
            }}>
                <p style={{ margin: 0, fontSize: '0.9rem' }}>
                    © {new Date().getFullYear()} CyberSafe Platform | Version 2.0
                </p>
            </footer>
        </div>
    );
}

const features = [
    {
        title: 'Complaint Management',
        description: 'Submit and track cybercrime complaints with automated status updates. The system generates summaries, assigns severity scores, and categorizes crime types automatically.'
    },
    {
        title: 'Malicious Text Detection',
        description: 'Analyze suspicious emails, messages, or chats to identify phishing attempts, scams, and social engineering tactics.'
    },
    {
        title: 'Call Scam Detection',
        description: 'Upload audio recordings or transcripts of suspicious calls to detect common scam patterns and fraudulent requests.'
    },
    {
        title: 'Similar Complaint Detection',
        description: 'Automatically identifies similar complaints to help detect organized crime patterns and serial offenders.'
    },
    {
        title: 'Behavioral Analysis',
        description: 'Monitors login patterns including typing speed, IP address, and device information to detect suspicious access attempts.'
    },
    {
        title: 'Chatbot Assistant',
        description: 'Get answers to questions about cybercrime laws, complaint procedures, and online safety tips through our AI-powered assistant.'
    }
];

