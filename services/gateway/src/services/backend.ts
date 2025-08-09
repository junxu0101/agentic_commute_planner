/**
 * Backend service client for GraphQL federation
 */

import { GraphQLError } from 'graphql';

export interface User {
  id: string;
  email: string;
  name: string;
  userPreferences?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Job {
  id: string;
  userId: string;
  status: string;
  progress: number;
  currentStep?: string;
  targetDate: string;
  inputData?: string;
  result?: string;
  errorMessage?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CalendarEvent {
  id: string;
  userId: string;
  summary: string;
  description?: string;
  startTime: string;
  endTime: string;
  location?: string;
  attendees?: string;
  meetingType: string;
  attendanceMode: string;
  isAllDay: boolean;
  isRecurring: boolean;
  googleEventId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CommuteRecommendation {
  id: string;
  jobId: string;
  optionRank: number;
  optionType: string;
  commuteStart?: string;
  officeArrival?: string;
  officeDeparture?: string;
  commuteEnd?: string;
  officeDuration?: string;
  officeMeetings?: string;
  remoteMeetings?: string;
  businessRuleCompliance?: string;
  perceptionAnalysis?: string;
  reasoning?: string;
  tradeOffs?: string;
  createdAt: string;
}

export class BackendService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async makeGraphQLRequest(query: string, variables?: any): Promise<any> {
    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          query,
          variables,
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend service responded with status: ${response.status}`);
      }

      const result: any = await response.json();

      if (result.errors) {
        console.error('Backend GraphQL errors:', result.errors);
        throw new Error(`Backend GraphQL error: ${result.errors[0]?.message || 'Unknown error'}`);
      }

      return result.data;
    } catch (error) {
      console.error('Error calling backend service:', error);
      throw error;
    }
  }

  // User operations
  async getUser(id: string): Promise<User | null> {
    const query = `
      query GetUser($id: ID!) {
        user(id: $id) {
          id
          email
          name
          userPreferences
          createdAt
          updatedAt
        }
      }
    `;

    const data = await this.makeGraphQLRequest(query, { id });
    return data?.user || null;
  }

  async getUsers(): Promise<User[]> {
    const query = `
      query GetUsers {
        users {
          id
          email
          name
          userPreferences
          createdAt
          updatedAt
        }
      }
    `;

    const data = await this.makeGraphQLRequest(query);
    return data?.users || [];
  }

  async createUser(input: {
    email: string;
    name: string;
    userPreferences?: string;
  }): Promise<User> {
    const mutation = `
      mutation CreateUser($input: CreateUserInput!) {
        createUser(input: $input) {
          id
          email
          name
          userPreferences
          createdAt
          updatedAt
        }
      }
    `;

    const data = await this.makeGraphQLRequest(mutation, { input });
    return data.createUser;
  }

  async updateUser(id: string, input: {
    email?: string;
    name?: string;
    userPreferences?: string;
  }): Promise<User> {
    const mutation = `
      mutation UpdateUser($id: ID!, $input: UpdateUserInput!) {
        updateUser(id: $id, input: $input) {
          id
          email
          name
          userPreferences
          createdAt
          updatedAt
        }
      }
    `;

    const data = await this.makeGraphQLRequest(mutation, { id, input });
    return data.updateUser;
  }

  async deleteUser(id: string): Promise<boolean> {
    const mutation = `
      mutation DeleteUser($id: ID!) {
        deleteUser(id: $id)
      }
    `;

    const data = await this.makeGraphQLRequest(mutation, { id });
    return data.deleteUser;
  }

  // Job operations
  async getJob(id: string): Promise<Job | null> {
    const query = `
      query GetJob($id: ID!) {
        job(id: $id) {
          id
          userId
          status
          progress
          currentStep
          targetDate
          inputData
          result
          errorMessage
          createdAt
          updatedAt
        }
      }
    `;

    const data = await this.makeGraphQLRequest(query, { id });
    return data?.job || null;
  }

  async getJobs(userId?: string): Promise<Job[]> {
    const query = `
      query GetJobs($userId: ID) {
        jobs(userId: $userId) {
          id
          userId
          status
          progress
          currentStep
          targetDate
          inputData
          result
          errorMessage
          createdAt
          updatedAt
        }
      }
    `;

    const data = await this.makeGraphQLRequest(query, { userId });
    return data?.jobs || [];
  }

  async createJob(input: {
    userId: string;
    targetDate: string;
    inputData?: string;
  }): Promise<Job> {
    const mutation = `
      mutation CreateJob($input: CreateJobInput!) {
        createJob(input: $input) {
          id
          userId
          status
          progress
          currentStep
          targetDate
          inputData
          result
          errorMessage
          createdAt
          updatedAt
        }
      }
    `;

    const data = await this.makeGraphQLRequest(mutation, { input });
    return data.createJob;
  }

  async updateJob(id: string, input: {
    status?: string;
    progress?: number;
    currentStep?: string;
    result?: string;
    errorMessage?: string;
  }): Promise<Job> {
    const mutation = `
      mutation UpdateJob($id: ID!, $input: UpdateJobInput!) {
        updateJob(id: $id, input: $input) {
          id
          userId
          status
          progress
          currentStep
          targetDate
          inputData
          result
          errorMessage
          createdAt
          updatedAt
        }
      }
    `;

    const data = await this.makeGraphQLRequest(mutation, { id, input });
    return data.updateJob;
  }

  async deleteJob(id: string): Promise<boolean> {
    const mutation = `
      mutation DeleteJob($id: ID!) {
        deleteJob(id: $id)
      }
    `;

    const data = await this.makeGraphQLRequest(mutation, { id });
    return data.deleteJob;
  }

  // Calendar event operations
  async getCalendarEvents(userId: string): Promise<CalendarEvent[]> {
    const query = `
      query GetCalendarEvents($userId: ID!) {
        calendarEvents(userId: $userId) {
          id
          userId
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
          googleEventId
          createdAt
          updatedAt
        }
      }
    `;

    const data = await this.makeGraphQLRequest(query, { userId });
    return data?.calendarEvents || [];
  }

  // Commute recommendation operations
  async getCommuteRecommendations(jobId: string): Promise<CommuteRecommendation[]> {
    const query = `
      query GetCommuteRecommendations($jobId: ID!) {
        commuteRecommendations(jobId: $jobId) {
          id
          jobId
          optionRank
          optionType
          commuteStart
          officeArrival
          officeDeparture
          commuteEnd
          officeDuration
          officeMeetings
          remoteMeetings
          businessRuleCompliance
          perceptionAnalysis
          reasoning
          tradeOffs
          createdAt
        }
      }
    `;

    const data = await this.makeGraphQLRequest(query, { jobId });
    return data?.commuteRecommendations || [];
  }
}