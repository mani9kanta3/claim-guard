import { useEffect, useState } from 'react'

import Loading from '../../components/Loading.jsx'
import PageHeader from '../../components/PageHeader.jsx'
import { createHospital } from '../../api/admin.js'
import { getHospitals } from '../../api/claims.js'
import { getErrorMessage } from '../../api/client.js'

const EMPTY_FORM = { name: '', city: '', is_network: true }

function Hospitals() {
  const [hospitals, setHospitals] = useState([])
  const [form, setForm] = useState(EMPTY_FORM)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  async function loadHospitals() {
    try {
      setHospitals(await getHospitals())
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHospitals()
  }, [])

  function handleChange(event) {
    const { name, value, type, checked } = event.target
    setForm({ ...form, [name]: type === 'checkbox' ? checked : value })
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setSaving(true)

    try {
      const hospital = await createHospital(form)
      setMessage(`${hospital.name} added.`)
      setForm(EMPTY_FORM)
      loadHospitals()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const networkCount = hospitals.filter((hospital) => hospital.is_network).length

  return (
    <div>
      <PageHeader
        title="Hospitals"
        subtitle={`${hospitals.length} hospitals, ${networkCount} in the network. Claims at non-network hospitals carry more risk.`}
      />

      <div className="row g-4">
        <div className="col-xl-4">
          <div className="card">
            <div className="card-header">
              <i className="bi bi-plus-circle me-2"></i>Add hospital
            </div>
            <div className="card-body">
              {error && <div className="alert alert-danger py-2 small">{error}</div>}
              {message && <div className="alert alert-success py-2 small">{message}</div>}

              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label className="form-label fw-medium">Name</label>
                  <input name="name" className="form-control" value={form.name} onChange={handleChange} required />
                </div>

                <div className="mb-3">
                  <label className="form-label fw-medium">City</label>
                  <input name="city" className="form-control" value={form.city} onChange={handleChange} required />
                </div>

                <div className="form-check form-switch mb-4">
                  <input
                    type="checkbox"
                    id="is_network"
                    name="is_network"
                    className="form-check-input"
                    checked={form.is_network}
                    onChange={handleChange}
                  />
                  <label className="form-check-label" htmlFor="is_network">
                    Network hospital
                  </label>
                </div>

                <button type="submit" className="btn btn-primary w-100" disabled={saving}>
                  {saving ? 'Adding...' : 'Add hospital'}
                </button>
              </form>
            </div>
          </div>
        </div>

        <div className="col-xl-8">
          <div className="card table-card">
            {loading ? (
              <div className="px-4"><Loading text="Loading hospitals..." /></div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>City</th>
                    <th>Network</th>
                  </tr>
                </thead>
                <tbody>
                  {hospitals.map((hospital) => (
                    <tr key={hospital.id}>
                      <td className="fw-semibold">{hospital.name}</td>
                      <td className="text-muted">{hospital.city}</td>
                      <td>
                        <span className={`soft-badge ${hospital.is_network ? 'tone-green' : 'tone-amber'}`}>
                          <span className="dot"></span>
                          {hospital.is_network ? 'In network' : 'Outside network'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Hospitals
