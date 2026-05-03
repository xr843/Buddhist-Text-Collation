/**
 * Helpers for narrowing `unknown` errors caught from axios / fetch into
 * the shape the UI cares about, without scattering `error: any` across
 * every `catch` block. Use these in place of `error: any`.
 *
 * Usage:
 *   try { ... } catch (error) {
 *     const message = getApiErrorMessage(error, '登录失败')
 *     if (isAuthError(error)) { ... }
 *   }
 */

/** Subset of AxiosError we actually read at call sites. */
export interface ApiErrorShape {
  response?: {
    data?: { detail?: string; message?: string }
    status?: number
  }
  message?: string
}

/**
 * Pull the most useful human-readable message out of an unknown error.
 * Order: backend `detail` > backend `message` > axios `error.message` > fallback.
 */
export function getApiErrorMessage(error: unknown, fallback = ''): string {
  const e = error as ApiErrorShape
  return (
    e?.response?.data?.detail ||
    e?.response?.data?.message ||
    e?.message ||
    fallback
  )
}

/** True for 401 responses — used to trigger token-refresh flows. */
export function isAuthError(error: unknown): boolean {
  return (error as ApiErrorShape)?.response?.status === 401
}

/** Generic status-code check, e.g. `getErrorStatus(e) === 404`. */
export function getErrorStatus(error: unknown): number | undefined {
  return (error as ApiErrorShape)?.response?.status
}
