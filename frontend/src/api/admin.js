import client from './client.js'

export async function getDashboardSummary() {
  const response = await client.get('/api/dashboard/summary')
  return response.data
}

export async function getAllPolicies() {
  const response = await client.get('/api/policies')
  return response.data
}

export async function createPolicy(policyData) {
  const response = await client.post('/api/policies', policyData)
  return response.data
}

export async function createHospital(hospitalData) {
  const response = await client.post('/api/hospitals', hospitalData)
  return response.data
}

export async function getCustomers() {
  const response = await client.get('/api/users', { params: { role: 'CUSTOMER' } })
  return response.data
}
