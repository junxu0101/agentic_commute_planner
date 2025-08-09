/**
 * Configuration management for the Gateway service
 */

import dotenv from 'dotenv';

dotenv.config();

export interface Config {
  port: number;
  backendServiceUrl: string;
  aiServiceUrl: string;
  databaseUrl: string;
  redisUrl: string;
  redisJobQueue: string;
  redisProgressChannel: string;
  corsOrigin: string;
  nodeEnv: string;
}

export const config: Config = {
  port: parseInt(process.env.PORT || '4000'),
  backendServiceUrl: process.env.BACKEND_SERVICE_URL || 'http://localhost:8080/graphql',
  aiServiceUrl: process.env.AI_SERVICE_URL || 'http://localhost:8000/graphql',
  databaseUrl: process.env.DATABASE_URL || 'postgres://commute_planner:dev_password@localhost:5432/commute_planner',
  redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
  redisJobQueue: process.env.REDIS_JOB_QUEUE || 'commute_jobs',
  redisProgressChannel: process.env.REDIS_PROGRESS_CHANNEL || 'job_progress',
  corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  nodeEnv: process.env.NODE_ENV || 'development',
};

export default config;