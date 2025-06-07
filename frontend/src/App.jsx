import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '../components/ui/theme-provider';
import '../App.css';

// Pages
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import Market from '../pages/Market';
import Portfolio from '../pages/Portfolio';
import Transactions from '../pages/Transactions';

// Components
import Layout from '../components/Layout';
import { Toaster } from '../components/ui/toaster';

// Context
import { AuthProvider } from '../context/AuthContext';

function App() {
  return (
    <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/market" element={
              <ProtectedRoute>
                <Layout>
                  <Market />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/portfolio" element={
              <ProtectedRoute>
                <Layout>
                  <Portfolio />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/transactions" element={
              <ProtectedRoute>
                <Layout>
                  <Transactions />
                </Layout>
              </ProtectedRoute>
            } />
          </Routes>
        </Router>
        <Toaster />
      </AuthProvider>
    </ThemeProvider>
  );
}

// Protected route component
function ProtectedRoute({ children }) {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check if user is authenticated
    async function checkAuth() {
      try {
        const response = await fetch('/auth/user');
        const data = await response.json();
        setIsAuthenticated(data.authenticated);
      } catch (error) {
        console.error('Authentication check failed:', error);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    }

    checkAuth();
  }, []);

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
}

export default App; 