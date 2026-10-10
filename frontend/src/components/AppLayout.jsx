import { useState } from 'react'
import { Link, Navigate, NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext.jsx'

const MENU = {
  CUSTOMER: [
    { to: '/customer/claims', label: 'My Claims', icon: 'bi-file-earmark-medical' },
    { to: '/customer/claims/new', label: 'New Claim', icon: 'bi-plus-circle' },
    { to: '/customer/policies', label: 'My Policies', icon: 'bi-shield-check' },
  ],
  OFFICER: [
    { to: '/officer/queue', label: 'Review Queue', icon: 'bi-inboxes' },
    { to: '/officer/dashboard', label: 'Dashboard', icon: 'bi-bar-chart-line' },
  ],
  ADMIN: [
    { to: '/admin/dashboard', label: 'Dashboard', icon: 'bi-bar-chart-line' },
    { to: '/admin/policies', label: 'Policies', icon: 'bi-shield-check' },
    { to: '/admin/hospitals', label: 'Hospitals', icon: 'bi-hospital' },
  ],
}

const ROLE_LABEL = {
  CUSTOMER: 'Policyholder',
  OFFICER: 'Claims Officer',
  ADMIN: 'Administrator',
}

function initials(name) {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  if (!user) {
    return <Navigate to="/login" replace />
  }

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
        <Link to="/" className="sidebar-brand" onClick={() => setMenuOpen(false)}>
          <span className="brand-icon">
            <i className="bi bi-shield-fill-check"></i>
          </span>
          ClaimGuard
        </Link>

        <div className="sidebar-section">Menu</div>
        <nav>
          {MENU[user.role].map((item) => (
            <NavLink key={item.to} to={item.to} end className="sidebar-link" onClick={() => setMenuOpen(false)}>
              <i className={`bi ${item.icon}`}></i>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-user">
          <div className="d-flex align-items-center gap-2 mb-3">
            <div className="avatar">{initials(user.full_name)}</div>
            <div className="small">
              <div className="fw-semibold">{user.full_name}</div>
              <div className="text-secondary">{ROLE_LABEL[user.role]}</div>
            </div>
          </div>
          <button className="btn btn-sm btn-outline-light w-100" onClick={handleLogout}>
            <i className="bi bi-box-arrow-right me-2"></i>
            Logout
          </button>
        </div>
      </aside>

      <div className="main-area">
        <div className="mobile-bar">
          <span className="fw-bold">
            <i className="bi bi-shield-fill-check me-2"></i>
            ClaimGuard
          </span>
          <button className="btn btn-sm btn-outline-light" onClick={() => setMenuOpen(!menuOpen)}>
            <i className="bi bi-list"></i>
          </button>
        </div>

        <main className="page">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default AppLayout
