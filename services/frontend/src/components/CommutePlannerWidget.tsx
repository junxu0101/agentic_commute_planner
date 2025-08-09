import React, { useState } from 'react';
import { gql, useMutation, useSubscription } from '@apollo/client';
import { useAuth } from '../contexts/AuthContext';

// GraphQL mutations and subscriptions
const CREATE_COMMUTE_JOB = gql`
  mutation CreateCommuteJob($input: CreateCommuteJobInput!) {
    createCommuteJob(input: $input) {
      id
      userId
      status
      progress
      targetDate
      createdAt
    }
  }
`;

const JOB_PROGRESS_SUBSCRIPTION = gql`
  subscription JobProgress {
    jobProgress {
      jobId
      status
      progress
      currentStep
      result
      errorMessage
      timestamp
    }
  }
`;

interface CommutePlannerWidgetProps {
  enabled: boolean;
  onPlanningStart: () => void;
}

interface JobProgress {
  jobId: string;
  status: string;
  progress: number;
  currentStep?: string;
  result?: any;
  errorMessage?: string;
  timestamp: string;
}

const CommutePlannerWidget: React.FC<CommutePlannerWidgetProps> = ({ 
  enabled, 
  onPlanningStart 
}) => {
  const { user } = useAuth();
  const [selectedDate, setSelectedDate] = useState(
    new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0] // Tomorrow
  );

  // Helper function to format date without timezone issues
  const formatDateSafe = (dateString: string) => {
    const [year, month, day] = dateString.split('-').map(Number);
    const date = new Date(year, month - 1, day); // month is 0-indexed
    return date.toLocaleDateString();
  };

  // Helper function to convert Date object to YYYY-MM-DD string in local timezone
  const dateToLocalString = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobResults, setJobResults] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const [creatingJob, setCreatingJob] = useState(false);

  // GraphQL hooks
  const [createCommuteJob, { loading: creatingJobMutation }] = useMutation(CREATE_COMMUTE_JOB);
  
  // Subscribe to all job progress updates (global subscription)
  const { data: progressData, error: subscriptionError } = useSubscription<{ jobProgress: JobProgress }>(
    JOB_PROGRESS_SUBSCRIPTION,
    {
      skip: !activeJobId, // Only subscribe when we have an active job
      onData: ({ data }: any) => {
        console.log('🔄 Received WebSocket data:', data);
        
        if (data?.data?.jobProgress) {
          const progress = data.data.jobProgress;
          console.log('📊 Progress update:', progress);
          
          // Only process updates for our active job
          if (progress.jobId !== activeJobId) {
            console.log(`⏭️  Ignoring progress for different job: ${progress.jobId} (active: ${activeJobId})`);
            return;
          }
          
          // Handle job completion
          if (progress.status === 'COMPLETED') {
            console.log('✅ Job completed!', progress);
            
            if (progress.result) {
              try {
                // Parse the JSON result string
                const result = JSON.parse(progress.result);
                console.log('📋 Parsed job result:', result);
                setJobResults(result);
              } catch (e) {
                console.error('Failed to parse job result JSON:', e);
                // Fallback to generic message
                setJobResults({ 
                  status: 'completed', 
                  message: 'Commute analysis completed successfully!',
                  jobId: progress.jobId,
                  timestamp: progress.timestamp
                });
              }
            } else {
              // No result provided, show generic completion
              setJobResults({ 
                status: 'completed', 
                message: 'Commute analysis completed successfully!',
                jobId: progress.jobId,
                timestamp: progress.timestamp
              });
            }
            
            setActiveJobId(null); // Stop subscription
          }
          
          // Handle job failure
          if (progress.status === 'FAILED') {
            console.log('❌ Job failed:', progress.errorMessage);
            setActiveJobId(null); // Stop subscription
          }
        }
      },
      onError: (error) => {
        console.error('🚨 Subscription error:', error);
      }
    }
  );

  // Log subscription errors
  if (subscriptionError) {
    console.error('❌ GraphQL subscription error:', subscriptionError);
  }

  // Log what Apollo Client is receiving
  console.log('🔍 Apollo subscription state:', {
    activeJobId,
    progressData,
    subscriptionError,
    hasData: !!progressData,
  });

  // Filter progress updates to only show our active job
  const currentProgress = (progressData as any)?.jobProgress?.jobId === activeJobId 
    ? (progressData as any)?.jobProgress 
    : null;

  const handlePlanCommute = async () => {
    if (!enabled || creatingJob || !user?.id) return;
    
    setError('');
    setCreatingJob(true);
    
    try {
      console.log('🚀 Creating commute planning job...');
      console.log('User ID:', user.id);
      console.log('Target Date:', selectedDate);
      
      onPlanningStart();
      
      // Use Apollo client to create job through the gateway (enables WebSocket subscriptions)
      const result = await createCommuteJob({
        variables: {
          input: {
            userId: user.id,
            targetDate: selectedDate,
            inputData: 'Commute planning request from demo data'
          }
        }
      });
      
      console.log('Gateway response:', result);
      
      if (result.data?.createCommuteJob?.id) {
        console.log('✅ Job created successfully:', result.data.createCommuteJob.id);
        setActiveJobId(result.data.createCommuteJob.id);
        setJobResults(null); // Clear previous results
      } else if (result.errors && result.errors.length > 0) {
        setError(`Gateway error: ${result.errors[0].message}`);
      } else {
        setError('Failed to create commute planning job - no job ID returned');
      }
    } catch (error) {
      console.error('❌ Failed to create commute job:', error);
      setError(error instanceof Error ? error.message : 'Failed to create commute planning job');
    } finally {
      setCreatingJob(false);
    }
  };

  // Get the next few weekdays for date suggestions
  const getUpcomingWeekdays = () => {
    const dates = [];
    const today = new Date();
    
    for (let i = 1; i <= 7; i++) {
      const date = new Date(today.getTime() + i * 24 * 60 * 60 * 1000);
      if (date.getDay() !== 0 && date.getDay() !== 6) { // Skip weekends
        dates.push(date);
      }
    }
    
    return dates.slice(0, 5); // Return next 5 weekdays
  };

  const upcomingDates = getUpcomingWeekdays();

  return (
    <div className="space-y-6">
      {/* Date Selection */}
      <div className="space-y-4">
        <div>
          <label htmlFor="targetDate" className="form-label">
            📅 Select Target Date for Commute Planning
          </label>
          <input
            id="targetDate"
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            min={new Date().toISOString().split('T')[0]}
            className="form-control"
            disabled={!enabled || !!activeJobId}
          />
        </div>

        {/* Quick Date Suggestions */}
        <div>
          <div className="text-sm text-gray-600 mb-2">Quick select upcoming weekdays:</div>
          <div className="flex flex-wrap gap-2">
            {upcomingDates.map(date => (
              <button
                key={date.toISOString()}
                onClick={() => setSelectedDate(dateToLocalString(date))}
                disabled={!enabled || !!activeJobId}
                className={`px-3 py-2 text-xs rounded-lg border transition-colors ${
                  selectedDate === dateToLocalString(date)
                    ? 'bg-blue-100 border-blue-300 text-blue-800'
                    : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                } ${(!enabled || !!activeJobId) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <div className="font-medium">
                  {date.toLocaleDateString([], { month: 'short', day: 'numeric' })}
                </div>
                <div className="text-xs text-gray-500">
                  {date.toLocaleDateString([], { weekday: 'short' })}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          <div className="flex items-center space-x-2">
            <span>❌</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Plan Commute Button */}
      <div className="text-center">
        {!enabled ? (
          <div className="space-y-3">
            <button disabled className="btn btn-secondary opacity-50 cursor-not-allowed w-full">
              <span>🤖</span>
              Plan My Commute (Generate demo data first)
            </button>
            <p className="text-sm text-gray-500">
              ⚠️ Please generate demo calendar data first to enable commute planning
            </p>
          </div>
        ) : (
          <button
            onClick={handlePlanCommute}
            disabled={creatingJob || !!activeJobId}
            className={`w-full btn ${activeJobId ? 'btn-secondary' : 'btn-primary'}`}
          >
            {creatingJob ? (
              <>
                <span className="spinner"></span>
                Creating planning job...
              </>
            ) : activeJobId ? (
              <>
                <span>⏳</span>
                AI is analyzing your calendar...
              </>
            ) : (
              <>
                <span>🚀</span>
                Plan My Commute for {formatDateSafe(selectedDate)}
              </>
            )}
          </button>
        )}
      </div>

      {/* Real-time Progress */}
      {currentProgress && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-800 mb-3 flex items-center space-x-2">
            <span>⚡</span>
            <span>Real-time AI Processing</span>
          </h4>
          
          <div className="space-y-3">
            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                style={{ width: `${currentProgress.progress * 100}%` }}
              ></div>
            </div>
            
            {/* Current Step */}
            <div className="flex items-center justify-between text-sm">
              <span className="text-blue-700">
                <span className="font-medium">Current Step:</span> {currentProgress.currentStep || 'Processing...'}
              </span>
              <span className="text-blue-600 font-medium">
                {Math.round(currentProgress.progress * 100)}%
              </span>
            </div>

            {/* Status */}
            <div className="text-xs text-blue-600">
              Status: {currentProgress.status} • Last update: {new Date(currentProgress.timestamp).toLocaleTimeString()}
            </div>

            {/* Error handling */}
            {currentProgress.errorMessage && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                Error: {currentProgress.errorMessage}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Results Display */}
      {jobResults && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="font-semibold text-green-800 mb-3 flex items-center space-x-2">
            <span>🎯</span>
            <span>AI Commute Recommendations</span>
          </h4>
          
          <div className="space-y-3">
            <div className="text-sm text-green-700">
              ✅ AI analysis completed for {formatDateSafe(selectedDate)}
            </div>
            
            {/* Display recommendations here */}
            <div className="bg-white border rounded-lg p-4">
              <div className="text-sm text-gray-700">
                <strong>Analysis Results:</strong>
                <pre className="mt-2 text-xs overflow-auto">
                  {JSON.stringify(jobResults, null, 2)}
                </pre>
              </div>
            </div>
            
            <button 
              onClick={() => setJobResults(null)}
              className="btn btn-secondary text-sm"
            >
              Plan Another Day
            </button>
          </div>
        </div>
      )}

      {/* Instructions */}
      {enabled && !activeJobId && !jobResults && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="font-semibold text-yellow-800 mb-2">🎯 How Commute Planning Works</h4>
          <div className="text-sm text-yellow-700 space-y-2">
            <div>1. <strong>Select Date:</strong> Choose when you want to plan your commute</div>
            <div>2. <strong>AI Analysis:</strong> Multi-agent system analyzes your calendar events</div>
            <div>3. <strong>Smart Decisions:</strong> Determines office vs remote based on meetings</div>
            <div>4. <strong>Recommendations:</strong> Provides optimal commute timing and reasoning</div>
            <div>5. <strong>Real-time:</strong> Watch progress updates via WebSocket</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CommutePlannerWidget;