import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import PageHeader from '../../components/PageHeader.jsx'
import StatusBadge from '../../components/StatusBadge.jsx'
import { getHospitals, getMyPolicies, submitClaim } from '../../api/claims.js'
import { getErrorMessage } from '../../api/client.js'
import { DIAGNOSIS_CATEGORIES, MAX_FILE_SIZE } from '../../constants.js'
import { formatMoney } from '../../utils/format.js'

const EMPTY_FORM = {
  policy_id: '',
  hospital_id: '',
  admission_date: '',
  discharge_date: '',
  diagnosis_category: '',
  claimed_amount: '',
}

const NEXT_STEPS = [
  ['bi-file-earmark-text', 'We read your bill', 'The amounts and dates on the PDF are read automatically.'],
  ['bi-shield-check', 'Automatic checks', 'Your claim is checked against your policy terms.'],
  ['bi-person-check', 'Officer review', 'A claims officer approves the amount.'],
  ['bi-bank', 'Payment', 'The approved amount is settled to you.'],
]

function NewClaim() {
  const fileInput = useRef(null)
  const [policies, setPolicies] = useState([])
  const [hospitals, setHospitals] = useState([])
  const [form, setForm] = useState(EMPTY_FORM)
  const [billFile, setBillFile] = useState(null)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    async function loadOptions() {
      try {
        const [policyList, hospitalList] = await Promise.all([getMyPolicies(), getHospitals()])
        setPolicies(policyList.filter((policy) => policy.status === 'ACTIVE'))
        setHospitals(hospitalList)
      } catch (err) {
        setError(getErrorMessage(err))
      }
    }
    loadOptions()
  }, [])

  const selectedPolicy = policies.find((policy) => String(policy.id) === form.policy_id)
  const today = new Date().toISOString().slice(0, 10)

  function handleChange(event) {
    setForm({ ...form, [event.target.name]: event.target.value })
  }

  function handleFileChange(event) {
    const file = event.target.files[0]
    setError('')

    if (!file) {
      setBillFile(null)
      return
    }
    if (file.type !== 'application/pdf') {
      setError('Only PDF files are allowed.')
      event.target.value = ''
      return
    }
    if (file.size > MAX_FILE_SIZE) {
      setError('File is too large. Maximum size is 2 MB.')
      event.target.value = ''
      return
    }
    setBillFile(file)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    if (form.discharge_date < form.admission_date) {
      setError('Discharge date cannot be before admission date.')
      return
    }
    if (!billFile) {
      setError('Please upload the hospital bill (PDF).')
      return
    }

    const formData = new FormData()
    Object.keys(form).forEach((key) => formData.append(key, form[key]))
    formData.append('bill', billFile)

    setLoading(true)
    try {
      setResult(await submitClaim(formData))
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  function startAnother() {
    setResult(null)
    setForm(EMPTY_FORM)
    setBillFile(null)
  }

  if (result) {
    const rejected = result.status === 'REJECTED'
    const lastNote = result.events[result.events.length - 1]?.note

    return (
      <div className="row justify-content-center">
        <div className="col-lg-7">
          <div className="card text-center">
            <div className="card-body p-5">
              <div className={`stat-icon mx-auto mb-3 ${rejected ? 'tone-red' : 'tone-green'}`}>
                <i className={`bi ${rejected ? 'bi-x-lg' : 'bi-check-lg'}`}></i>
              </div>
              <h3 className="fw-bold">{rejected ? 'Claim could not be accepted' : 'Claim submitted'}</h3>
              <p className="text-muted">
                Your claim number is <strong>{result.claim_number}</strong>
              </p>
              <div className="mb-3">
                <StatusBadge status={result.status} />
              </div>
              {rejected && lastNote && <div className="alert alert-danger">{lastNote}</div>}
              {!rejected && (
                <p className="text-muted small">
                  We read your bill and ran our automatic checks. A claims officer will review it next.
                </p>
              )}
              <div className="d-flex justify-content-center gap-2 mt-4">
                <Link to={`/customer/claims/${result.id}`} className="btn btn-primary">
                  Track this claim
                </Link>
                <button className="btn btn-outline-secondary" onClick={startAnother}>
                  Submit another
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader title="Submit a Claim" subtitle="Reimbursement claim for a hospital stay you have already paid for" />

      <div className="row g-4">
        <div className="col-lg-8">
          <div className="card">
            <div className="card-body p-4">
              {error && <div className="alert alert-danger">{error}</div>}

              <form onSubmit={handleSubmit}>
                <div className="row g-3">
                  <div className="col-md-6">
                    <label className="form-label fw-medium">Policy</label>
                    <select name="policy_id" className="form-select" value={form.policy_id} onChange={handleChange} required>
                      <option value="">Select policy</option>
                      {policies.map((policy) => (
                        <option key={policy.id} value={policy.id}>
                          {policy.policy_number} ({policy.plan_name})
                        </option>
                      ))}
                    </select>
                    {selectedPolicy && (
                      <div className="form-text">
                        Remaining cover: {formatMoney(selectedPolicy.remaining_sum_insured)}
                      </div>
                    )}
                  </div>

                  <div className="col-md-6">
                    <label className="form-label fw-medium">Hospital</label>
                    <select name="hospital_id" className="form-select" value={form.hospital_id} onChange={handleChange} required>
                      <option value="">Select hospital</option>
                      {hospitals.map((hospital) => (
                        <option key={hospital.id} value={hospital.id}>
                          {hospital.name}, {hospital.city}
                          {hospital.is_network ? '' : ' (non-network)'}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="col-md-6">
                    <label className="form-label fw-medium">Admission date</label>
                    <input
                      type="date"
                      name="admission_date"
                      max={today}
                      className="form-control"
                      value={form.admission_date}
                      onChange={handleChange}
                      required
                    />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label fw-medium">Discharge date</label>
                    <input
                      type="date"
                      name="discharge_date"
                      max={today}
                      className="form-control"
                      value={form.discharge_date}
                      onChange={handleChange}
                      required
                    />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label fw-medium">Treatment category</label>
                    <select
                      name="diagnosis_category"
                      className="form-select"
                      value={form.diagnosis_category}
                      onChange={handleChange}
                      required
                    >
                      <option value="">Select category</option>
                      {DIAGNOSIS_CATEGORIES.map((category) => (
                        <option key={category} value={category}>
                          {category.replace('_', ' ')}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="col-md-6">
                    <label className="form-label fw-medium">Claimed amount (₹)</label>
                    <input
                      type="number"
                      name="claimed_amount"
                      className="form-control"
                      min="1"
                      step="0.01"
                      value={form.claimed_amount}
                      onChange={handleChange}
                      required
                    />
                  </div>

                  <div className="col-12">
                    <label className="form-label fw-medium">Hospital bill</label>
                    <div className="upload-box" onClick={() => fileInput.current.click()}>
                      <i className="bi bi-cloud-arrow-up fs-2 text-primary"></i>
                      {billFile ? (
                        <div className="fw-semibold mt-2">{billFile.name}</div>
                      ) : (
                        <div className="mt-2">Click to choose the PDF bill</div>
                      )}
                      <div className="small text-muted">PDF only, up to 2 MB</div>
                    </div>
                    <input ref={fileInput} type="file" accept=".pdf" className="d-none" onChange={handleFileChange} />
                  </div>
                </div>

                <button type="submit" className="btn btn-primary btn-lg mt-4 w-100" disabled={loading}>
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2"></span>
                      Reading your bill and checking the claim...
                    </>
                  ) : (
                    'Submit claim'
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>

        <div className="col-lg-4">
          <div className="card">
            <div className="card-header">What happens next</div>
            <div className="card-body">
              {NEXT_STEPS.map(([icon, title, text]) => (
                <div className="d-flex gap-3 mb-3" key={title}>
                  <div className="stat-icon tone-indigo" style={{ width: 38, height: 38, fontSize: '1rem' }}>
                    <i className={`bi ${icon}`}></i>
                  </div>
                  <div>
                    <div className="fw-semibold">{title}</div>
                    <div className="small text-muted">{text}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NewClaim
