import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import AuthLayout from '../components/AuthLayout.jsx'
import { loginUser, registerUser } from '../api/auth.js'
import { getErrorMessage } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'

function Register() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    setLoading(true)
    try {
      await registerUser(fullName, email, password)
      const data = await loginUser(email, password)
      login(data.access_token, data.user)
      navigate('/')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout>
      <h2 className="fw-bold mb-1">Create your account</h2>
      <p className="text-muted mb-4">For policyholders. Officers are added by an administrator.</p>

      {error && (
        <div className="alert alert-danger d-flex gap-2 align-items-center">
          <i className="bi bi-exclamation-circle"></i>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="form-label fw-medium">Full name</label>
          <input
            type="text"
            className="form-control form-control-lg"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
        </div>

        <div className="mb-3">
          <label className="form-label fw-medium">Email</label>
          <input
            type="email"
            className="form-control form-control-lg"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="mb-4">
          <label className="form-label fw-medium">Password</label>
          <input
            type="password"
            className="form-control form-control-lg"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <div className="form-text">At least 8 characters.</div>
        </div>

        <button type="submit" className="btn btn-primary btn-lg w-100" disabled={loading}>
          {loading ? 'Creating account...' : 'Create account'}
        </button>
      </form>

      <p className="text-center mt-3 mb-0">
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </AuthLayout>
  )
}

export default Register
