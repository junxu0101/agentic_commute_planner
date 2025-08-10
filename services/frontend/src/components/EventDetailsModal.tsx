import React from 'react';
import { createPortal } from 'react-dom';

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

interface EventDetailsModalProps {
  event: CalendarEvent | null;
  isOpen: boolean;
  onClose: () => void;
}

const EventDetailsModal: React.FC<EventDetailsModalProps> = ({
  event,
  isOpen,
  onClose
}) => {
  if (!isOpen || !event) return null;

  // Parse attendees if it's a JSON string
  const parseAttendees = (attendees: any): string[] => {
    if (Array.isArray(attendees)) {
      return attendees;
    }
    if (typeof attendees === 'string') {
      try {
        const parsed = JSON.parse(attendees);
        return Array.isArray(parsed) ? parsed : [];
      } catch {
        return [attendees]; // If parsing fails, treat as single attendee
      }
    }
    return [];
  };

  const attendeesList = parseAttendees(event.attendees);

  // Format date and time
  const formatDateTime = (date: Date): string => {
    return date.toLocaleString([], {
      weekday: 'long',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Get event type styling
  const getEventTypeInfo = () => {
    switch (event.type) {
      case 'meeting':
        return {
          icon: '🗓',
          color: 'bg-blue-50 border-blue-200',
          title: 'Meeting Details'
        };
      case 'commute':
        return {
          icon: '🚗',
          color: 'bg-amber-50 border-amber-200',
          title: 'Commute Details'
        };
      case 'office-time':
        return {
          icon: '🏢',
          color: 'bg-green-50 border-green-200',
          title: 'Office Presence'
        };
      default:
        return {
          icon: '📋',
          color: 'bg-gray-50 border-gray-200',
          title: 'Event Details'
        };
    }
  };

  const typeInfo = getEventTypeInfo();

  // Get attendance mode styling
  const getAttendanceModeInfo = (mode?: string) => {
    switch (mode) {
      case 'MUST_BE_IN_OFFICE':
        return { text: 'Must be in office', color: 'text-red-700 bg-red-100', icon: '🏢' };
      case 'CAN_BE_REMOTE':
        return { text: 'Can be remote', color: 'text-green-700 bg-green-100', icon: '🏠' };
      case 'FLEXIBLE':
        return { text: 'Flexible location', color: 'text-purple-700 bg-purple-100', icon: '⚡' };
      default:
        return null;
    }
  };

  const attendanceModeInfo = getAttendanceModeInfo(event.attendanceMode);

  const modalContent = (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 999999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        backgroundColor: 'rgba(0, 0, 0, 0.5)'
      }} 
      onClick={onClose}
    >
      <div 
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          width: '100%',
          maxWidth: '32rem',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: '20px'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`p-6 border-b ${typeInfo.color}`}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{typeInfo.icon}</span>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {event.title}
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  {typeInfo.title}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Time */}
          <div className="flex items-center gap-3">
            <span className="text-lg">🕒</span>
            <div>
              <div className="font-medium text-gray-900">
                {formatDateTime(event.start)}
              </div>
              <div className="text-sm text-gray-600">
                {formatTime(event.start)} - {formatTime(event.end)}
                <span className="ml-2 text-gray-500">
                  ({Math.round((event.end.getTime() - event.start.getTime()) / (1000 * 60))} min)
                </span>
              </div>
            </div>
          </div>

          {/* Attendance Mode */}
          {attendanceModeInfo && (
            <div className="flex items-center gap-3">
              <span className="text-lg">{attendanceModeInfo.icon}</span>
              <div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${attendanceModeInfo.color}`}>
                  {attendanceModeInfo.text}
                </span>
              </div>
            </div>
          )}

          {/* Location */}
          {event.location && (
            <div className="flex items-center gap-3">
              <span className="text-lg">📍</span>
              <div>
                <div className="font-medium text-gray-900">Location</div>
                <div className="text-sm text-gray-600">{event.location}</div>
              </div>
            </div>
          )}

          {/* Description */}
          {event.description && (
            <div className="flex items-start gap-3">
              <span className="text-lg mt-1">📝</span>
              <div className="flex-1">
                <div className="font-medium text-gray-900">Description</div>
                <div className="text-sm text-gray-600 mt-1 leading-relaxed">
                  {event.description}
                </div>
              </div>
            </div>
          )}

          {/* Attendees */}
          {attendeesList.length > 0 && (
            <div className="flex items-start gap-3">
              <span className="text-lg mt-1">👥</span>
              <div className="flex-1">
                <div className="font-medium text-gray-900">
                  Attendees ({attendeesList.length})
                </div>
                <div className="mt-2 space-y-1">
                  {attendeesList.slice(0, 5).map((attendee, index) => (
                    <div key={index} className="text-sm text-gray-600">
                      {attendee}
                    </div>
                  ))}
                  {attendeesList.length > 5 && (
                    <div className="text-sm text-gray-500">
                      +{attendeesList.length - 5} more...
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Meeting Type */}
          {event.meetingType && (
            <div className="flex items-center gap-3">
              <span className="text-lg">🏷️</span>
              <div>
                <div className="font-medium text-gray-900">Meeting Type</div>
                <div className="text-sm text-gray-600">
                  {event.meetingType.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}
                </div>
              </div>
            </div>
          )}

          {/* Event-specific info */}
          {event.type === 'commute' && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <div className="flex items-center gap-2 text-amber-800 font-medium mb-2">
                <span>🚗</span>
                Commute Information
              </div>
              <div className="text-sm text-amber-700">
                This is your planned commute time. Make sure to account for traffic conditions and any stops you need to make.
              </div>
            </div>
          )}

          {event.type === 'office-time' && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-2 text-blue-800 font-medium mb-2">
                <span>🏢</span>
                Office Presence Block
              </div>
              <div className="text-sm text-blue-700">
                This represents your planned office presence time, optimized around your meeting schedule.
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 rounded-b-lg">
          <button
            onClick={onClose}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );

  // Render modal using portal to document body to escape parent container constraints
  return createPortal(modalContent, document.body);
};

export default EventDetailsModal;