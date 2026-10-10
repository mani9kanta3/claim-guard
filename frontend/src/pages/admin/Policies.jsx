import { useEffect, useState } from 'react'

import Loading from '../../components/Loading.jsx'
import PageHeader from '../../components/PageHeader.jsx'
import { createPolicy, getAllPolicies, getCustomers } from '../../api/admin.js'
import { getErrorMessage } from '../../api/client.js'
import { formatDate, formatMoney } from '../../utils/format.js'

const PLAN_SUM_INSURED = { Silver: 300000, Gold: 500000, Platinum: 1000000 }

const EMPTY_FORM = {
  user_id: '',
  plan_name: 'Silver',
  sum_insured: PLAN_SUM_INSURED.Silver,
  start_date: '',
  end_date: '',
  waiting_period_days: 30,
}

function Policies() {
  const [policies, setPolicies] = useState([])
  const [customers, setCustomers] = useState([])
  const [form, setForm] = useState(EMPTY_FORM)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  async function loadPolicies() {
    try {
      setPolicies(await getAllPolicies())
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPolicies()
    getCustomers()
      .then(setCustomers)
      .catch((err) => setError(getErrorMessage(err)))
  }, [])

  function handleChange(event) {
    const { name, value } = event.target
    if (name === 'plan_name') {
      setForm({ ...form, plan_name: value, sum_insured: PLAN_SUM_INSURED[value] })
    } else {
      setForm({ ...form, [name]: value })
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setMessage('')

    if (form.end_date <= form.start_date) {
      setError('End date must be after start date.')
      return
    }

    setSaving(true)
    try {
      const policy = await createPolicy(form)
      setMessage(`Policy ${policy.policy_number} created for ${policy.holder_name}.`)
      setForm(EMPTY_FORM)
      loadPolicies()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <PageHeader title="Policies" subtitle="Create health policies for customers and track their remaining cover" />

      <div className="row g-4">
        <div className="col-xl-4">
          <div className="card">
            <div className="card-header">
              <i className="bi bi-plus-circle me-2"></i>New policy
            </div>
            <div className="card-body">
              {error && <div className="alert alert-danger py-2 small">{error}</div>}
              {message && <div className="alert alert-success py-2 small">{message}</div>}

              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label className="form-label fw-medium">Customer</label>
                  <select name="user_id" className="form-select" value={form.user_id} onChange={handleChange} required>
                    <option value="">Select customer</option>
                    {customers.map((customer) => (
                      <option key={customer.id} value={customer.id}>
                        {customer.full_name} ({customer.email})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="row g-2 mb-3">
                  <div className="col-6">
                    <label className="form-label fw-medium">Plan</label>
                    <select name="plan_name" className="form-select" value={form.plan_name} onChange={handleChange}>
                      {Object.keys(PLAN_SUM_INSURED).map((plan) => (
                        <option key={plan}>{plan}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-6">
                    <label className="form-label fw-medium">Sum insured (₹)</label>
                    <input type="number" name="sum_insured" min="1" className="form-control" value={form.sum_insured} onChange={handleChange} required />
                  </div>
                </div>

                <div className="row g-2 mb-3">
                  <div className="col-6">
                    <label className="form-label fw-medium">Start date</label>
                    <input type="date" name="start_date" className="form-control" value={form.start_date} onChange={handleChange} required />
                  </div>
                  <div className="col-6">
                    <label className="form-label fw-medium">End date</label>
                    <input type="date" name="end_date" className="form-control" value={form.end_date} onChange={handleChange} required />
                  </div>
                </div>

                <div className="mb-4">
                  <label className="form-label fw-medium">Waiting period (days)</label>
                  <input type="number" name="waiting_period_days" min="0" max="365" className="form-control" value={form.waiting_period_days} onChange={handleChange} />
                </div>

                <button type="submit" className="btn btn-primary w-100" disabled={saving}>
                  {saving ? 'Creating...' : 'Create policy'}
                </button>
              </form>
            </div>
          </div>
        </div>

        <div className="col-xl-8">
          <div className="card table-card">
            {loading ? (
              <div className="px-4"><Loading text="Loading policies..." /></div>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Policy No</th>
                    <th>Holder</th>
                    <th>Plan</th>
                    <th className="text-end">Remaining / Sum insured</th>
                    <th>Valid till</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {policies.map((policy) => (
                    <tr key={policy.id}>
                      <td className="fw-semibold">{policy.policy_number}</td>
                      <td>{policy.holder_name}</td>
                      <td>{policy.plan_name}</td>
                      <td className="text-end">
                        {formatMoney(policy.remaining_sum_insured)}
                        <span className="text-muted"> / {formatMoney(policy.sum_insured)}</span>
                      </td>
                      <td className="text-muted">{formatDate(policy.end_date)}</td>
                      <td>
                        <span className={`soft-badge ${policy.status === 'ACTIVE' ? 'tone-green' : 'tone-gray'}`}>
                          <span className="dot"></span>
                          {policy.status}
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

export default Policies
