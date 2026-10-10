import { Navigate, Route, Routes } from 'react-router-dom'

import AppLayout from './components/AppLayout.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import { useAuth } from './context/AuthContext.jsx'

import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'

import MyPolicies from './pages/customer/MyPolicies.jsx'
import NewClaim from './pages/customer/NewClaim.jsx'
import MyClaims from './pages/customer/MyClaims.jsx'
import ClaimStatus from './pages/customer/ClaimStatus.jsx'

import ReviewQueue from './pages/officer/ReviewQueue.jsx'
import ClaimReview from './pages/officer/ClaimReview.jsx'

import Dashboard from './pages/admin/Dashboard.jsx'
import Policies from './pages/admin/Policies.jsx'
import Hospitals from './pages/admin/Hospitals.jsx'

const HOME_PAGE = {
  CUSTOMER: '/customer/claims',
  OFFICER: '/officer/queue',
  ADMIN: '/admin/dashboard',
}

function HomeRedirect() {
  const { user } = useAuth()

  if (!user) {
    return <Navigate to="/login" replace />
  }
  return <Navigate to={HOME_PAGE[user.role]} replace />
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route element={<AppLayout />}>
        <Route element={<ProtectedRoute allowedRoles={['CUSTOMER']} />}>
          <Route path="/customer/policies" element={<MyPolicies />} />
          <Route path="/customer/claims" element={<MyClaims />} />
          <Route path="/customer/claims/new" element={<NewClaim />} />
          <Route path="/customer/claims/:id" element={<ClaimStatus />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={['OFFICER']} />}>
          <Route path="/officer/queue" element={<ReviewQueue />} />
          <Route path="/officer/claims/:id" element={<ClaimReview />} />
          <Route path="/officer/dashboard" element={<Dashboard />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={['ADMIN']} />}>
          <Route path="/admin/dashboard" element={<Dashboard />} />
          <Route path="/admin/policies" element={<Policies />} />
          <Route path="/admin/hospitals" element={<Hospitals />} />
        </Route>
      </Route>

      <Route path="*" element={<HomeRedirect />} />
    </Routes>
  )
}

export default App
