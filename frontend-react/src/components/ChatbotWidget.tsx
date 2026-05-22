import { useState, useRef, useEffect } from 'react';
import { queryChatbot } from '../api/client';

interface Message {
    id: number;
    text: string;
    isUser: boolean;
}

export default function ChatbotWidget() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 0,
            text: "Hello! I'm your CyberSafe assistant. Ask me anything about cybercrime laws, how to file complaints, or online safety tips.",
            isUser: false,
        },
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    
    // Draggable state - using top/left positioning for consistent drag behavior
    const [position, setPosition] = useState({ x: 24, y: 0 }); // x from left, y from bottom initially
    const [isDragging, setIsDragging] = useState(false);
    const [useTopPositioning, setUseTopPositioning] = useState(false);
    const [topPosition, setTopPosition] = useState(0);
    const dragOffset = useRef({ x: 0, y: 0 });
    const windowRef = useRef<HTMLDivElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Handle dragging - Fixed: Now properly handles upward drag
    useEffect(() => {
        if (!isDragging) return;
        
        function handleMouseMove(e: MouseEvent) {
            if (!windowRef.current) return;
            
            const windowHeight = window.innerHeight;
            const windowWidth = window.innerWidth;
            const chatHeight = 500; // chatbot window height
            const chatWidth = 380; // chatbot window width
            
            // Calculate new position from top-left
            let newX = e.clientX - dragOffset.current.x;
            let newY = e.clientY - dragOffset.current.y;
            
            // Constrain to viewport
            newX = Math.max(0, Math.min(windowWidth - chatWidth, newX));
            newY = Math.max(0, Math.min(windowHeight - chatHeight, newY));
            
            setPosition({ x: newX, y: 0 }); // y is now handled differently
            setTopPosition(newY);
            setUseTopPositioning(true);
        }
        
        function handleMouseUp() {
            setIsDragging(false);
        }
        
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        
        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging]);

    function handleDragStart(e: React.MouseEvent) {
        if (!windowRef.current) return;
        
        const rect = windowRef.current.getBoundingClientRect();
        setIsDragging(true);
        dragOffset.current = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
        
        // Switch to top positioning on first drag
        if (!useTopPositioning) {
            setTopPosition(rect.top);
            setPosition({ x: rect.left, y: 0 });
            setUseTopPositioning(true);
        }
        
        e.preventDefault();
    }

    function resetPosition() {
        setUseTopPositioning(false);
        setPosition({ x: 24, y: 0 });
        setTopPosition(0);
    }

    async function sendMessage() {
        if (!input.trim() || loading) return;

        const userMessage = input.trim();
        setInput('');

        // Add user message
        const newUserMsg: Message = {
            id: Date.now(),
            text: userMessage,
            isUser: true,
        };
        setMessages(prev => [...prev, newUserMsg]);
        setLoading(true);

        try {
            const result = await queryChatbot(userMessage);
            const botMsg: Message = {
                id: Date.now() + 1,
                text: result.answer,
                isUser: false,
            };
            setMessages(prev => [...prev, botMsg]);
        } catch {
            const errorMsg: Message = {
                id: Date.now() + 1,
                text: 'Sorry, I encountered an error. Please try again.',
                isUser: false,
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setLoading(false);
        }
    }

    function handleKeyPress(e: React.KeyboardEvent<HTMLInputElement>) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    }

    // Dynamic positioning styles
    const windowStyle: React.CSSProperties = isOpen 
        ? useTopPositioning 
            ? {
                position: 'fixed',
                left: `${position.x}px`,
                top: `${topPosition}px`,
                bottom: 'auto',
            }
            : {
                position: 'fixed',
                left: '24px',
                bottom: '99px',
            }
        : {};

    return (
        <div className="chatbot-widget">
            <div 
                ref={windowRef}
                className={`chatbot-window ${isOpen ? 'open' : ''}`}
                style={windowStyle}
            >
                <div 
                    className={`chatbot-header ${isDragging ? 'dragging' : ''}`}
                    onMouseDown={handleDragStart}
                    style={{ cursor: 'move', userSelect: 'none' }}
                >
                    <span className="chatbot-header-icon">🤖</span>
                    <span className="chatbot-header-title">CyberSafe Assistant</span>
                    <button 
                        className="chatbot-reset-btn"
                        onClick={(e) => { e.stopPropagation(); resetPosition(); }}
                        title="Reset position"
                        style={{ 
                            background: 'transparent', 
                            border: 'none', 
                            color: 'rgba(255,255,255,0.7)',
                            cursor: 'pointer',
                            marginRight: '4px',
                            fontSize: '0.9rem'
                        }}
                    >
                        📍
                    </button>
                    <button 
                        className="chatbot-close-btn"
                        onClick={(e) => { e.stopPropagation(); setIsOpen(false); }}
                        aria-label="Close chat"
                    >
                        ✕
                    </button>
                </div>
                <div className="chatbot-messages">
                    {messages.map(msg => (
                        <div key={msg.id} className={`chatbot-message ${msg.isUser ? 'user' : 'bot'}`}>
                            {msg.text}
                        </div>
                    ))}
                    {loading && (
                        <div className="chatbot-message bot">
                            <div className="chatbot-typing">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
                <div className="chatbot-input-wrapper">
                    <input
                        type="text"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Type your question..."
                        disabled={loading}
                    />
                    <button 
                        className="btn btn-primary btn-sm" 
                        onClick={sendMessage} 
                        disabled={loading || !input.trim()}
                        aria-label="Send message"
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="22" y1="2" x2="11" y2="13"></line>
                            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                        </svg>
                    </button>
                </div>
            </div>
            <button 
                className="chatbot-toggle" 
                onClick={() => setIsOpen(!isOpen)}
                aria-label={isOpen ? "Close chat" : "Open chat"}
                aria-expanded={isOpen}
            >
                {isOpen ? '✕' : '💬'}
            </button>
        </div>
    );
}
