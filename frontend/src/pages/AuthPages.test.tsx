import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '@/app/context/AuthContext'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import { useAuth } from '@/app/context/AuthContext'

// Mock the API module
vi.mock('@/lib/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

import api from '@/lib/api'

const renderWithProviders = (component: React.ReactNode) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {component}
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders login form', () => {
    renderWithProviders(<LoginPage />)
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows error when email is empty', async () => {
    renderWithProviders(<LoginPage />)
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()
    })
  })

  it('shows error when password is empty', async () => {
    renderWithProviders(<LoginPage />)
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => {
      expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    })
  })

  it('calls API on valid submit', async () => {
    api.post.mockResolvedValueOnce({
      data: {
        token: 'test-token',
        user_id: '123',
        email: 'test@test.com',
        name: 'Test User',
        role: 'applicant',
        email_verified: true,
      },
    })

    renderWithProviders(<LoginPage />)
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/auth/login', {
        email: 'test@test.com',
        password: 'password123',
      })
    })
  })

  it('navigates to register page on link click', () => {
    renderWithProviders(<LoginPage />)
    fireEvent.click(screen.getByText(/create an account/i))
    expect(screen.getByText(/register/i)).toBeInTheDocument()
  })
})

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders registration form', () => {
    renderWithProviders(<RegisterPage />)
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('shows password strength indicator', () => {
    renderWithProviders(<RegisterPage />)
    const passwordInput = screen.getByLabelText(/password/i)
    fireEvent.change(passwordInput, { target: { value: 'weak' } })
    expect(screen.getByText(/weak/i)).toBeInTheDocument()
  })

  it('toggles between applicant and recruiter role', () => {
    renderWithProviders(<RegisterPage />)
    expect(screen.getByText(/applicant/i)).toBeInTheDocument()
    expect(screen.getByText(/recruiter/i)).toBeInTheDocument()
  })

  it('calls API on valid submit', async () => {
    api.post.mockResolvedValueOnce({
      data: {
        token: 'test-token',
        user_id: '123',
        email: 'new@test.com',
        name: 'New User',
        role: 'applicant',
        email_verified: false,
      },
    })

    renderWithProviders(<RegisterPage />)
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'New User' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'new@test.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/auth/register', {
        name: 'New User',
        email: 'new@test.com',
        password: 'password123',
        role: 'applicant',
      })
    })
  })
})

describe('AuthContext', () => {
  it('provides login function', () => {
    let authValue: any
    const TestComponent = () => {
      authValue = useAuth()
      return null
    }

    renderWithProviders(<TestComponent />)
    expect(authValue.login).toBeDefined()
    expect(authValue.register).toBeDefined()
    expect(authValue.logout).toBeDefined()
    expect(authValue.isAuthenticated).toBe(false)
  })
})