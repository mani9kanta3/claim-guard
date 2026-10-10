import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import Loading from '../../components/Loading.jsx'
import PageHeader from '../../components/PageHeader.jsx'
import StatCard from '../../components/StatCard.jsx'
import { getDashboardSummary } from '../../api/admin.js'
import { getErrorMessage } from '../../api/client.js'
import { formatMoney } from '../../utils/format.js'

const STATUS_COLORS = {
  UNDER_REVIEW: '#4338ca',
  INVESTIGATION: '#d97706',
  APPROVED: '#0284c7',
  SETTLED: '#059669',
  REJECTED: '#dc2626',
  SUBMITTED: '#6b7280',
}

const RISK_COLORS = { LOW: '#059669', MEDIUM: '#d97706', HIGH: '#dc2626' }

const RULE_NAMES = {
  R1: 'Waiting period',
  R2: 'Duplicate bill',
  R3: 'Most of cover',
  R4: 'Unusual amount',
  R5: 'Non-network',
  R6: 'Frequent claims',
  R7: 'Total mismatch',
  R8: 'Details mismatch',
}

function formatHours(hours) {
  if (hours === null) {
    return '-'
  }
  if (hours < 48) {
    return `${hours} h`
  }
  return `${(hours / 24).toFixed(1)} days`
}

function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadSummary() {
      try {
        setSummary(await getDashboardSummary())
      } catch (err) {
        setError(getErrorMessage(err))
      }
    }
    loadSummary()
  }, [])

  if (error) {
    return <div className="alert alert-danger">{error}</div>
  }

  if (!summary) {
    return <Loading text="Loading dashboard..." />
  }

  const statusData = summary.claims_by_status.map((row) => ({
    name: row.status.replace('_', ' '),
    value: row.count,
    color: STATUS_COLORS[row.status],
  }))
  const riskData = summary.claims_by_risk.map((row) => ({
    name: row.risk_level,
    value: row.count,
    color: RISK_COLORS[row.risk_level],
  }))
  const flagData = summary.flags_by_rule.map((row) => ({
    name: row.rule_code,
    label: RULE_NAMES[row.rule_code],
    count: row.count,
  }))

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Claims, risk and settlements at a glance" />

      <div className="row g-3 mb-4">
        <div className="col-sm-6 col-xl">
          <StatCard label="Total claims" value={summary.total_claims} icon="bi-files" tone="indigo" />
        </div>
        <div className="col-sm-6 col-xl">
          <StatCard label="Waiting for review" value={summary.pending_review} icon="bi-hourglass-split" tone="amber" />
        </div>
        <div className="col-sm-6 col-xl">
          <StatCard label="High risk" value={summary.high_risk} icon="bi-exclamation-triangle" tone="red" />
        </div>
        <div className="col-sm-6 col-xl">
          <StatCard
            label="Settled amount"
            value={formatMoney(summary.settled_amount)}
            icon="bi-cash-stack"
            tone="green"
            hint={`${summary.awaiting_settlement} approved, waiting to settle`}
          />
        </div>
        <div className="col-sm-6 col-xl">
          <StatCard
            label="Avg time to decision"
            value={formatHours(summary.avg_hours_to_decision)}
            icon="bi-stopwatch"
            tone="sky"
          />
        </div>
      </div>

      <div className="row g-4">
        <div className="col-lg-6">
          <div className="card h-100">
            <div className="card-header">Claims by status</div>
            <div className="card-body chart-box">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={statusData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100} paddingAngle={2} isAnimationActive={false}>
                    {statusData.map((item) => (
                      <Cell key={item.name} fill={item.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="col-lg-6">
          <div className="card h-100">
            <div className="card-header">Risk mix</div>
            <div className="card-body chart-box">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={riskData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100} paddingAngle={2} isAnimationActive={false}>
                    {riskData.map((item) => (
                      <Cell key={item.name} fill={item.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="col-12">
          <div className="card">
            <div className="card-header">Fraud rules fired</div>
            <div className="card-body chart-box">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={flagData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" name="Claims flagged" fill="#4338ca" radius={[6, 6, 0, 0]} isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
