import client from './client.js'

export async function getClaims(filters = {}) {
  const response = await client.get('/api/claims', { params: filters })
  return response.data
}

export async function getClaim(id) {
  const response = await client.get(`/api/claims/${id}`)
  return response.data
}

export async function submitClaim(formData) {
  const response = await client.post('/api/claims', formData)
  return response.data
}

export async function changeClaimStatus(id, toStatus, note, approvedAmount) {
  const response = await client.post(`/api/claims/${id}/transition`, {
    to_status: toStatus,
    note: note || null,
    approved_amount: approvedAmount || null,
  })
  return response.data
}

export async function settleClaim(id) {
  const response = await client.post(`/api/claims/${id}/settle`)
  return response.data
}

export async function rescoreClaim(id) {
  const response = await client.post(`/api/claims/${id}/rescore`)
  return response.data
}

export async function openClaimDocument(id) {
  const response = await client.get(`/api/claims/${id}/document`, { responseType: 'blob' })
  const url = URL.createObjectURL(response.data)
  window.open(url, '_blank')
}

export async function getMyPolicies() {
  const response = await client.get('/api/policies')
  return response.data
}

export async function getHospitals() {
  const response = await client.get('/api/hospitals')
  return response.data
}
