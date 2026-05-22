import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { ThemeProvider } from './hooks/useTheme';
import './index.css';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import AboutUs from './pages/AboutUs';

// User Pages
import UserLayout from './layouts/UserLayout';
import UserDashboard from './pages/user/Dashboard';
import RegisterComplaint from './pages/user/RegisterComplaint';
import MyComplaints from './pages/user/MyComplaints';
import ScamDetector from './pages/user/ScamDetector';
import MaliciousDetector from './pages/user/MaliciousDetector';
import UserProfile from './pages/user/Profile';

// Admin Pages
import AdminLayout from './layouts/AdminLayout';
import AdminDashboard from './pages/admin/Dashboard';
import AllComplaints from './pages/admin/AllComplaints';
import PendingComplaints from './pages/admin/PendingComplaints';
import ComplaintDetail from './pages/admin/ComplaintDetail';
import LoginHistory from './pages/admin/LoginHistory';
import AdminProfile from './pages/admin/Profile';

// Protected Route Component
function ProtectedRoute({ children, requireAdmin = false }: { children: React.ReactNode; requireAdmin?: boolean }) {
  const { isAuthenticated, isAdmin } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && !isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  const { isAuthenticated, isAdmin } = useAuth();

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={isAuthenticated ? <Navigate to={isAdmin ? "/admin" : "/dashboard"} replace /> : <Login />} />
      <Route path="/register" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Register />} />
      <Route path="/about" element={<AboutUs />} />

      {/* User Routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <UserLayout />
        </ProtectedRoute>
      }>
        <Route index element={<UserDashboard />} />
        <Route path="complaints" element={<MyComplaints />} />
        <Route path="complaints/new" element={<RegisterComplaint />} />
        <Route path="scam-detector" element={<ScamDetector />} />
        <Route path="malicious-detector" element={<MaliciousDetector />} />
        <Route path="profile" element={<UserProfile />} />
      </Route>

      {/* Admin Routes */}
      <Route path="/admin" element={
        <ProtectedRoute requireAdmin>
          <AdminLayout />
        </ProtectedRoute>
      }>
        <Route index element={<AdminDashboard />} />
        <Route path="complaints" element={<AllComplaints />} />
        <Route path="complaints/pending" element={<PendingComplaints />} />
        <Route path="complaints/:id" element={<ComplaintDetail />} />
        <Route path="login-history" element={<LoginHistory />} />
        <Route path="profile" element={<AdminProfile />} />
      </Route>

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
