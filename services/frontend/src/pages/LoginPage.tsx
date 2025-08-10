import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const LoginPage: React.FC = () => {
  const { login, isLoading } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
    setError(''); // Clear error when user types
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login(formData.email, formData.password);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Commute Planner
          </h1>
          <h2 className="text-xl text-gray-600 mb-4">
            AI-Powered Commute Intelligence
          </h2>
          <p className="text-sm text-gray-500">
            Sign in to start planning your optimal commutes with AI
          </p>
        </div>

        {/* Login Form */}
        <div className="card">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="form-label">
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="form-control"
                placeholder="Enter your email"
                value={formData.email}
                onChange={handleChange}
              />
            </div>

            <div>
              <label htmlFor="password" className="form-label">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="form-control"
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleChange}
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn btn-primary"
            >
              {isLoading ? (
                <>
                  <span className="spinner"></span>
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <Link to="/signup" className="font-medium text-blue-600 hover:text-blue-500">
                Create one now
              </Link>
            </p>
          </div>
        </div>

        {/* Demo Preview */}
        <div className="card bg-gradient-to-r from-green-50 to-blue-50 border border-green-200">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              🎯 What You'll Experience After Login
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-gray-700">
              <div className="flex items-start space-x-2">
                <span></span>
                <div>
                  <div className="font-semibold">Generate Demo Data</div>
                  <div>Realistic calendar events with business rules</div>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <span></span>
                <div>
                  <div className="font-semibold">Plan Commute</div>
                  <div>Pick date → AI analyzes → Get recommendations</div>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <span></span>
                <div>
                  <div className="font-semibold">AI Processing</div>
                  <div>Real-time progress with WebSocket updates</div>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <span></span>
                <div>
                  <div className="font-semibold">Smart Results</div>
                  <div>Office vs remote recommendations with reasoning</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* OAuth Future Preview */}
        <div className="card bg-gray-50 border border-gray-200">
          <div className="text-center">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              Coming Soon: Real Calendar Integration
            </h3>
            <div className="flex justify-center space-x-4">
              <button 
                disabled 
                className="btn btn-secondary opacity-50 cursor-not-allowed text-sm"
              >
                🗓 Sign in with Google
              </button>
              <button 
                disabled 
                className="btn btn-secondary opacity-50 cursor-not-allowed text-sm"
              >
                📧 Sign in with Microsoft
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              OAuth architecture ready - easy migration from JWT
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;