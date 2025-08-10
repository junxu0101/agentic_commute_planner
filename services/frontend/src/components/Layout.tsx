import React from 'react';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main content */}
      <main>
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center text-gray-500 text-sm">
            <p>
              OAuth-ready architecture • Smart demo data • AI-powered recommendations
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