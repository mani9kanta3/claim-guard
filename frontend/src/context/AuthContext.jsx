import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

function getSavedUser() {
  const saved = localStorage.getItem('user')
  return saved ? JSON.parse(saved) : null
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getSavedUser)

  function login(token, userData) {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(userData))
    setUser(userData)
  }

  function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
