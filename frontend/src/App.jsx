import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './theme-provider';
import './App.css';

// Pages
import Login from './Login';
import Dashboard from './Dashboard';
import Market from './Market';
import Portfolio from './Portfolio';
import Transactions from './Transactions';
import Subscription from './Subscription';

// Components
import Layout from './Layout';
import { Toaster } from './components/ui/toaster';

// Context
import { AuthProvider } from './AuthContext';

function App() {
  return (
    <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
      <Router>
        <AuthProvider>
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
            <Route path="/subscription" element={
              <ProtectedRoute>
                <Layout>
                  <Subscription />
                </Layout>
              </ProtectedRoute>
            } />
          </Routes>
        </AuthProvider>
        <Toaster />
      </Router>
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