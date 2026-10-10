import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import EmptyState from '../../components/EmptyState.jsx'
import Loading from '../../components/Loading.jsx'
import PageHeader from '../../components/PageHeader.jsx'
import Pagination from '../../components/Pagination.jsx'
import StatusBadge from '../../components/StatusBadge.jsx'
import { getClaims } from '../../api/claims.js'
import { getErrorMessage } from '../../api/client.js'
import { formatDate, formatMoney } from '../../utils/format.js'

function MyClaims() {
  const navigate = useNavigate()
  const [claims, setClaims] = useState([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadClaims() {
      setLoading(true)
      try {
        const data = await getClaims({ page })
        setClaims(data.items)
        setTotalPages(data.total_pages)
      } catch (err) {
        setError(getErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }
    loadClaims()
  }, [page])

  return (
    <div>
      <PageHeader title="My Claims" subtitle="Track every reimbursement claim you have submitted">
        <Link to="/customer/claims/new" className="btn btn-primary">
          <i className="bi bi-plus-lg me-2"></i>New Claim
        </Link>
      </PageHeader>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card table-card">
        {loading && <div className="px-4"><Loading text="Loading claims..." /></div>}

        {!loading && !error && claims.length === 0 && (
          <EmptyState icon="bi-file-earmark-medical" title="No claims yet" text="Submit your first hospital bill to get started.">
            <Link to="/customer/claims/new" className="btn btn-primary btn-sm">Submit a claim</Link>
          </EmptyState>
        )}

        {!loading && claims.length > 0 && (
          <table className="table table-hover">
            <thead>
              <tr>
                <th>Claim No</th>
                <th>Hospital</th>
                <th>Treatment</th>
                <th className="text-end">Amount</th>
                <th>Status</th>
                <th>Submitted</th>
              </tr>
            </thead>
            <tbody>
              {claims.map((claim) => (
                <tr key={claim.id} onClick={() => navigate(`/customer/claims/${claim.id}`)}>
                  <td className="fw-semibold text-nowrap">{claim.claim_number}</td>
                  <td>{claim.hospital_name}</td>
                  <td className="text-muted">{claim.diagnosis_category.replace('_', ' ')}</td>
                  <td className="text-end">{formatMoney(claim.claimed_amount)}</td>
                  <td><StatusBadge status={claim.status} /></td>
                  <td className="text-muted text-nowrap">{formatDate(claim.submitted_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
    </div>
  )
}

export default MyClaims
