const STATUS_STYLE = {
  SUBMITTED: { tone: 'tone-gray', label: 'Submitted' },
  UNDER_REVIEW: { tone: 'tone-indigo', label: 'Under review' },
  INVESTIGATION: { tone: 'tone-amber', label: 'Investigation' },
  APPROVED: { tone: 'tone-sky', label: 'Approved' },
  SETTLED: { tone: 'tone-green', label: 'Settled' },
  REJECTED: { tone: 'tone-red', label: 'Rejected' },
}

function StatusBadge({ status }) {
  const style = STATUS_STYLE[status] || { tone: 'tone-gray', label: status }

  return (
    <span className={`soft-badge ${style.tone}`}>
      <span className="dot"></span>
      {style.label}
    </span>
  )
}

export default StatusBadge
