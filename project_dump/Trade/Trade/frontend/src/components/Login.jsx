import React, { useState } from 'react'
import { useAuth } from '../AuthContext'
import './Auth.css'

export default function Login({ onNavigate }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    if (!email || !password) {
      setError('Email and password are required')
      setLoading(false)
      return
    }

    try {
      await login(email, password)
      onNavigate('dashboard')
    } catch (err) {
      setError(err.message || 'Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-icon">⚡</div>
        <h1>Welcome back</h1>
        <p className="auth-subtitle">Enter your credentials to access the terminal</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              placeholder="quant@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="form-input"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label>
              Password
              <a href="#" className="forgot-link" onClick={(e) => e.preventDefault()}>
                Forgot password?
              </a>
            </label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="form-input"
              disabled={loading}
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? 'Logging in...' : 'Log In'}
          </button>
        </form>

        <p className="auth-link">
          Don't have an account?{' '}
          <button className="link-btn" onClick={() => onNavigate('signup')} disabled={loading}>
            Sign up
          </button>
        </p>
      </div>
    </div>
  )
}
