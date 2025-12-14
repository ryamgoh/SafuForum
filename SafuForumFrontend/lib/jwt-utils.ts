/**
 * JWT Utilities for token management and validation
 */

interface JWTPayload {
  userId: number;
  role?: string;
  type: 'access' | 'refresh';
  sub: string;
  iat: number;
  exp: number;
}

/**
 * Decode a JWT token without verification (client-side only)
 * For verification, use backend
 */
export function decodeJWT(token: string): JWTPayload | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }

    const payload = parts[1];
    const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
    return decoded;
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
}

/**
 * Check if a JWT token is expired
 */
export function isTokenExpired(token: string): boolean {
  const decoded = decodeJWT(token);
  if (!decoded || !decoded.exp) {
    return true;
  }

  // exp is in seconds, Date.now() is in milliseconds
  const now = Date.now() / 1000;
  return decoded.exp < now;
}

/**
 * Check if token should be refreshed (within threshold of expiration)
 * @param token JWT token to check
 * @param thresholdMinutes Number of minutes before expiration to trigger refresh
 */
export function shouldRefreshToken(token: string, thresholdMinutes: number = 5): boolean {
  const decoded = decodeJWT(token);
  if (!decoded || !decoded.exp) {
    return true;
  }

  const now = Date.now() / 1000;
  const timeUntilExpiry = decoded.exp - now;
  const thresholdSeconds = thresholdMinutes * 60;

  return timeUntilExpiry < thresholdSeconds && timeUntilExpiry > 0;
}

/**
 * Get time until token expiration in seconds
 */
export function getTimeUntilExpiry(token: string): number {
  const decoded = decodeJWT(token);
  if (!decoded || !decoded.exp) {
    return 0;
  }

  const now = Date.now() / 1000;
  const timeUntilExpiry = decoded.exp - now;
  return Math.max(0, timeUntilExpiry);
}

/**
 * Get token type (access or refresh)
 */
export function getTokenType(token: string): 'access' | 'refresh' | null {
  const decoded = decodeJWT(token);
  return decoded?.type || null;
}

/**
 * Extract user ID from token
 */
export function getUserIdFromToken(token: string): number | null {
  const decoded = decodeJWT(token);
  return decoded?.userId || null;
}

/**
 * Extract user role from token
 */
export function getRoleFromToken(token: string): string | null {
  const decoded = decodeJWT(token);
  return decoded?.role || null;
}

