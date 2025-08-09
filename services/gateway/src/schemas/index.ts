/**
 * Gateway GraphQL schema - Federation layer with job queue orchestration
 */

import { gql } from 'graphql-tag';

export const typeDefs = gql`
  # Job progress subscription payload for real-time updates
  type JobProgress {
    jobId: ID!
    status: String!
    progress: Float!
    currentStep: String
    result: String
    errorMessage: String
    timestamp: String!
  }

  # Input types for job creation
  input CreateCommuteJobInput {
    userId: ID!
    targetDate: String!
    inputData: String
  }

  # Queue status information
  type QueueStatus {
    length: Int!
    processing: Int!
  }

  # Health check response
  type HealthStatus {
    status: String!
    redis: Boolean!
    queue: Int!
    backend: String!
    timestamp: String!
  }

  # Gateway-specific queries and mutations
  type Query {
    # Queue management
    queueStatus: QueueStatus!
    
    # Health check
    gatewayHealth: HealthStatus!

    # Federated queries (delegated to backend)
    user(id: ID!): User
    users: [User!]!
    job(id: ID!): Job
    jobs(userId: ID): [Job!]!
    calendarEvents(userId: ID!): [CalendarEvent!]!
    commuteRecommendations(jobId: ID!): [CommuteRecommendation!]!
  }

  type Mutation {
    # Gateway orchestration - creates job via backend + queues for AI processing
    createCommuteJob(input: CreateCommuteJobInput!): Job!

    # Federated mutations (delegated to backend)
    createUser(input: CreateUserInput!): User!
    updateUser(id: ID!, input: UpdateUserInput!): User!
    deleteUser(id: ID!): Boolean!
    updateJob(id: ID!, input: UpdateJobInput!): Job!
    deleteJob(id: ID!): Boolean!
  }

  type Subscription {
    # Real-time job progress updates
    jobProgress(jobId: ID): JobProgress!
  }

  # Types that will be resolved by the backend service
  # These are placeholders - actual resolution happens via federation

  scalar Time

  enum JobStatus {
    PENDING
    IN_PROGRESS
    COMPLETED
    FAILED
  }

  enum CommuteOptionType {
    FULL_DAY_OFFICE
    STRATEGIC_AFTERNOON
    FULL_REMOTE_RECOMMENDED
  }

  enum MeetingType {
    CLIENT_MEETING
    PRESENTATION
    TEAM_WORKSHOP
    INTERVIEW
    STAKEHOLDER_MEETING
    ONE_ON_ONE
    STATUS_UPDATE
    REVIEW
    BRAINSTORMING
    CHECK_IN
    UNKNOWN
  }

  enum AttendanceMode {
    MUST_BE_IN_OFFICE
    CAN_BE_REMOTE
    FLEXIBLE
  }

  type User {
    id: ID!
    email: String!
    name: String!
    userPreferences: String
    createdAt: Time!
    updatedAt: Time!
  }

  type Job {
    id: ID!
    userId: ID!
    user: User
    status: JobStatus!
    progress: Float!
    currentStep: String
    targetDate: String!
    inputData: String
    result: String
    errorMessage: String
    createdAt: Time!
    updatedAt: Time!
    recommendations: [CommuteRecommendation!]
  }

  type CalendarEvent {
    id: ID!
    userId: ID!
    user: User
    summary: String!
    description: String
    startTime: Time!
    endTime: Time!
    location: String
    attendees: String
    meetingType: MeetingType!
    attendanceMode: AttendanceMode!
    isAllDay: Boolean!
    isRecurring: Boolean!
    googleEventId: String
    createdAt: Time!
    updatedAt: Time!
  }

  type CommuteRecommendation {
    id: ID!
    jobId: ID!
    job: Job
    optionRank: Int!
    optionType: CommuteOptionType!
    commuteStart: Time
    officeArrival: Time
    officeDeparture: Time
    commuteEnd: Time
    officeDuration: String
    officeMeetings: String
    remoteMeetings: String
    businessRuleCompliance: String
    perceptionAnalysis: String
    reasoning: String
    tradeOffs: String
    createdAt: Time!
  }

  # Input types
  input CreateUserInput {
    email: String!
    name: String!
    userPreferences: String
  }

  input UpdateUserInput {
    email: String
    name: String
    userPreferences: String
  }

  input UpdateJobInput {
    status: JobStatus
    progress: Float
    currentStep: String
    result: String
    errorMessage: String
  }
`;