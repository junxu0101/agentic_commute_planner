import React, { useState } from 'react';
import { Calendar, momentLocalizer, View, Event } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';

// Setup the localizer
const localizer = momentLocalizer(moment);

// Define our event types
interface CalendarEvent extends Event {
  id: string;
  title: string;
  start: Date;
  end: Date;
  type: 'meeting' | 'commute' | 'office-time';
  meetingType?: 'CLIENT_MEETING' | 'TEAM_MEETING' | 'ONE_ON_ONE' | 'PRESENTATION' | 'REVIEW' | 'STANDUP';
  attendanceMode?: 'MUST_BE_IN_OFFICE' | 'CAN_BE_REMOTE' | 'FLEXIBLE';
  location?: string;
  description?: string;
  attendees?: string[];
}

interface CalendarVisualizationProps {
  meetings: any[]; // Raw meeting data from backend
  commuteOptions?: any[]; // Commute recommendations
  selectedOption?: number; // Which commute option is selected
  onEventClick?: (event: CalendarEvent) => void;
  onDateClick?: (date: Date) => void;
}

const CalendarVisualization: React.FC<CalendarVisualizationProps> = ({
  meetings = [],
  commuteOptions = [],
  selectedOption = 0,
  onEventClick,
  onDateClick
}) => {
  const [currentView, setCurrentView] = useState<View>('week');

  // Convert meeting data to calendar events
  const convertMeetingsToEvents = (meetings: any[]): CalendarEvent[] => {
    return meetings.map(meeting => ({
      id: meeting.id,
      title: meeting.summary || 'Untitled Meeting',
      start: new Date(meeting.start_time || meeting.startTime),
      end: new Date(meeting.end_time || meeting.endTime),
      type: 'meeting' as const,
      meetingType: meeting.meeting_type || meeting.meetingType,
      attendanceMode: meeting.attendance_mode || meeting.attendanceMode,
      location: meeting.location,
      description: meeting.description,
      attendees: meeting.attendees
    }));
  };

  // Convert commute recommendations to calendar events
  const convertCommuteToEvents = (commuteOption: any): CalendarEvent[] => {
    if (!commuteOption) return [];

    const events: CalendarEvent[] = [];

    // Add commute to office
    if (commuteOption.commute_start && commuteOption.office_arrival) {
      events.push({
        id: `commute-to-${commuteOption.id || 'office'}`,
        title: '🚗 Commute to Office',
        start: new Date(commuteOption.commute_start),
        end: new Date(commuteOption.office_arrival),
        type: 'commute'
      });
    }

    // Add office time block
    if (commuteOption.office_arrival && commuteOption.office_departure) {
      events.push({
        id: `office-time-${commuteOption.id || 'block'}`,
        title: '🏢 Office Time',
        start: new Date(commuteOption.office_arrival),
        end: new Date(commuteOption.office_departure),
        type: 'office-time'
      });
    }

    // Add commute from office
    if (commuteOption.office_departure && commuteOption.commute_end) {
      events.push({
        id: `commute-from-${commuteOption.id || 'office'}`,
        title: '🚗 Commute Home',
        start: new Date(commuteOption.office_departure),
        end: new Date(commuteOption.commute_end),
        type: 'commute'
      });
    }

    return events;
  };

  // Combine all events
  const meetingEvents = convertMeetingsToEvents(meetings);
  const commuteEvents = selectedOption !== undefined && commuteOptions[selectedOption] 
    ? convertCommuteToEvents(commuteOptions[selectedOption])
    : [];
  
  const allEvents = [...meetingEvents, ...commuteEvents];

  // Custom event styling
  const eventStyleGetter = (event: CalendarEvent) => {
    let style = {
      borderRadius: '4px',
      border: 'none',
      color: 'white',
      fontSize: '12px',
      fontWeight: '500'
    };

    switch (event.type) {
      case 'meeting':
        // Color based on attendance mode
        if (event.attendanceMode === 'MUST_BE_IN_OFFICE') {
          return { style: { ...style, backgroundColor: '#DC2626' } }; // Red for must-be-in-office
        } else if (event.attendanceMode === 'CAN_BE_REMOTE') {
          return { style: { ...style, backgroundColor: '#059669' } }; // Green for remote-ok
        } else {
          return { style: { ...style, backgroundColor: '#7C3AED' } }; // Purple for flexible
        }
      
      case 'commute':
        return { 
          style: {
            ...style, 
            backgroundColor: '#F59E0B', // Amber for commute
            opacity: 0.8
          }
        };
      
      case 'office-time':
        return { 
          style: {
            ...style, 
            backgroundColor: '#3B82F6', // Blue for office time
            opacity: 0.3
          }
        };
      
      default:
        return { style: { ...style, backgroundColor: '#6B7280' } }; // Gray default
    }
  };

  // Custom event component for better display
  const CustomEvent: React.FC<{ event: CalendarEvent }> = ({ event }) => {
    const getEventIcon = () => {
      switch (event.type) {
        case 'meeting':
          if (event.meetingType === 'CLIENT_MEETING') return '👔';
          if (event.meetingType === 'PRESENTATION') return '📊';
          if (event.meetingType === 'ONE_ON_ONE') return '💬';
          if (event.meetingType === 'STANDUP') return '⚡';
          return '🗓';
        case 'commute':
          return '🚗';
        case 'office-time':
          return '🏢';
        default:
          return '';
      }
    };

    return (
      <div className="flex items-center space-x-1 h-full">
        <span>{getEventIcon()}</span>
        <span className="truncate text-xs">{event.title}</span>
      </div>
    );
  };

  // Handle event selection
  const handleSelectEvent = (event: CalendarEvent) => {
    console.log('🗓 Calendar event clicked:', event);
    if (onEventClick) {
      onEventClick(event);
    } else {
      console.log('❌ No onEventClick handler provided');
    }
  };

  // Handle date/slot selection
  const handleSelectSlot = ({ start }: { start: Date }) => {
    if (onDateClick) {
      onDateClick(start);
    }
  };

  return (
    <div className="calendar-visualization">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          Your Calendar
        </h3>
        
        {/* Static Legend - Event Types */}
        <div className="bg-gray-50 p-3 rounded-lg mb-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div 
                style={{ 
                  width: '12px', 
                  height: '12px', 
                  borderRadius: '2px',
                  backgroundColor: '#DC2626',
                  flexShrink: 0,
                  display: 'inline-block'
                }}
              ></div>
              <span style={{ flex: 1 }}>In-office required meetings</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div 
                style={{ 
                  width: '12px', 
                  height: '12px', 
                  borderRadius: '2px',
                  backgroundColor: '#059669',
                  flexShrink: 0,
                  display: 'inline-block'
                }}
              ></div>
              <span style={{ flex: 1 }}>Remote-friendly meetings</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div 
                style={{ 
                  width: '12px', 
                  height: '12px', 
                  borderRadius: '2px',
                  backgroundColor: '#7C3AED',
                  flexShrink: 0,
                  display: 'inline-block'
                }}
              ></div>
              <span style={{ flex: 1 }}>Flexible location meetings</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div 
                style={{ 
                  width: '12px', 
                  height: '12px', 
                  borderRadius: '2px',
                  backgroundColor: '#F59E0B',
                  opacity: 0.8,
                  flexShrink: 0,
                  display: 'inline-block'
                }}
              ></div>
              <span style={{ flex: 1 }}>Commute recommendations</span>
            </div>
          </div>
        </div>
      </div>

      {/* Calendar */}
      <div style={{ height: '600px' }} className="border rounded-lg overflow-hidden">
        <Calendar
          localizer={localizer}
          events={allEvents}
          startAccessor="start"
          endAccessor="end"
          view={currentView}
          onView={setCurrentView}
          views={['month', 'week', 'day']}
          defaultView="week"
          onSelectEvent={handleSelectEvent}
          onSelectSlot={handleSelectSlot}
          selectable
          eventPropGetter={eventStyleGetter}
          components={{
            event: CustomEvent
          }}
          step={30}
          timeslots={2}
          min={new Date(0, 0, 0, 0, 0, 0)} // 12 AM (midnight)
          max={new Date(0, 0, 0, 23, 59, 59)} // 11:59 PM (end of day)
          formats={{
            timeGutterFormat: 'h A',
            dayHeaderFormat: 'ddd M/D',
            agendaTimeFormat: 'h:mm A'
          }}
        />
      </div>

      {/* Meeting count summary */}
      <div className="mt-4 text-sm text-gray-600">
        <span>📊 {meetingEvents.length} meetings scheduled</span>
        {commuteEvents.length > 0 && (
          <span> • 🚗 {commuteEvents.filter(e => e.type === 'commute').length} commute blocks</span>
        )}
      </div>
    </div>
  );
};

export default CalendarVisualization;