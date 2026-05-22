import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

interface UserSession {
    user_id: string;
    username: string;
    user_type: 'user' | 'admin';
}

interface AuthContextType {
    user: UserSession | null;
    login: (session: UserSession) => void;
    logout: () => void;
    isAuthenticated: boolean;
    isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<UserSession | null>(null);

    useEffect(() => {
        // Load session from sessionStorage on mount
        const stored = sessionStorage.getItem('userSession');
        if (stored) {
            try {
                setUser(JSON.parse(stored));
            } catch {
                sessionStorage.removeItem('userSession');
            }
        }
    }, []);

    const login = (session: UserSession) => {
        setUser(session);
        sessionStorage.setItem('userSession', JSON.stringify(session));
    };

    const logout = () => {
        setUser(null);
        sessionStorage.removeItem('userSession');
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                login,
                logout,
                isAuthenticated: !!user,
                isAdmin: user?.user_type === 'admin',
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
