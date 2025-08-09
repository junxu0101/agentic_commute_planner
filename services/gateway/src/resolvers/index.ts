/**
 * Gateway GraphQL resolvers - Federation layer with backend service communication
 */

import { GraphQLError } from 'graphql';
import { PubSub } from 'graphql-subscriptions';
import { RedisService, JobProgress } from '../services/redis';
import { BackendService } from '../services/backend';
import config from '../config';

// Create a PubSub instance for GraphQL subscriptions
const pubsub = new PubSub();

export interface Context {
  redis: RedisService;
}

export interface CreateCommuteJobInput {
  userId: string;
  targetDate: string;
  inputData?: string;
}

// Backend service instance for GraphQL federation
const backendService = new BackendService(config.backendServiceUrl);

export const resolvers = {
  Query: {
    // Gateway-specific queries
    async queueStatus(_: any, __: any, { redis }: Context) {
      try {
        const length = await redis.getQueueLength();
        return {
          length,
          processing: 0, // Would need to track this separately
        };
      } catch (error) {
        console.error('Error fetching queue status:', error);
        throw new GraphQLError('Failed to fetch queue status', {
          extensions: { code: 'INTERNAL_ERROR' }
        });
      }
    },

    async gatewayHealth(_: any, __: any, { redis }: Context) {
      const timestamp = new Date().toISOString();
      
      try {
        const queueLength = await redis.getQueueLength();
        
        return {
          status: 'healthy',
          redis: redis.isHealthy(),
          queue: queueLength,
          backend: config.backendServiceUrl,
          timestamp,
        };
      } catch (error) {
        console.error('Health check error:', error);
        return {
          status: 'unhealthy',
          redis: false,
          queue: 0,
          backend: config.backendServiceUrl,
          timestamp,
        };
      }
    },

    // Federated queries - delegate to backend service
    async user(_: any, args: { id: string }) {
      try {
        return await backendService.getUser(args.id);
      } catch (error) {
        console.error('Error fetching user from backend:', error);
        throw new GraphQLError('Failed to fetch user', {
          extensions: { code: 'BACKEND_ERROR' }
        });
      }
    },

    async users() {
      try {
        return await backendService.getUsers();
      } catch (error) {
        console.error('Error fetching users from backend:', error);
        throw new GraphQLError('Failed to fetch users', {
          extensions: { code: 'BACKEND_ERROR' }
        });
      }
    },

    async job(_: any, args: { id: string }) {
      try {
        return await backendService.getJob(args.id);
      } catch (error) {
        console.error('Error fetching job from backend:', error);
        throw new GraphQLError('Failed to fetch job', {
          extensions: { code: 'BACKEND_ERROR' }
        });
      }
    },

    async jobs(_: any, args: { userId?: string }) {
      try {
        return await backendService.getJobs(args.userId);
      } catch (error) {
        console.error('Error fetching jobs from backend:', error);
        throw new GraphQLError('Failed to fetch jobs', {
          extensions: { code: 'BACKEND_ERROR' }
        });
      }
    },

    async calendarEvents(_: any, args: { userId: string }) {
      try {
        return await backendService.getCalendarEvents(args.userId);
      } catch (error) {
        console.error('Error fetching calendar events from backend:', error);
        throw new GraphQLError('Failed to fetch calendar events', {
          extensions: { code: 'BACKEND_ERROR' }
        });
      }
    },

    async commuteRecommendations(_: any, args: { jobId: string }) {
      try {
        return await backendService.getCommuteRecommendations(args.jobId);
      } catch (error) {
        console.error('Error fetching commute recommendations from backend:', error);
        throw new GraphQLError('Failed to fetch commute recommendations', {
          extensions: { code: 'BACKEND_ERROR' }
        });
      }
    },
  },

  Mutation: {
    // Gateway orchestration - create job via backend + queue for AI processing
    async createCommuteJob(
      _: any,
      { input }: { input: CreateCommuteJobInput },
      { redis }: Context
    ) {
      try {
        // Validate input
        if (!input.userId || !input.targetDate) {
          throw new GraphQLError('userId and targetDate are required', {
            extensions: { code: 'BAD_USER_INPUT' }
          });
        }

        // 1. Create job via backend service (proper microservices pattern)
        const job = await backendService.createJob({
          userId: input.userId,
          targetDate: input.targetDate,
          inputData: input.inputData,
        });

        // 2. Push job to Redis queue for AI processing
        await redis.pushJob({
          job_id: job.id,
          user_id: job.userId,
          target_date: job.targetDate,
        });

        console.log(`Created job ${job.id} via backend and queued for AI processing`);

        // 3. Publish initial progress update
        const initialProgress: JobProgress = {
          jobId: job.id,
          status: 'PENDING',
          progress: 0,
          currentStep: 'Queued for processing',
          timestamp: new Date(),
        };

        pubsub.publish('JOB_PROGRESS', { jobProgress: initialProgress });

        return job;
      } catch (error) {
        console.error('Error creating commute job:', error);
        
        if (error instanceof GraphQLError) {
          throw error;
        }
        
        throw new GraphQLError('Failed to create commute job', {
          extensions: { code: 'INTERNAL_ERROR' }
        });
      }
    },

    // Federated mutations - delegate to backend service
    async createUser(_: any, args: { input: any }) {
      try {
        return await backendService.createUser(args.input);
      } catch (error) {
        console.error('Error creating user via backend:', error);
        throw new GraphQLError('Failed to create user', {
          extensions: { code: 'BACKEND_ERROR' }
        });
      }
    },

    async updateUser(_: any, args: { id: string; input: any }) {
      try {
        return await backendService.updateUser(args.id, args.input);
      } catch (error) {
        console.error('Error updating user via backend:', error);
        throw new GraphQLError('Failed to update user', {
          extensions: { code: 'BACKEND_ERROR' }
        });
      }
    },

    async deleteUser(_: any, args: { id: string }) {
      try {
        return await backendService.deleteUser(args.id);
      } catch (error) {
        console.error('Error deleting user via backend:', error);
        throw new GraphQLError('Failed to delete user', {
          extensions: { code: 'BACKEND_ERROR' }
        });
      }
    },

    async updateJob(_: any, args: { id: string; input: any }) {
      try {
        return await backendService.updateJob(args.id, args.input);
      } catch (error) {
        console.error('Error updating job via backend:', error);
        throw new GraphQLError('Failed to update job', {
          extensions: { code: 'BACKEND_ERROR' }
        });
      }
    },

    async deleteJob(_: any, args: { id: string }) {
      try {
        return await backendService.deleteJob(args.id);
      } catch (error) {
        console.error('Error deleting job via backend:', error);
        throw new GraphQLError('Failed to delete job', {
          extensions: { code: 'BACKEND_ERROR' }
        });
      }
    },
  },

  Subscription: {
    jobProgress: {
      subscribe: (_: any, { jobId }: { jobId?: string }) => {
        console.log(`Client subscribed to job progress${jobId ? ` for job ${jobId}` : ' (all jobs)'}`);
        
        // If jobId is provided, filter for that specific job
        if (jobId) {
          return pubsub.asyncIterator([`JOB_PROGRESS_${jobId}`]);
        }
        
        // Otherwise, subscribe to all job progress updates
        return pubsub.asyncIterator(['JOB_PROGRESS']);
      },
    },
  },
};

export { pubsub };