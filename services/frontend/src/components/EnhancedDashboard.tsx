import React, { useState, useEffect } from 'react';
import { gql, useQuery } from '@apollo/client';
import { useAuth } from '../contexts/AuthContext';
import CalendarVisualization from './CalendarVisualization';
import CommuteOptionsPanel from './CommuteOptionsPanel';
import EventDetailsModal from './EventDetailsModal';
import CommutePlannerWidget from './CommutePlannerWidget';
import DemoDataWidget from './DemoDataWidget';

// GraphQL query for calendar events (for display - gets all user events)
const GET_CALENDAR_EVENTS = gql`
  query GetCalendarEvents($userId: ID!) {
    calendarEvents(userId: $userId) {
      id
      summary
      description
      startTime
      endTime
      location
      attendees
      meetingType
      attendanceMode
      isAllDay
      isRecurring
    }
  }
`;

interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  type: 'meeting' | 'commute' | 'office-time';
  meetingType?: string;
  attendanceMode?: string;
  location?: string;
  description?: string;
  attendees?: string[];
}

const EnhancedDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [selectedCommuteOption, setSelectedCommuteOption] = useState<number>(0);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [isEventModalOpen, setIsEventModalOpen] = useState(false);
  const [commuteRecommendations, setCommuteRecommendations] = useState<any[]>([]);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false);
  const [targetDate, setTargetDate] = useState(
    new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().split('T')[0] // Tomorrow
  );

  // Query calendar events for display (all user events)
  const { data: calendarData, loading: calendarLoading, refetch: refetchCalendar } = useQuery(
    GET_CALENDAR_EVENTS,
    {
      variables: { userId: user?.id },
      skip: !user?.id,
      errorPolicy: 'all'
    }
  );

  // Handle commute plan results
  const handlePlanningComplete = (results: any) => {
    console.log('Planning complete with results:', results);
    console.log('Results structure:', Object.keys(results || {}));
    
    // Update target date if provided in results
    if (results.target_date) {
      console.log(`🗓 Updating target date to: ${results.target_date}`);
      setTargetDate(results.target_date);
    }
    
    // Try different possible data structures
    let recommendations = [];
    
    if (results.recommendations && Array.isArray(results.recommendations)) {
      recommendations = results.recommendations;
      console.log('✅ Found recommendations array:', recommendations.length, 'options');
    } else if (results.commute_options && Array.isArray(results.commute_options)) {
      recommendations = results.commute_options;
      console.log('✅ Found commute_options array:', recommendations.length, 'options');
    } else if (results.options && Array.isArray(results.options)) {
      recommendations = results.options;
      console.log('✅ Found options array:', recommendations.length, 'options');
    } else if (results.result && results.result.recommendations) {
      recommendations = results.result.recommendations;
      console.log('✅ Found nested recommendations:', recommendations.length, 'options');
    } else {
      console.log('❌ No recommendations found in results structure');
      console.log('Available keys:', Object.keys(results || {}));
      // Try to extract any array from the results
      for (const [key, value] of Object.entries(results || {})) {
        if (Array.isArray(value) && value.length > 0) {
          console.log(`🔍 Found potential recommendations in key '${key}':`, value);
          recommendations = value;
          break;
        }
      }
    }
    
    if (recommendations.length > 0) {
      // Transform AI service data structure to match frontend expectations
      const transformedRecommendations = recommendations.map((rec: any, index: number) => {
        console.log(`🔄 Transforming recommendation ${index + 1}:`, rec);
        
        // Extract data from nested structures
        const optionData = rec.option_data || rec;
        const detailedSchedule = rec.detailed_schedule || {};
        
        return {
          id: rec.id || `option-${index}`,
          option_type: rec.option_type || optionData.option_type || 'UNKNOWN',
          
          // Commute timing fields - check multiple possible locations
          commute_start: optionData.commute_start || rec.commute_start || null,
          office_arrival: optionData.office_arrival || rec.office_arrival || null,
          office_departure: optionData.office_departure || rec.office_departure || null,
          commute_end: optionData.commute_end || rec.commute_end || null,
          office_duration: optionData.office_duration || rec.office_duration || '0 hours',
          
          // Meeting and reasoning data
          office_meetings: optionData.office_meetings || rec.office_meetings || [],
          remote_meetings: optionData.remote_meetings || rec.remote_meetings || [],
          reasoning: rec.ai_summary || rec.reasoning || 'AI-optimized recommendation',
          
          // Additional fields
          commute_cost: optionData.commute_cost || rec.commute_cost,
          environmental_impact: optionData.environmental_impact || rec.environmental_impact,
          confidence_score: rec.confidence_score,
          title: rec.title
        };
      });
      
      console.log('✅ Transformed recommendations:', transformedRecommendations);
      setCommuteRecommendations(transformedRecommendations);
      setSelectedCommuteOption(0); // Select first option by default
      console.log('✅ Set recommendations:', transformedRecommendations.length, 'options');
    } else {
      console.log('❌ No valid recommendations found to display');
      setCommuteRecommendations([]);
    }
  };

  // Handle event clicks
  const handleEventClick = (event: CalendarEvent) => {
    console.log('🎯 EnhancedDashboard handleEventClick called:', event);
    console.log('🎯 Setting modal state - selectedEvent:', event);
    console.log('🎯 Setting isEventModalOpen to true');
    setSelectedEvent(event);
    setIsEventModalOpen(true);
  };

  // Handle commute option selection
  const handleCommuteOptionSelect = (index: number) => {
    setSelectedCommuteOption(index);
  };

  // Close event modal
  const closeEventModal = () => {
    setIsEventModalOpen(false);
    setSelectedEvent(null);
  };

  // Format calendar events data
  const calendarEvents = calendarData?.calendarEvents || [];

  return (
    <div className="min-h-screen bg-gray-50" style={{ paddingLeft: '50px', paddingRight: '50px' }}>
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div style={{ width: '100%', padding: '16px 24px' }}>
          <div style={{ display: 'flex', justifyContent: 'flex-end', width: '100%' }}>
            <button
              onClick={logout}
              className="btn btn-secondary text-sm"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            AI Commute Planner
          </h1>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          
          {/* Left Column: Calendar + Planning */}
          <div className="xl:col-span-2 space-y-6">
            {/* Planning Widget */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <CommutePlannerWidget 
                enabled={true}
                onPlanningStart={() => setIsLoadingRecommendations(true)}
                onPlanningComplete={(results) => {
                  setIsLoadingRecommendations(false);
                  handlePlanningComplete(results);
                }}
              />
            </div>

            {/* Calendar Visualization */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              {calendarLoading ? (
                <div className="text-center py-12">
                  <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                  <p className="text-gray-600">Loading your calendar...</p>
                </div>
              ) : (
                <CalendarVisualization
                  meetings={calendarEvents}
                  commuteOptions={commuteRecommendations}
                  selectedOption={selectedCommuteOption}
                  onEventClick={handleEventClick}
                />
              )}
            </div>
          </div>

          {/* Right Column: Options + Tools */}
          <div className="space-y-6">
            {/* Commute Options */}
            <CommuteOptionsPanel
              options={commuteRecommendations}
              selectedOption={selectedCommuteOption}
              onOptionSelect={handleCommuteOptionSelect}
              isLoading={isLoadingRecommendations}
            />

            {/* Demo Data Widget */}
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="p-6 border-b">
                <h3 className="text-lg font-semibold text-gray-900">
                  Demo Data
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  Generate realistic calendar events for testing
                </p>
              </div>
              <div className="p-6">
                <DemoDataWidget 
                  onDataGenerated={() => {
                    console.log(`🔄 Refetching calendar for target date: ${targetDate}`);
                    refetchCalendar();
                  }}
                />
              </div>
            </div>

            {/* Stats Card */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Quick Stats
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Calendar events</span>
                  <span className="font-semibold">{calendarEvents.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Commute options</span>
                  <span className="font-semibold">{commuteRecommendations.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Office meetings</span>
                  <span className="font-semibold">
                    {calendarEvents.filter((e: any) => 
                      e.attendanceMode === 'MUST_BE_IN_OFFICE'
                    ).length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Remote meetings</span>
                  <span className="font-semibold">
                    {calendarEvents.filter((e: any) => 
                      e.attendanceMode === 'CAN_BE_REMOTE'
                    ).length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Section: Instructions */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <div>
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                How it works
              </h3>
              <div className="text-blue-800 space-y-1">
                <p>• <strong>Generate demo data</strong> to populate your calendar with realistic meetings</p>
                <p>• <strong>Create a commute plan</strong> and our AI will analyze your schedule</p>
                <p>• <strong>View recommendations</strong> as overlays on your calendar visualization</p>
                <p>• <strong>Click any event</strong> to see detailed information and meeting context</p>
                <p>• <strong>Select different options</strong> to compare AI recommendations side-by-side</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Event Details Modal */}
      <EventDetailsModal
        event={selectedEvent}
        isOpen={isEventModalOpen}
        onClose={closeEventModal}
      />
    </div>
  );
};

export default EnhancedDashboard;