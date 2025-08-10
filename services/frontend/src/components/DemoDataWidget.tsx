import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface DemoDataWidgetProps {
  onDataGenerated: () => void;
  hasExistingData?: boolean;
}

interface DemoData {
  calendarEventsGenerated: number;
  events: Array<{
    id: string;
    summary: string;
    startTime: string;
    endTime: string;
    meetingType: string;
    attendanceMode: string;
    location?: string;
  }>;
  dateRange: string;
}

const DemoDataWidget: React.FC<DemoDataWidgetProps> = ({ onDataGenerated, hasExistingData = false }) => {
  const { generateDemoData } = useAuth();
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedData, setGeneratedData] = useState<DemoData | null>(null);
  const [error, setError] = useState('');

  const handleGenerateDemoData = async () => {
    setIsGenerating(true);
    setError('');
    
    try {
      const result = await generateDemoData();
      setGeneratedData(result as any);
      onDataGenerated();
      
      // Show success feedback
      setTimeout(() => {
        // Could add toast notification here
      }, 1000);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate demo data');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Generate Button */}
      <div className="text-center">
        <button
          onClick={handleGenerateDemoData}
          disabled={isGenerating}
          className={`btn ${(generatedData || hasExistingData) ? 'btn-success' : 'btn-primary'} w-full`}
        >
          {isGenerating ? (
            <>
              <span className="spinner"></span>
              Generating intelligent calendar data...
            </>
          ) : (generatedData || hasExistingData) ? (
            <>
              <span>✅</span>
              Regenerate Demo Data
            </>
          ) : (
            <>
              <span></span>
              Generate Demo Calendar Data
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* Existing Data Notice */}
      {hasExistingData && !generatedData && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-3">
            <span className="text-green-600 text-lg">✅</span>
            <h3 className="font-semibold text-green-800">Existing Demo Data Found!</h3>
          </div>
          <div className="text-sm text-green-700 space-y-1">
            <div>🗓 You already have demo calendar events</div>
            <div>🎯 Ready for AI commute analysis</div>
            <div>💡 Click "Regenerate" to create fresh demo data</div>
          </div>
        </div>
      )}

      {/* Demo Data Preview */}
      {generatedData && (
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <span className="text-green-600 text-lg">✨</span>
              <h3 className="font-semibold text-green-800">Demo Data Generated Successfully!</h3>
            </div>
            <div className="text-sm text-green-700 space-y-1">
              <div>🗓 Generated <strong>{generatedData.calendarEventsGenerated}</strong> realistic calendar events</div>
              <div>🗓️ Date range: <strong>{generatedData.dateRange}</strong></div>
              <div>🎯 Ready for AI commute analysis</div>
            </div>
          </div>

          {/* Event Preview */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-800 mb-3 flex items-center space-x-2">
              <span>📋</span>
              <span>Sample Generated Events</span>
            </h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {generatedData.events.slice(0, 8).map(event => (
                <div key={event.id} className="bg-white border rounded-lg p-3 text-sm">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900">{event.summary}</div>
                      <div className="text-gray-600 mt-1">
                        {new Date(event.startTime).toLocaleDateString()} • {' '}
                        {new Date(event.startTime).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - {' '}
                        {new Date(event.endTime).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                      </div>
                      {event.location && (
                        <div className="text-gray-500 text-xs mt-1">📍 {event.location}</div>
                      )}
                    </div>
                    <div className="ml-3">
                      <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                        event.attendanceMode === 'MUST_BE_IN_OFFICE' 
                          ? 'bg-red-100 text-red-800' 
                          : event.attendanceMode === 'CAN_BE_REMOTE'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {event.attendanceMode === 'MUST_BE_IN_OFFICE' && '🏢 Office Required'}
                        {event.attendanceMode === 'CAN_BE_REMOTE' && '🏠 Remote OK'}
                        {event.attendanceMode === 'FLEXIBLE' && '🔄 Flexible'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {generatedData.events.length > 8 && (
              <div className="text-center mt-3 text-sm text-gray-500">
                ... and {generatedData.events.length - 8} more events
              </div>
            )}
          </div>

          {/* Business Rules Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-800 mb-2 flex items-center space-x-2">
              <span>🧠</span>
              <span>Intelligent Generation Rules</span>
            </h4>
            <div className="text-sm text-blue-700 space-y-1">
              <div>• <strong>Smart Scheduling:</strong> 3-6 events on weekdays, realistic business hours</div>
              <div>• <strong>Meeting Types:</strong> Client meetings, interviews, workshops, 1:1s, standups</div>
              <div>• <strong>Attendance Modes:</strong> Some require office presence, others flexible</div>
              <div>• <strong>Realistic Locations:</strong> Conference rooms, Zoom calls, meeting spaces</div>
              <div>• <strong>Business Logic:</strong> No overlap, appropriate durations, varied attendees</div>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      {!generatedData && !hasExistingData && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-800 mb-2">🎯 What This Will Generate</h4>
          <div className="text-sm text-blue-700 space-y-2">
            <div>• <strong>14 days</strong> of realistic business calendar events</div>
            <div>• <strong>Smart variety:</strong> Client meetings, interviews, workshops, standups</div>
            <div>• <strong>Business rules:</strong> Some meetings require office presence</div>
            <div>• <strong>Realistic timing:</strong> No overlaps, appropriate durations</div>
            <div>• <strong>Ready for AI:</strong> Perfect data for commute planning analysis</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DemoDataWidget;