/**
 * Vitest global setup
 *
 * - Adds jest-dom matchers (toBeInTheDocument, toHaveTextContent, ...)
 * - Polyfills missing browser APIs that JSDOM doesn't ship
 */
import '@testing-library/jest-dom/vitest'

// matchMedia polyfill (antd uses it internally)
if (!window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  })
}

// IntersectionObserver polyfill
if (!('IntersectionObserver' in window)) {
  // @ts-expect-error simple stub for tests
  window.IntersectionObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
}
