import React, { createContext, useState, useEffect } from 'react'

export const AuthContext = createContext()

const API_URL = 'http://localhost:8000/api'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if token is saved in localStorage
    const savedToken = localStorage.getItem('quantai_token')
    if (savedToken) {
      setToken(savedToken)
      // Verify token is still valid
      verifyTokenValidity(savedToken)
    }
    setLoading(false)
  }, [])

  const verifyTokenValidity = async (tkn) => {
    try {
      const res = await fetch(`${API_URL}/auth/me?token=${tkn}`)
      if (res.ok) {
        const userData = await res.json()
        setUser(userData)
      } else {
        localStorage.removeItem('quantai_token')
        setToken(null)
      }
    } catch (err) {
      console.error('Token verification failed:', err)
    }
  }

  const signup = async (fullName, email, password) => {
    try {
      const res = await fetch(`${API_URL}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: fullName, email, password })
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Sign up failed')
      }
      const data = await res.json()
      localStorage.setItem('quantai_token', data.access_token)
      setToken(data.access_token)
      setUser(data.user)
      return true
    } catch (err) {
      console.error('Signup error:', err)
      throw err
    }
  }

  const login = async (email, password) => {
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Login failed')
      }
      const data = await res.json()
      localStorage.setItem('quantai_token', data.access_token)
      setToken(data.access_token)
      setUser(data.user)
      return true
    } catch (err) {
      console.error('Login error:', err)
      throw err
    }
  }

  const logout = () => {
    localStorage.removeItem('quantai_token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, signup, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = React.useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
