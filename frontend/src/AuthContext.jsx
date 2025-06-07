import { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    console.log('AuthProvider: Starting authentication check');

    async function fetchUser() {
      try {
        console.log('AuthProvider: Fetching user data');
        const response = await fetch('/auth/user');
        console.log('AuthProvider: Response status:', response.status);
        const data = await response.json();
        console.log('AuthProvider: User data:', data);
        
        if (mounted) {
          if (data.authenticated) {
            setUser(data.user);
          } else {
            setUser(null);
          }
        }
      } catch (error) {
        console.error('AuthProvider: Failed to fetch user:', error);
        if (mounted) {
          setUser(null);
        }
      } finally {
        if (mounted) {
          console.log('AuthProvider: Setting loading to false');
          setLoading(false);
        }
      }
    }

    fetchUser();

    // Cleanup function
    return () => {
      console.log('AuthProvider: Cleanup - unmounting');
      mounted = false;
    };
  }, []);

  const login = () => {
    console.log('AuthProvider: Initiating login');
    // Use a more reliable way to handle navigation
    const loginUrl = '/auth/login';
    if (window.location.pathname !== loginUrl) {
      window.location.href = loginUrl;
    }
  };

  const logout = async () => {
    console.log('AuthProvider: Initiating logout');
    try {
      await fetch('/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });
      setUser(null);
      // Use a more reliable way to handle navigation
      const loginUrl = '/login';
      if (window.location.pathname !== loginUrl) {
        window.location.href = loginUrl;
      }
    } catch (error) {
      console.error('AuthProvider: Logout failed:', error);
    }
  };

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

