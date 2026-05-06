import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Outlet } from 'react-router-dom'

vi.mock('../components/Layout/MainLayout', () => ({
  default: () => <Outlet />,
}))

vi.mock('../pages/auth/Login', () => ({
  default: () => <div data-testid="login-page">login</div>,
}))

vi.mock('../pages/auth/Register', () => ({
  default: () => <div data-testid="register-page">register</div>,
}))

vi.mock('../pages/auth/Profile', () => ({
  default: () => <div data-testid="profile-page">profile</div>,
}))

vi.mock('../pages/admin/Users', () => ({
  default: () => <div data-testid="admin-users-page">admin users</div>,
}))

import App from '../App'

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>
  )
}

describe('App auth routes', () => {
  it('renders the login route', async () => {
    renderAt('/login')

    expect(await screen.findByTestId('login-page')).toBeInTheDocument()
  })

  it('renders the register route', async () => {
    renderAt('/register')

    expect(await screen.findByTestId('register-page')).toBeInTheDocument()
  })

  it('redirects unauthenticated profile access to login', async () => {
    renderAt('/profile')

    expect(await screen.findByTestId('login-page')).toBeInTheDocument()
  })
})
