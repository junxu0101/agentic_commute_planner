/**
 * Input validation utilities
 */

export function validateDateString(dateString: string): boolean {
  const date = new Date(dateString);
  return !isNaN(date.getTime()) && !!dateString.match(/^\d{4}-\d{2}-\d{2}$/);
}

export function validateUserId(userId: string): boolean {
  return typeof userId === 'string' && userId.length > 0 && userId.length <= 255;
}

export function sanitizeInput(input: string): string {
  return input.trim().replace(/[<>]/g, '');
}

export function validateJobId(jobId: string): boolean {
  // UUID v4 format validation
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(jobId);
}