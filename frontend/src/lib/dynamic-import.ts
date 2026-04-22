/**
 * Dynamic import utilities for code splitting
 */
import dynamic from 'next/dynamic'

/**
 * Create a dynamically imported component with loading fallback
 *
 * @param importFn - The dynamic import function
 * @param options - Loading options
 */
export function createDynamicComponent<T = unknown>(
  importFn: () => Promise<{ default: React.ComponentType<T> }>,
  options: {
    loading?: () => React.ReactNode
    ssr?: boolean
  } = {}
) {
  return dynamic(importFn, {
    loading: options.loading || (() => (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )),
    ssr: options.ssr ?? true,
  })
}

/**
 * Preload a dynamic import
 */
export function preloadComponent(
  importFn: () => Promise<unknown>
): void {
  // Trigger the import to be cached by Next.js
  importFn()
}
