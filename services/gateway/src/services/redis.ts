/**
 * Redis service for job queue management and pub/sub
 */

import { createClient, RedisClientType } from 'redis';
import config from '../config';

export interface JobProgress {
  jobId: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  progress: number;
  currentStep?: string;
  result?: any;
  errorMessage?: string;
  timestamp: string;
}

export interface JobData {
  job_id: string;
  user_id: string;
  target_date: string;
}

export class RedisService {
  private client: RedisClientType;
  private subscriber: RedisClientType;
  private isConnected = false;
  private progressListeners = new Map<string, (progress: JobProgress) => void>();

  constructor() {
    this.client = createClient({ url: config.redisUrl });
    this.subscriber = createClient({ url: config.redisUrl });

    // Handle connection errors
    this.client.on('error', (err) => {
      console.error('Redis Client Error:', err);
    });

    this.subscriber.on('error', (err) => {
      console.error('Redis Subscriber Error:', err);
    });

    this.client.on('connect', () => {
      console.log('Redis client connected');
    });

    this.subscriber.on('connect', () => {
      console.log('Redis subscriber connected');
    });
  }

  async connect(): Promise<void> {
    try {
      await Promise.all([
        this.client.connect(),
        this.subscriber.connect(),
      ]);

      // Subscribe to job progress updates
      await this.subscriber.subscribe(config.redisProgressChannel, (message) => {
        try {
          const progress: JobProgress = JSON.parse(message);
          // Keep timestamp as ISO string for frontend parsing compatibility
          
          // Notify all listeners for this job
          const listener = this.progressListeners.get(progress.jobId);
          if (listener) {
            listener(progress);
          }
          
          // Notify global listeners (for subscriptions)
          const globalListener = this.progressListeners.get('*');
          if (globalListener) {
            globalListener(progress);
          }
        } catch (error) {
          console.error('Error parsing job progress message:', error);
        }
      });

      this.isConnected = true;
      console.log('Redis service connected and subscribed to progress updates');
    } catch (error) {
      console.error('Error connecting to Redis:', error);
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    try {
      await Promise.all([
        this.client.disconnect(),
        this.subscriber.disconnect(),
      ]);
      this.isConnected = false;
      this.progressListeners.clear();
      console.log('Redis service disconnected');
    } catch (error) {
      console.error('Error disconnecting from Redis:', error);
      throw error;
    }
  }

  async pushJob(jobData: JobData): Promise<void> {
    try {
      await this.client.lPush(config.redisJobQueue, JSON.stringify(jobData));
      console.log(`Job ${jobData.job_id} pushed to queue`);
    } catch (error) {
      console.error('Error pushing job to queue:', error);
      throw new Error('Failed to queue job for processing');
    }
  }

  async getQueueLength(): Promise<number> {
    try {
      return await this.client.lLen(config.redisJobQueue);
    } catch (error) {
      console.error('Error getting queue length:', error);
      return 0;
    }
  }

  async publishProgress(progress: JobProgress): Promise<void> {
    try {
      await this.client.publish(
        config.redisProgressChannel,
        JSON.stringify(progress)
      );
    } catch (error) {
      console.error('Error publishing progress:', error);
      throw new Error('Failed to publish job progress');
    }
  }

  subscribeToJobProgress(jobId: string, listener: (progress: JobProgress) => void): void {
    this.progressListeners.set(jobId, listener);
  }

  subscribeToAllProgress(listener: (progress: JobProgress) => void): void {
    this.progressListeners.set('*', listener);
  }

  unsubscribeFromJobProgress(jobId: string): void {
    this.progressListeners.delete(jobId);
  }

  unsubscribeFromAllProgress(): void {
    this.progressListeners.delete('*');
  }

  async ping(): Promise<string> {
    try {
      return await this.client.ping();
    } catch (error) {
      console.error('Redis ping failed:', error);
      throw error;
    }
  }

  isHealthy(): boolean {
    return this.isConnected;
  }
}