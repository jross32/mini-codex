import React, { useState } from 'react'
import { useAuth } from '../AuthContext'
import './Auth.css'

export default function SignUp({ onNavigate }) {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { signup } = useAuth()

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!fullName || !email || !password) {
      setError('All fields are required')
      return
    }
    try {
      signup(fullName, email, password)
      onNavigate('dashboard')
    } catch (err) {
      setError('Sign up failed')
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-icon">⚡</div>
        <h1>Create an account</h1>
        <p className="auth-subtitle">Start your paper trading journey today</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Full Name</label>
            <input
              type="text"
              placeholder="John Doe"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              placeholder="quant@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="form-input"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="btn-submit">
            Sign Up
          </button>
        </form>

        <p className="auth-link">
          Already have an account?{' '}
          <button className="link-btn" onClick={() => onNavigate('login')}>
            Log in
          </button>
        </p>
      </div>
    </div>
  )
}
