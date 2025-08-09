import React from 'react';
import { useAuth } from '../contexts/AuthContext';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">
                🚀 Commute Planner
              </h1>
              <span className="text-sm text-gray-500">
                Intelligent AI-powered commute planning
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-700">
                Welcome, <span className="font-semibold">{user?.name}</span>
              </div>
              <button
                onClick={logout}
                className="btn btn-secondary text-sm"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center text-gray-500 text-sm">
            <p>
              🔐 OAuth-ready architecture • 🎲 Smart demo data • 🤖 AI-powered recommendations
            </p>
            <p className="mt-2">
              Built with React, TypeScript, GraphQL, and Go microservices
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;