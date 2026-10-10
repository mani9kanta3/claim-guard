import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import ClaimTimeline from '../../components/ClaimTimeline.jsx'
import FlagList from '../../components/FlagList.jsx'
import Loading from '../../components/Loading.jsx'
import RiskBadge from '../../components/RiskBadge.jsx'
import StatusBadge from '../../components/StatusBadge.jsx'
import { changeClaimStatus, getClaim, openClaimDocument, rescoreClaim, settleClaim } from '../../api/claims.js'
import { getErrorMessage } from '../../api/client.js'
import { formatDate, formatMoney, formatPercent } from '../../utils/format.js'

const RISK_COLOR = { LOW: '#059669', MEDIUM: '#d97706', HIGH: '#dc2626' }

function MatchIcon({ match }) {
  if (match === null) {
    return <span className="text-muted">-</span>
  }
  return match ? (
    <i className="bi bi-check-circle-fill text-success"></i>
  ) : (
    <i className="bi bi-x-circle-fill text-danger"></i>
  )
}

function showValue(field, value) {
  return field.includes('date') ? formatDate(value) : value
}

function BillComparison({ bill, onViewBill }) {
  if (!bill) {
    return <p className="text-muted mb-0">No bill was uploaded with this claim.</p>
  }

  if (bill.extraction_status !== 'DONE') {
    return (
      <div className="alert alert-warning mb-0 d-flex gap-2">
        <i className="bi bi-exclamation-triangle"></i>
        <div>
          <strong>Bill could not be read automatically, verify manually.</strong>
          {bill.error && <div className="small">{bill.error}</div>}
          <button className="btn btn-link btn-sm p-0" onClick={onViewBill}>Open the bill</button>
        </div>
      </div>
    )
  }

  return (
    <>
      <table className="table mb-2">
        <thead>
          <tr>
            <th>Field</th>
            <th>Entered by customer</th>
            <th>Read from bill</th>
            <th className="text-center">Match</th>
          </tr>
        </thead>
        <tbody>
          {bill.comparison.map((row) => (
            <tr key={row.field} className={row.match === false ? 'table-danger' : ''}>
              <td className="text-muted">{row.field}</td>
              <td>{showValue(row.field, row.entered)}</td>
              <td>{row.extracted ? showValue(row.field, row.extracted) : <span className="text-muted">not found</span>}</td>
              <td className="text-center"><MatchIcon match={row.match} /></td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="small text-muted">
        Read by: {bill.extracted.provider} · Diagnosis on bill: {bill.extracted.diagnosis || '-'}
      </div>
    </>
  )
}

function ClaimReview() {
  const { id } = useParams()
  const [claim, setClaim] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  const [note, setNote] = useState('')
  const [approvedAmount, setApprovedAmount] = useState('')
  const [actionError, setActionError] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    async function loadClaim() {
      try {
        const data = await getClaim(id)
        setClaim(data)
        setApprovedAmount(String(data.claimed_amount))
      } catch (err) {
        setLoadError(getErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }
    loadClaim()
  }, [id])

  async function runAction(action, successText) {
    setActionError('')
    setMessage('')
    setSaving(true)
    try {
      const updated = await action()
      setClaim(updated)
      setNote('')
      setMessage(successText)
    } catch (err) {
      setActionError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  function decide(toStatus) {
    if (toStatus === 'APPROVED' && !approvedAmount) {
      setActionError('Enter the approved amount.')
      return
    }
    if (toStatus !== 'APPROVED' && !note.trim()) {
      setActionError('Please write a note or reason for this action.')
      return
    }
    const amount = toStatus === 'APPROVED' ? approvedAmount : null
    runAction(() => changeClaimStatus(claim.id, toStatus, note, amount), `Claim moved to ${toStatus.replace('_', ' ')}.`)
  }

  function settle() {
    runAction(() => settleClaim(claim.id), 'Claim settled. The amount was deducted from the policy cover.')
  }

  function rescore() {
    runAction(() => rescoreClaim(claim.id), 'Bill re-read and risk recalculated.')
  }

  async function viewBill() {
    try {
      await openClaimDocument(claim.id)
    } catch (err) {
      setActionError(getErrorMessage(err))
    }
  }

  if (loading) {
    return <Loading text="Loading claim..." />
  }

  if (loadError) {
    return (
      <div>
        <div className="alert alert-danger">{loadError}</div>
        <Link to="/officer/queue">Back to queue</Link>
      </div>
    )
  }

  const canDecide = claim.status === 'UNDER_REVIEW'
  const inInvestigation = claim.status === 'INVESTIGATION'
  const canSettle = claim.status === 'APPROVED'
  const isOpen = canDecide || inInvestigation

  return (
    <div>
      <Link to="/officer/queue" className="d-inline-block mb-3 text-decoration-none">
        <i className="bi bi-arrow-left me-1"></i> Review queue
      </Link>

      <div className="page-header">
        <div>
          <h1 className="page-title d-flex align-items-center flex-wrap gap-3">
            {claim.claim_number}
            <StatusBadge status={claim.status} />
          </h1>
          <p className="page-subtitle">
            {claim.customer_name} · {claim.hospital_name} · submitted {formatDate(claim.submitted_at)}
          </p>
        </div>
        <div className="d-flex gap-2">
          {isOpen && (
            <button className="btn btn-outline-secondary" disabled={saving} onClick={rescore}>
              <i className="bi bi-arrow-repeat me-2"></i>Re-run checks
            </button>
          )}
          <button className="btn btn-outline-primary" onClick={viewBill}>
            <i className="bi bi-file-earmark-pdf me-2"></i>View bill
          </button>
        </div>
      </div>

      <div className="row g-4 mb-4">
        <div className="col-md-4">
          <div className="card h-100">
            <div className="card-body">
              <div className="stat-label mb-1">Rule risk score</div>
              <div className="d-flex align-items-center gap-2 mb-2">
                <span className="stat-value">{claim.risk_score ?? '-'}</span>
                <span className="text-muted">/ 100</span>
                <span className="ms-auto"><RiskBadge level={claim.risk_level} /></span>
              </div>
              <div className="risk-meter">
                <div
                  className="risk-meter-fill"
                  style={{ width: `${claim.risk_score || 0}%`, background: RISK_COLOR[claim.risk_level] || '#9ca3af' }}
                ></div>
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card h-100">
            <div className="card-body">
              <div className="stat-label mb-1">ML fraud probability</div>
              <div className="stat-value mb-2">{formatPercent(claim.ml_fraud_probability)}</div>
              <div className="small text-muted">Second opinion from the trained model. It never changes the status.</div>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card h-100">
            <div className="card-body">
              <div className="stat-label mb-1">Claimed amount</div>
              <div className="stat-value mb-2">{formatMoney(claim.claimed_amount)}</div>
              <div className="small text-muted">Policy cover left: {formatMoney(claim.remaining_sum_insured)}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="row g-4">
        <div className="col-xl-8">
          <div className="card mb-4">
            <div className="card-header">
              <i className="bi bi-file-earmark-text me-2"></i>Bill check: entered vs extracted
            </div>
            <div className="card-body">
              <BillComparison bill={claim.bill} onViewBill={viewBill} />
            </div>
          </div>

          <div className="card mb-4">
            <div className="card-header">
              <i className="bi bi-shield-exclamation me-2"></i>Why this risk score
            </div>
            <div className="card-body py-2">
              <FlagList flags={claim.flags} />
            </div>
          </div>

          <div className="card">
            <div className="card-header">Claim details</div>
            <div className="card-body">
              <dl className="detail-list">
                <dt>Policy</dt>
                <dd>{claim.policy_number}</dd>
                <dt>Treatment</dt>
                <dd>{claim.diagnosis_category.replace('_', ' ')}</dd>
                <dt>Hospital stay</dt>
                <dd>{formatDate(claim.admission_date)} – {formatDate(claim.discharge_date)}</dd>
                {claim.approved_amount !== null && (
                  <>
                    <dt>Approved amount</dt>
                    <dd className="text-success fw-bold">{formatMoney(claim.approved_amount)}</dd>
                  </>
                )}
                {claim.settlement_reference && (
                  <>
                    <dt>Settlement</dt>
                    <dd>{claim.settlement_reference}</dd>
                  </>
                )}
              </dl>
            </div>
          </div>
        </div>

        <div className="col-xl-4">
          <div className="card mb-4">
            <div className="card-header">
              <i className="bi bi-person-check me-2"></i>Decision
            </div>
            <div className="card-body">
              {actionError && <div className="alert alert-danger py-2 small">{actionError}</div>}
              {message && <div className="alert alert-success py-2 small">{message}</div>}

              {canDecide && (
                <div className="mb-3">
                  <label className="form-label fw-medium">Approved amount (₹)</label>
                  <input
                    type="number"
                    className="form-control"
                    min="1"
                    max={claim.claimed_amount}
                    value={approvedAmount}
                    onChange={(e) => setApprovedAmount(e.target.value)}
                  />
                </div>
              )}

              {isOpen && (
                <div className="mb-3">
                  <label className="form-label fw-medium">Note / reason</label>
                  <textarea
                    className="form-control"
                    rows="3"
                    placeholder="Required to reject or investigate"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                  />
                </div>
              )}

              <div className="d-grid gap-2">
                {canDecide && (
                  <>
                    <button className="btn btn-success" disabled={saving} onClick={() => decide('APPROVED')}>
                      <i className="bi bi-check-lg me-2"></i>Approve
                    </button>
                    <button className="btn btn-warning" disabled={saving} onClick={() => decide('INVESTIGATION')}>
                      <i className="bi bi-search me-2"></i>Send to investigation
                    </button>
                    <button className="btn btn-outline-danger" disabled={saving} onClick={() => decide('REJECTED')}>
                      <i className="bi bi-x-lg me-2"></i>Reject
                    </button>
                  </>
                )}

                {inInvestigation && (
                  <>
                    <button className="btn btn-primary" disabled={saving} onClick={() => decide('UNDER_REVIEW')}>
                      <i className="bi bi-arrow-counterclockwise me-2"></i>Back to review
                    </button>
                    <button className="btn btn-outline-danger" disabled={saving} onClick={() => decide('REJECTED')}>
                      <i className="bi bi-x-lg me-2"></i>Reject
                    </button>
                  </>
                )}

                {canSettle && (
                  <>
                    <div className="small text-muted mb-1">
                      Pays {formatMoney(claim.approved_amount)} and deducts it from the policy cover. This can only
                      happen once.
                    </div>
                    <button className="btn btn-success btn-lg" disabled={saving} onClick={settle}>
                      <i className="bi bi-bank me-2"></i>Settle claim
                    </button>
                  </>
                )}

                {!isOpen && !canSettle && (
                  <div className="text-muted small d-flex gap-2 align-items-center">
                    <i className="bi bi-lock"></i>
                    This claim is closed. No more actions.
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <i className="bi bi-clock-history me-2"></i>Audit timeline
            </div>
            <div className="card-body">
              <ClaimTimeline events={claim.events} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ClaimReview
