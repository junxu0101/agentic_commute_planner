/**
 * Gateway service with proper GraphQL federation and Redis queue orchestration
 */

import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import { ApolloServerPluginDrainHttpServer } from '@apollo/server/plugin/drainHttpServer';
import { makeExecutableSchema } from '@graphql-tools/schema';
import { WebSocketServer } from 'ws';
import { useServer } from 'graphql-ws/lib/use/ws';
import express from 'express';
import http from 'http';
import cors from 'cors';
import { typeDefs } from './schemas';
import { resolvers, pubsub, Context } from './resolvers';
import { RedisService, JobProgress } from './services/redis';
import config from './config';

async function startServer() {
  // Initialize Redis service only (no direct database access)
  console.log('Initializing Gateway services...');
  
  const redis = new RedisService();

  // Connect to Redis
  try {
    await redis.connect();
    console.log('Redis service connected successfully');
  } catch (error) {
    console.error('Failed to connect to Redis:', error);
    process.exit(1);
  }

  // Set up Redis progress listener for GraphQL subscriptions
  redis.subscribeToAllProgress((progress: JobProgress) => {
    console.log(`Received progress update for job ${progress.jobId}: ${Math.round(progress.progress * 100)}%`);
    
    // Publish to GraphQL subscription for specific job
    pubsub.publish(`JOB_PROGRESS_${progress.jobId}`, { jobProgress: progress });
    
    // Publish to global subscription
    pubsub.publish('JOB_PROGRESS', { jobProgress: progress });
  });

  // Create Express app
  const app = express();
  const httpServer = http.createServer(app);

  // Create GraphQL schema
  const schema = makeExecutableSchema({
    typeDefs,
    resolvers,
  });

  // Create WebSocket server for subscriptions
  const wsServer = new WebSocketServer({
    server: httpServer,
    path: '/graphql',
  });

  // Save the returned server's info so we can shutdown this server later
  const serverCleanup = useServer(
    {
      schema,
      context: async (): Promise<Context> => ({
        redis,
      }),
    },
    wsServer
  );

  // Create Apollo Server
  const server = new ApolloServer<Context>({
    schema,
    plugins: [
      // Proper shutdown for the HTTP server
      ApolloServerPluginDrainHttpServer({ httpServer }),
      
      // Proper shutdown for the WebSocket server
      {
        async serverWillStart() {
          return {
            async drainServer() {
              await serverCleanup.dispose();
            },
          };
        },
      },
    ],
  });

  // Start Apollo Server
  await server.start();

  // Set up CORS
  const corsOptions = {
    origin: config.corsOrigin,
    credentials: true,
  };

  // Apply middleware
  app.use(
    '/graphql',
    cors<cors.CorsRequest>(corsOptions),
    express.json({ limit: '50mb' }),
    expressMiddleware(server, {
      context: async (): Promise<Context> => ({
        redis,
      }),
    })
  );

  // Health check endpoint
  app.get('/health', async (req, res) => {
    try {
      const queueLength = await redis.getQueueLength();
      const healthData = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        services: {
          redis: redis.isHealthy(),
          queue: queueLength,
          backend: config.backendServiceUrl,
        },
      };
      
      res.json(healthData);
    } catch (error) {
      console.error('Health check failed:', error);
      res.status(503).json({
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: 'Service unavailable',
      });
    }
  });

  // Graceful shutdown handling
  const gracefulShutdown = async () => {
    console.log('Received shutdown signal, gracefully shutting down...');
    
    try {
      // Stop accepting new connections
      httpServer.close();
      
      // Stop Apollo Server
      await server.stop();
      
      // Disconnect from Redis
      await redis.disconnect();
      
      console.log('Gateway service shut down successfully');
      process.exit(0);
    } catch (error) {
      console.error('Error during shutdown:', error);
      process.exit(1);
    }
  };

  // Handle shutdown signals
  process.on('SIGTERM', gracefulShutdown);
  process.on('SIGINT', gracefulShutdown);

  // Start HTTP server
  const PORT = config.port;
  httpServer.listen(PORT, () => {
    console.log(`🚀 Gateway server ready!`);
    console.log(`📊 GraphQL endpoint: http://localhost:${PORT}/graphql`);
    console.log(`🔄 GraphQL subscriptions: ws://localhost:${PORT}/graphql`);
    console.log(`💚 Health check: http://localhost:${PORT}/health`);
    console.log(`🌍 Environment: ${config.nodeEnv}`);
    console.log(`🔗 Backend service: ${config.backendServiceUrl}`);
  });
}

// Start the server
startServer().catch((error) => {
  console.error('Failed to start Gateway service:', error);
  process.exit(1);
});