/**
 * 冒烟测试 / Smoke tests
 *
 * 验证：
 * - 测试基础设施跑得起来（jsdom + vitest + testing-library）
 * - 一个简单组件能渲染
 *
 * 业务测试请放到 src/__tests__/<feature>.test.tsx，按 feature 拆分。
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

describe('smoke', () => {
  it('test infra works (jsdom + vitest + testing-library)', () => {
    expect(1 + 1).toBe(2)
    expect(typeof window).toBe('object')
    expect(typeof document).toBe('object')
  })

  it('can render a simple JSX element', () => {
    render(<div data-testid="hello">hello world</div>)
    const el = screen.getByTestId('hello')
    expect(el).toBeInTheDocument()
    expect(el).toHaveTextContent('hello world')
  })

  it('matchMedia polyfill is in place', () => {
    expect(window.matchMedia).toBeTypeOf('function')
    const result = window.matchMedia('(min-width: 768px)')
    expect(result.matches).toBe(false)
  })
})
