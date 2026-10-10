import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import ClaimTimeline from '../../components/ClaimTimeline.jsx'
import Loading from '../../components/Loading.jsx'
import StatusBadge from '../../components/StatusBadge.jsx'
import StatusStepper from '../../components/StatusStepper.jsx'
import { getClaim, openClaimDocument } from '../../api/claims.js'
import { getErrorMessage } from '../../api/client.js'
import { formatDate, formatMoney } from '../../utils/format.js'

function ClaimStatus() {
  const { id } = useParams()
  const [claim, setClaim] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadClaim() {
      try {
        setClaim(await getClaim(id))
      } catch (err) {
        setError(getErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }
    loadClaim()
  }, [id])

  async function viewBill() {
    try {
      await openClaimDocument(id)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  if (loading) {
    return <Loading text="Loading claim..." />
  }

  if (!claim) {
    return (
      <div>
        <div className="alert alert-danger">{error}</div>
        <Link to="/customer/claims">Back to my claims</Link>
      </div>
    )
  }

  return (
    <div>
      <Link to="/customer/claims" className="d-inline-block mb-3 text-decoration-none">
        <i className="bi bi-arrow-left me-1"></i> My claims
      </Link>

      <div className="page-header">
        <div>
          <h1 className="page-title d-flex align-items-center gap-3">
            {claim.claim_number}
            <StatusBadge status={claim.status} />
          </h1>
          <p className="page-subtitle">
            {claim.hospital_name} · submitted {formatDate(claim.submitted_at)}
          </p>
        </div>
        <button className="btn btn-outline-primary" onClick={viewBill}>
          <i className="bi bi-file-earmark-pdf me-2"></i>View bill
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card mb-4">
        <div className="card-body">
          <StatusStepper status={claim.status} />
        </div>
      </div>

      <div className="row g-4">
        <div className="col-lg-7">
          <div className="card">
            <div className="card-header">Claim details</div>
            <div className="card-body">
              <dl className="detail-list">
                <dt>Policy</dt>
                <dd>{claim.policy_number}</dd>
                <dt>Hospital</dt>
                <dd>{claim.hospital_name}</dd>
                <dt>Treatment</dt>
                <dd>{claim.diagnosis_category.replace('_', ' ')}</dd>
                <dt>Hospital stay</dt>
                <dd>{formatDate(claim.admission_date)} – {formatDate(claim.discharge_date)}</dd>
                <dt>Claimed amount</dt>
                <dd>{formatMoney(claim.claimed_amount)}</dd>
                {claim.approved_amount !== null && (
                  <>
                    <dt>Approved amount</dt>
                    <dd className="text-success fw-bold">{formatMoney(claim.approved_amount)}</dd>
                  </>
                )}
              </dl>
            </div>
          </div>
        </div>

        <div className="col-lg-5">
          <div className="card">
            <div className="card-header">Timeline</div>
            <div className="card-body">
              <ClaimTimeline events={claim.events} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ClaimStatus
