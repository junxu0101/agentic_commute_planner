import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import CommutePlannerWidget from '../components/CommutePlannerWidget';
import DemoDataWidget from '../components/DemoDataWidget';

const DashboardPage: React.FC = () => {
  const { user, getAccessToken, isLoading: authLoading } = useAuth();
  const [demoDataGenerated, setDemoDataGenerated] = useState(false);
  const [isCheckingData, setIsCheckingData] = useState(true);

  // Check if user has existing calendar events
  useEffect(() => {
    const checkExistingData = async () => {
      console.log('=== DashboardPage Debug ===');
      console.log('Auth loading:', authLoading);
      console.log('User object:', user);
      console.log('User ID:', user?.id);
      console.log('User email:', user?.email);
      
      // Wait for auth loading to complete
      if (authLoading) {
        console.log('Still loading auth, waiting...');
        return;
      }
      
      if (!user?.id) {
        console.log('No user ID after auth loading complete, stopping check');
        setIsCheckingData(false);
        return;
      }

      try {
        const token = getAccessToken();
        console.log('Retrieved token:', token ? `Token exists (${token.substring(0, 50)}...)` : 'No token');
        
        if (!token) {
          console.error('No authentication token available');
          setIsCheckingData(false);
          return;
        }

        console.log('Making API call to /demo/check...');
        const response = await fetch('http://localhost:8080/demo/check', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        console.log('API response status:', response.status);
        console.log('API response headers:', Object.fromEntries(response.headers));
        
        if (response.ok) {
          const data = await response.json();
          console.log('API response data:', data);
          
          if (data.success && data.hasData) {
            console.log('✅ Found existing demo data! Setting demoDataGenerated to true');
            setDemoDataGenerated(true);
          } else {
            console.log('❌ No demo data found');
            setDemoDataGenerated(false);
          }
        } else {
          console.error('❌ API call failed with status:', response.status);
          const errorText = await response.text();
          console.error('Error response:', errorText);
        }
      } catch (error) {
        console.error('❌ Exception in checkExistingData:', error);
      } finally {
        console.log('=== End Debug - Setting isCheckingData to false ===');
        setIsCheckingData(false);
      }
    };

    console.log('🚀 DashboardPage useEffect triggered');
    checkExistingData();
  }, [user, getAccessToken, authLoading]);

  if (isCheckingData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="spinner mb-4"></div>
          <p className="text-gray-600">Checking your calendar data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome back, {user?.name}! 🚀
        </h1>
        <p className="text-xl text-gray-600 mb-2">
          Ready to plan your optimal commute with AI?
        </p>
        <p className="text-sm text-gray-500">
          {user?.authProvider === 'local' ? (
            <>OAuth-ready architecture • Currently using JWT authentication</>
          ) : (
            <>Connected via {user?.authProvider} • OAuth integration active</>
          )}
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card text-center bg-gradient-to-br from-blue-50 to-blue-100">
          <div className="text-3xl mb-2">🎲</div>
          <div className="text-lg font-semibold text-gray-900">Demo Data</div>
          <div className="text-sm text-gray-600">
            Generate realistic calendar events for testing
          </div>
        </div>
        
        <div className="card text-center bg-gradient-to-br from-green-50 to-green-100">
          <div className="text-3xl mb-2">🤖</div>
          <div className="text-lg font-semibold text-gray-900">AI Planning</div>
          <div className="text-sm text-gray-600">
            Multi-agent workflow for commute optimization
          </div>
        </div>
        
        <div className="card text-center bg-gradient-to-br from-purple-50 to-purple-100">
          <div className="text-3xl mb-2">📊</div>
          <div className="text-lg font-semibold text-gray-900">Smart Results</div>
          <div className="text-sm text-gray-600">
            Office vs remote recommendations with reasoning
          </div>
        </div>
      </div>

      {/* Main Workflow */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Step 1: Generate Demo Data */}
        <div className="space-y-6">
          <div className="card">
            <div className="card-header">
              <h2 className="flex items-center space-x-2">
                <span>🎲</span>
                <span>Step 1: Generate Demo Data</span>
              </h2>
              <p className="text-sm text-gray-600 mt-2">
                Create realistic calendar events with intelligent business rules
              </p>
            </div>
            
            <DemoDataWidget 
              onDataGenerated={() => setDemoDataGenerated(true)}
              hasExistingData={demoDataGenerated}
            />
          </div>

          {/* Future OAuth Integration Preview */}
          <div className="card bg-gray-50 border border-gray-200">
            <div className="card-header">
              <h2 className="flex items-center space-x-2 text-gray-700">
                <span>🚀</span>
                <span>Future: Real Calendar Integration</span>
              </h2>
            </div>
            
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Coming soon: Connect your real Google Calendar for automatic event sync
              </p>
              
              <div className="flex space-x-4">
                <button 
                  disabled 
                  className="btn btn-secondary opacity-50 cursor-not-allowed flex items-center space-x-2"
                >
                  <span>📅</span>
                  <span>Connect Google Calendar</span>
                </button>
                <button 
                  disabled 
                  className="btn btn-secondary opacity-50 cursor-not-allowed flex items-center space-x-2"
                >
                  <span>📧</span>
                  <span>Connect Outlook</span>
                </button>
              </div>
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="text-sm text-blue-800">
                  <div className="font-semibold">✨ OAuth Migration Ready</div>
                  <div className="mt-1">
                    The entire auth architecture is designed for easy OAuth migration:
                  </div>
                  <ul className="list-disc list-inside mt-2 space-y-1 text-xs">
                    <li>AuthProvider interface supports multiple providers</li>
                    <li>Database schema ready with oauth_tokens & scopes</li>
                    <li>JWT → Google OAuth migration in ~1 day</li>
                    <li>Real calendar permissions for commute planning</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Step 2: Plan Commute */}
        <div className="space-y-6">
          <div className="card">
            <div className="card-header">
              <h2 className="flex items-center space-x-2">
                <span>🤖</span>
                <span>Step 2: Plan Your Commute</span>
              </h2>
              <p className="text-sm text-gray-600 mt-2">
                Select a date and let AI analyze your calendar for optimal commute recommendations
              </p>
            </div>
            
            <CommutePlannerWidget 
              enabled={demoDataGenerated}
              onPlanningStart={() => {/* Handle planning start */}}
            />
          </div>

          {/* Architecture Info */}
          <div className="card bg-gradient-to-r from-gray-50 to-blue-50 border border-gray-200">
            <div className="card-header">
              <h2 className="flex items-center space-x-2 text-gray-800">
                <span>⚙️</span>
                <span>System Architecture</span>
              </h2>
            </div>
            
            <div className="space-y-3 text-sm text-gray-700">
              <div className="flex items-start space-x-2">
                <span className="text-blue-600">🔐</span>
                <div>
                  <div className="font-semibold">OAuth-Ready Authentication</div>
                  <div>JWT now, Google OAuth later for calendar access</div>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-green-600">🏗️</span>
                <div>
                  <div className="font-semibold">Microservices Architecture</div>
                  <div>Gateway → Backend → AI Service with GraphQL federation</div>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-purple-600">⚡</span>
                <div>
                  <div className="font-semibold">Real-time Updates</div>
                  <div>WebSocket subscriptions for live job progress</div>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-orange-600">🤖</span>
                <div>
                  <div className="font-semibold">Multi-Agent AI Workflow</div>
                  <div>Schedule analysis → Meeting classification → Commute optimization</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;