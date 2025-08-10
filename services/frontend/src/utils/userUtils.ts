/**
 * User utilities for demo vs real user handling
 */

export interface UserContext {
  isDemoUser: boolean;
  fallbackStrategy: 'demo_data_fallback' | 'fail_fast';
  allowMockData: boolean;
}

// Demo user patterns (should match backend)
const DEMO_USER_PATTERNS = ['demo', 'test', 'example', 'sample'];
const DEMO_USER_IDS = new Set(['demo-user-123', 'test-user-456', 'sample-user-789']);

export function isDemoUser(userId: string): boolean {
  if (!userId) return false;
  
  const userIdLower = userId.toLowerCase();
  
  // Check explicit demo user IDs
  if (DEMO_USER_IDS.has(userId)) {
    return true;
  }
  
  // Check demo patterns in user ID
  return DEMO_USER_PATTERNS.some(pattern => userIdLower.includes(pattern));
}

export function getUserContext(userId: string): UserContext {
  const isDemo = isDemoUser(userId);
  
  return {
    isDemoUser: isDemo,
    fallbackStrategy: isDemo ? 'demo_data_fallback' : 'fail_fast',
    allowMockData: isDemo
  };
}

export function formatUserType(userId: string): string {
  return isDemoUser(userId) ? 'Demo User' : 'Real User';
}