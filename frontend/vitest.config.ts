import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'happy-dom',
      globals: true,
      include: ['src/**/*.{test,spec}.{ts,tsx,js,jsx}'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html', 'json-summary'],
        include: ['src/**/*.{ts,tsx,vue}'],
        exclude: ['node_modules', 'dist', 'coverage'],
      },
    },
  }),
)
