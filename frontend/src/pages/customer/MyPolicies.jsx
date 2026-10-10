import { useEffect, useState } from 'react'

import EmptyState from '../../components/EmptyState.jsx'
import Loading from '../../components/Loading.jsx'
import PageHeader from '../../components/PageHeader.jsx'
import { getMyPolicies } from '../../api/claims.js'
import { getErrorMessage } from '../../api/client.js'
import { formatDate, formatMoney } from '../../utils/format.js'

function MyPolicies() {
  const [policies, setPolicies] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadPolicies() {
      try {
        setPolicies(await getMyPolicies())
      } catch (err) {
        setError(getErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }
    loadPolicies()
  }, [])

  return (
    <div>
      <PageHeader title="My Policies" subtitle="Your health cover and how much of it is left" />

      {error && <div className="alert alert-danger">{error}</div>}
      {loading && <Loading text="Loading policies..." />}

      {!loading && !error && policies.length === 0 && (
        <div className="card">
          <EmptyState icon="bi-shield" title="No policies yet" text="Your insurer will add your policy here." />
        </div>
      )}

      <div className="row g-4">
        {policies.map((policy) => {
          const usedPercent = Math.round((1 - policy.remaining_sum_insured / policy.sum_insured) * 100)
          return (
            <div className="col-md-6 col-xl-4" key={policy.id}>
              <div className="card policy-card h-100">
                <div className="card-body">
                  <div className="d-flex justify-content-between align-items-start mb-3">
                    <div>
                      <div className="small text-muted">{policy.plan_name} plan</div>
                      <div className="fw-bold fs-5">{policy.policy_number}</div>
                    </div>
                    <span className={`soft-badge ${policy.status === 'ACTIVE' ? 'tone-green' : 'tone-gray'}`}>
                      <span className="dot"></span>
                      {policy.status}
                    </span>
                  </div>

                  <div className="small text-muted">Remaining cover</div>
                  <div className="fs-3 fw-bold mb-2">{formatMoney(policy.remaining_sum_insured)}</div>
                  <div className="progress mb-1">
                    <div className="progress-bar" style={{ width: `${usedPercent}%`, background: 'var(--cg-primary)' }}></div>
                  </div>
                  <div className="small text-muted mb-3">
                    {usedPercent}% used of {formatMoney(policy.sum_insured)}
                  </div>

                  <dl className="detail-list small">
                    <dt>Valid</dt>
                    <dd>{formatDate(policy.start_date)} – {formatDate(policy.end_date)}</dd>
                    <dt>Waiting period</dt>
                    <dd>{policy.waiting_period_days} days</dd>
                  </dl>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default MyPolicies
