import client from './client.js'

export async function loginUser(email, password) {
  const response = await client.post('/api/auth/login', { email, password })
  return response.data
}

export async function registerUser(fullName, email, password) {
  const response = await client.post('/api/auth/register', {
    full_name: fullName,
    email,
    password,
  })
  return response.data
}

export async function getCurrentUser() {
  const response = await client.get('/api/auth/me')
  return response.data
}
