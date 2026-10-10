function StatCard({ label, value, icon, tone = 'indigo', hint }) {
  return (
    <div className="card h-100">
      <div className="card-body stat-card">
        <div className={`stat-icon tone-${tone}`}>
          <i className={`bi ${icon}`}></i>
        </div>
        <div>
          <div className="stat-label">{label}</div>
          <div className="stat-value">{value}</div>
          {hint && <div className="small text-muted">{hint}</div>}
        </div>
      </div>
    </div>
  )
}

export default StatCard
