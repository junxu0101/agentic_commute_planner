import React from 'react';

interface CommuteOption {
  id: string;
  option_type: string;
  commute_start?: string;
  office_arrival?: string;
  office_departure?: string;
  commute_end?: string;
  office_duration?: string;
  office_meetings?: any[];
  commute_cost?: number;
  environmental_impact?: string;
  reasoning?: string;
}

interface CommuteOptionsPanelProps {
  options: CommuteOption[];
  selectedOption: number;
  onOptionSelect: (index: number) => void;
  isLoading?: boolean;
}

const CommuteOptionsPanel: React.FC<CommuteOptionsPanelProps> = ({
  options = [],
  selectedOption,
  onOptionSelect,
  isLoading = false
}) => {
  // Format time string for display
  const formatTime = (timeString?: string): string => {
    if (!timeString) return 'N/A';
    try {
      return new Date(timeString).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return 'Invalid time';
    }
  };

  // Get option title
  const getOptionTitle = (option: CommuteOption, index: number): string => {
    if (option.option_type === 'REMOTE_DAY') {
      return `Option ${index + 1}: Full Remote Day`;
    }
    if (option.option_type === 'OFFICE_DAY') {
      return `Option ${index + 1}: Office Day`;
    }
    return `Option ${index + 1}: ${option.option_type || 'Mixed Day'}`;
  };

  // Get option icon
  const getOptionIcon = (option: CommuteOption): string => {
    if (option.option_type === 'REMOTE_DAY') return '🏠';
    if (option.option_type === 'OFFICE_DAY') return '🏢';
    return '⚡';
  };

  // Calculate total day duration
  const getDayDuration = (option: CommuteOption): string => {
    if (!option.commute_start || !option.commute_end) {
      return 'Remote day';
    }
    
    try {
      const start = new Date(option.commute_start);
      const end = new Date(option.commute_end);
      const durationMs = end.getTime() - start.getTime();
      const durationHours = Math.round(durationMs / (1000 * 60 * 60) * 10) / 10;
      return `${durationHours}h total`;
    } catch {
      return 'N/A';
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Commute Options
        </h3>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="animate-pulse">
              <div className="h-20 bg-gray-200 rounded-lg"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (options.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          AI Commute Recommendations
        </h3>
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">🗓</div>
          <p>No commute options available yet.</p>
          <p className="text-sm">Create a commute plan to see recommendations.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      <div className="p-6 border-b">
        <h3 className="text-lg font-semibold text-gray-900">
          AI Commute Recommendations
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          {options.length === 1 
            ? 'AI-optimized recommendation based on your schedule' 
            : 'Choose an option to see it overlaid on your calendar'
          }
        </p>
      </div>

      <div className="p-6 space-y-6">
        {options.map((option, index) => (
          <div
            key={option.id || index}
            className={`
              relative p-4 rounded-lg border-2 cursor-pointer transition-all duration-200
              ${selectedOption === index 
                ? 'border-blue-500 bg-blue-50 shadow-md' 
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }
            `}
            onClick={() => {
              console.log('🎯 Option clicked:', index, option);
              onOptionSelect(index);
            }}
          >
            {/* Radio button indicator */}
            <div className="flex items-start space-x-4">
              {options.length > 1 && (
                <div 
                  className="mt-2 flex-shrink-0"
                  style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '50%',
                    border: selectedOption === index ? '2px solid #2563eb' : '2px solid #9ca3af',
                    backgroundColor: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.2s ease',
                    boxShadow: selectedOption === index ? '0 0 0 1px #2563eb' : 'none'
                  }}
                >
                  {selectedOption === index && (
                    <div 
                      style={{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        backgroundColor: '#2563eb'
                      }}
                    />
                  )}
                </div>
              )}
              {options.length === 1 && (
                <div 
                  className="mt-2 flex-shrink-0"
                  style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '50%',
                    border: '2px solid #10b981',
                    backgroundColor: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.1)'
                  }}
                >
                  <div 
                    style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: '#10b981'
                    }}
                  />
                </div>
              )}

              <div className="flex-1">
                {/* Option header */}
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900 flex items-center gap-2">
                    <span>{getOptionIcon(option)}</span>
                    {getOptionTitle(option, index)}
                  </h4>
                  <span className="text-sm text-gray-500">
                    {getDayDuration(option)}
                  </span>
                </div>

                {/* Timeline */}
                {option.option_type !== 'REMOTE_DAY' && (
                  <div className="space-y-2 mb-3">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="w-16 text-gray-600">🚗 Leave:</span>
                      <span className="font-mono">{formatTime(option.commute_start)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="w-16 text-gray-600">🏢 Office:</span>
                      <span className="font-mono">
                        {formatTime(option.office_arrival)} - {formatTime(option.office_departure)}
                      </span>
                      <span className="text-gray-500">({option.office_duration})</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="w-16 text-gray-600">🏠 Home:</span>
                      <span className="font-mono">{formatTime(option.commute_end)}</span>
                    </div>
                  </div>
                )}

                {/* Meetings count */}
                {option.office_meetings && option.office_meetings.length > 0 && (
                  <div className="text-sm text-gray-600 mb-2">
                    🗓 {option.office_meetings.length} office meeting{option.office_meetings.length !== 1 ? 's' : ''}
                  </div>
                )}

                {/* AI Reasoning */}
                {option.reasoning && (
                  <div className="text-sm text-gray-700 bg-gray-100 p-3 rounded mt-2">
                    <span className="font-medium">🤖 AI Analysis:</span>
                    <p className="mt-1">{option.reasoning}</p>
                  </div>
                )}

                {/* Additional info */}
                <div className="flex items-center gap-4 text-xs text-gray-500 mt-2">
                  {option.commute_cost && (
                    <span>💰 ${option.commute_cost}</span>
                  )}
                  {option.environmental_impact && (
                    <span>🌱 {option.environmental_impact}</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer with summary */}
      <div className="px-6 py-4 bg-gray-50 rounded-b-lg">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            {options.length === 1 
              ? '🎯 Optimized recommendation - view details on your calendar above'
              : '💡 Tip: Click any option to preview it on your calendar'
            }
          </span>
          <span>{options.length} option{options.length !== 1 ? 's' : ''} available</span>
        </div>
      </div>
    </div>
  );
};

export default CommuteOptionsPanel;