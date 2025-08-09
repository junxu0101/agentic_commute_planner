/**
 * Federation utilities for connecting to backend services
 */

import { RemoteGraphQLDataSource } from '@apollo/gateway';
import config from '../config';

export class BackendDataSource extends RemoteGraphQLDataSource {
  constructor() {
    super();
    this.url = config.backendServiceUrl;
  }

  willSendRequest({ request, context }: any) {
    // Add authentication headers if needed
    if (context.token) {
      request.http.headers.set('authorization', context.token);
    }
    
    // Add request ID for tracing
    request.http.headers.set('x-request-id', context.requestId || 'unknown');
  }

  didReceiveResponse({ response, request, context }: any) {
    // Log response for debugging
    console.log(`Backend response: ${response.http.status} for ${request.operationName}`);
    return response;
  }

  didEncounterError(error: any, request: any) {
    console.error('Backend service error:', {
      error: error.message,
      operation: request.operationName,
      variables: request.variables,
    });
  }
}

export class AIServiceDataSource extends RemoteGraphQLDataSource {
  constructor() {
    super();
    this.url = config.aiServiceUrl;
  }

  willSendRequest({ request, context }: any) {
    if (context.token) {
      request.http.headers.set('authorization', context.token);
    }
    
    request.http.headers.set('x-request-id', context.requestId || 'unknown');
  }

  didReceiveResponse({ response, request, context }: any) {
    console.log(`AI service response: ${response.http.status} for ${request.operationName}`);
    return response;
  }

  didEncounterError(error: any, request: any) {
    console.error('AI service error:', {
      error: error.message,
      operation: request.operationName,
      variables: request.variables,
    });
  }
}