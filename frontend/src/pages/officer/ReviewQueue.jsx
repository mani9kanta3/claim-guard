import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import EmptyState from '../../components/EmptyState.jsx'
import Loading from '../../components/Loading.jsx'
import PageHeader from '../../components/PageHeader.jsx'
import Pagination from '../../components/Pagination.jsx'
import RiskBadge from '../../components/RiskBadge.jsx'
import StatusBadge from '../../components/StatusBadge.jsx'
import { getClaims } from '../../api/claims.js'
import { getErrorMessage } from '../../api/client.js'
import { RISK_LEVELS } from '../../constants.js'
import { formatDate, formatMoney, formatPercent } from '../../utils/format.js'

const TABS = [
  { status: 'UNDER_REVIEW', label: 'To review' },
  { status: 'INVESTIGATION', label: 'Investigation' },
  { status: 'APPROVED', label: 'To settle' },
  { status: 'SETTLED', label: 'Settled' },
  { status: 'REJECTED', label: 'Rejected' },
  { status: '', label: 'All' },
]

function ReviewQueue() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState('UNDER_REVIEW')
  const [riskFilter, setRiskFilter] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const [claims, setClaims] = useState([])
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadClaims() {
      setLoading(true)
      setError('')
      try {
        const data = await getClaims({ status: statusFilter, risk_level: riskFilter, search, page })
        setClaims(data.items)
        setTotal(data.total)
        setTotalPages(data.total_pages)
      } catch (err) {
        setError(getErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }
    loadClaims()
  }, [statusFilter, riskFilter, search, page])

  function changeTab(status) {
    setStatusFilter(status)
    setPage(1)
  }

  return (
    <div>
      <PageHeader title="Review Queue" subtitle="Highest risk claims first. Open a claim to see the reasons and decide." />

      <ul className="nav nav-pills mb-3 gap-1">
        {TABS.map((tab) => (
          <li className="nav-item" key={tab.label}>
            <button
              className={`nav-link ${statusFilter === tab.status ? 'active' : 'text-secondary'}`}
              style={statusFilter === tab.status ? { background: 'var(--cg-primary)' } : {}}
              onClick={() => changeTab(tab.status)}
            >
              {tab.label}
            </button>
          </li>
        ))}
      </ul>

      <div className="card table-card">
        <div className="card-body d-flex flex-wrap gap-2 align-items-center border-bottom">
          <div className="input-group" style={{ maxWidth: 280 }}>
            <span className="input-group-text bg-white"><i className="bi bi-search"></i></span>
            <input
              className="form-control"
              placeholder="Search claim number"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
            />
          </div>
          <select
            className="form-select"
            style={{ maxWidth: 180 }}
            value={riskFilter}
            onChange={(e) => {
              setRiskFilter(e.target.value)
              setPage(1)
            }}
          >
            <option value="">All risk levels</option>
            {RISK_LEVELS.map((level) => (
              <option key={level} value={level}>{level} risk</option>
            ))}
          </select>
          <span className="ms-auto small text-muted">{total} claims</span>
        </div>

        {error && <div className="alert alert-danger m-3">{error}</div>}
        {loading && <div className="px-4"><Loading text="Loading claims..." /></div>}

        {!loading && !error && claims.length === 0 && (
          <EmptyState icon="bi-check2-all" title="Nothing here" text="No claims match these filters." />
        )}

        {!loading && claims.length > 0 && (
          <table className="table table-hover">
            <thead>
              <tr>
                <th>Claim No</th>
                <th>Customer</th>
                <th>Hospital</th>
                <th className="text-end">Amount</th>
                <th>Risk</th>
                <th>ML</th>
                <th>Status</th>
                <th>Submitted</th>
              </tr>
            </thead>
            <tbody>
              {claims.map((claim) => (
                <tr key={claim.id} onClick={() => navigate(`/officer/claims/${claim.id}`)}>
                  <td className="fw-semibold text-nowrap">{claim.claim_number}</td>
                  <td>{claim.customer_name}</td>
                  <td className="text-muted">{claim.hospital_name}</td>
                  <td className="text-end">{formatMoney(claim.claimed_amount)}</td>
                  <td><RiskBadge level={claim.risk_level} score={claim.risk_score} /></td>
                  <td>{formatPercent(claim.ml_fraud_probability)}</td>
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

export default ReviewQueue
