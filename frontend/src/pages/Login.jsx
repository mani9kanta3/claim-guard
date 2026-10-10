import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import AuthLayout from '../components/AuthLayout.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { loginUser } from '../api/auth.js'
import { getErrorMessage } from '../api/client.js'

const DEMO_ACCOUNTS = [
  { email: 'customer@demo.com', role: 'Policyholder', icon: 'bi-person' },
  { email: 'officer@demo.com', role: 'Claims Officer', icon: 'bi-person-badge' },
  { email: 'admin@demo.com', role: 'Administrator', icon: 'bi-gear' },
]
const DEMO_PASSWORD = 'password123'

function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user) {
    return <Navigate to="/" replace />
  }

  async function signIn(emailValue, passwordValue) {
    setError('')
    setLoading(true)
    try {
      const data = await loginUser(emailValue, passwordValue)
      login(data.access_token, data.user)
      navigate('/')
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    signIn(email, password)
  }

  function signInAsDemo(demoEmail) {
    setEmail(demoEmail)
    setPassword(DEMO_PASSWORD)
    signIn(demoEmail, DEMO_PASSWORD)
  }

  return (
    <AuthLayout>
      <h2 className="fw-bold mb-1">Welcome back</h2>
      <p className="text-muted mb-4">Sign in to continue to ClaimGuard</p>

      {error && (
        <div className="alert alert-danger d-flex gap-2 align-items-center">
          <i className="bi bi-exclamation-circle"></i>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="form-label fw-medium">Email</label>
          <input
            type="email"
            className="form-control form-control-lg"
            placeholder="you@example.com"
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
            placeholder="Your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button type="submit" className="btn btn-primary btn-lg w-100" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>

      <p className="text-center mt-3 mb-4">
        New policyholder? <Link to="/register">Create an account</Link>
      </p>

      <div className="text-muted small text-uppercase fw-semibold mb-2">Try a demo account</div>
      <div className="d-grid gap-2">
        {DEMO_ACCOUNTS.map((account) => (
          <button
            key={account.email}
            type="button"
            className="demo-chip d-flex align-items-center gap-3"
            disabled={loading}
            onClick={() => signInAsDemo(account.email)}
          >
            <i className={`bi ${account.icon} fs-5 text-primary`}></i>
            <span>
              <span className="fw-semibold d-block">{account.role}</span>
              <span className="small text-muted">{account.email}</span>
            </span>
            <i className="bi bi-arrow-right ms-auto text-muted"></i>
          </button>
        ))}
      </div>
    </AuthLayout>
  )
}

export default Login
