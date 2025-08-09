import { ApolloClient, InMemoryCache, createHttpLink, split } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';
import { getMainDefinition } from '@apollo/client/utilities';

// HTTP link for queries and mutations
const httpLink = createHttpLink({
  uri: 'http://localhost:4000/graphql',
});

// WebSocket link for subscriptions (real-time job progress)
const wsLink = new GraphQLWsLink(
  createClient({
    url: 'ws://localhost:4000/graphql',
    connectionParams: () => {
      const token = localStorage.getItem('commute_planner_token');
      return {
        authorization: token ? `Bearer ${token}` : '',
      };
    },
  })
);

// Auth link - automatically adds JWT token to requests
const authLink = setContext((_, { headers }) => {
  const token = localStorage.getItem('commute_planner_token');
  
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
    },
  };
});

// Split link - HTTP for queries/mutations, WebSocket for subscriptions
const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  authLink.concat(httpLink)
);

// Apollo Client configuration
export const apolloClient = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache({
    typePolicies: {
      User: {
        fields: {
          jobs: {
            merge: true,
          },
          calendarEvents: {
            merge: true,
          },
        },
      },
      Job: {
        fields: {
          recommendations: {
            merge: true,
          },
        },
      },
    },
  }),
  defaultOptions: {
    watchQuery: {
      errorPolicy: 'all',
    },
    query: {
      errorPolicy: 'all',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
});