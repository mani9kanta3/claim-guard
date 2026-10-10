const RISK_TONE = {
  LOW: 'tone-green',
  MEDIUM: 'tone-amber',
  HIGH: 'tone-red',
}

function RiskBadge({ level, score }) {
  if (!level) {
    return <span className="text-muted">-</span>
  }

  return (
    <span className={`soft-badge ${RISK_TONE[level]}`}>
      {level}
      {score !== undefined && score !== null && <span className="opacity-75">· {score}</span>}
    </span>
  )
}

export default RiskBadge
