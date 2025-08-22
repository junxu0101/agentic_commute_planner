import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { apolloClient } from '../lib/apollo-client';

// OAuth-ready user interface - supports both JWT and OAuth providers
export interface User {
  id: string;
  email: string;
  name: string;
  authProvider?: string;           // 'local', 'google', 'microsoft', etc.
  isEmailVerified?: boolean;
  oauthScopes?: string[];          // For OAuth integrations
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
}

// Auth result from any provider (JWT or OAuth)
export interface AuthResult {
  user: User;
  accessToken: string;
  refreshToken?: string;           // For OAuth
  tokenType: string;               // 'Bearer'
  expiresIn: number;
  scopes?: string[];               // OAuth scopes
}

// OAuth-ready auth context interface
// This interface works for JWT now and will work for OAuth later
export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Local auth methods (JWT) - current implementation
  signup: (email: string, password: string, name: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  
  // Future OAuth methods - ready for Google Calendar integration
  loginWithGoogle?: () => Promise<void>;
  loginWithMicrosoft?: () => Promise<void>;
  
  // Token management (works for both JWT and OAuth)
  getAccessToken: () => string | null;
  refreshAccessToken?: () => Promise<void>;
  
  // Demo data management
  generateDemoData: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Token storage utilities - OAuth compatible
const TOKEN_KEY = 'commute_planner_token';
const REFRESH_TOKEN_KEY = 'commute_planner_refresh_token';
const USER_KEY = 'commute_planner_user';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      const userData = localStorage.getItem(USER_KEY);
      
      if (token && userData) {
        try {
          const user = JSON.parse(userData);
          setUser(user);
          
          // Apollo Client auth header is handled in apollo-client.ts
        } catch (error) {
          console.error('Failed to restore auth session:', error);
          clearAuthData();
        }
      }
      
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const clearAuthData = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
    
    // Clear Apollo Client auth header
    apolloClient.resetStore();
  };

  const saveAuthData = (authResult: AuthResult) => {
    localStorage.setItem(TOKEN_KEY, authResult.accessToken);
    localStorage.setItem(USER_KEY, JSON.stringify(authResult.user));
    
    if (authResult.refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, authResult.refreshToken);
    }
    
    setUser(authResult.user);
    
    // Apollo Client auth header is automatically handled via localStorage
  };

  const signup = async (email: string, password: string, name: string): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8080/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, name }),
      });

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || 'Signup failed');
      }

      saveAuthData(result.data);
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8080/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || 'Login failed');
      }

      saveAuthData(result.data);
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    clearAuthData();
  };

  const getAccessToken = (): string | null => {
    return localStorage.getItem(TOKEN_KEY);
  };

  const generateDemoData = async (): Promise<void> => {
    const token = getAccessToken();
    if (!token) {
      throw new Error('Authentication required');
    }

    // Get user's timezone for timezone-aware demo data generation
    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    const response = await fetch('http://localhost:8080/demo/generate', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userTimezone: userTimezone
      }),
    });

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.error || 'Failed to generate demo data');
    }

    return result.data;
  };

  // OAuth methods - stubbed for future implementation
  const loginWithGoogle = async (): Promise<void> => {
    throw new Error('Google OAuth not implemented yet - coming soon for Calendar integration!');
  };

  const loginWithMicrosoft = async (): Promise<void> => {
    throw new Error('Microsoft OAuth not implemented yet');
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    signup,
    login,
    logout,
    loginWithGoogle,
    loginWithMicrosoft,
    getAccessToken,
    generateDemoData,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};