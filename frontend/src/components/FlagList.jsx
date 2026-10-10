const RULE_NAMES = {
  R1: 'Waiting period',
  R2: 'Duplicate bill',
  R3: 'Most of cover used',
  R4: 'Unusual amount',
  R5: 'Non-network hospital',
  R6: 'Frequent claims',
  R7: 'Bill total mismatch',
  R8: 'Bill details mismatch',
}

function FlagList({ flags }) {
  if (flags.length === 0) {
    return (
      <div className="d-flex align-items-center gap-2 text-success">
        <i className="bi bi-check-circle-fill"></i>
        No fraud rules fired. This claim looks clean.
      </div>
    )
  }

  return (
    <div>
      {flags.map((flag) => (
        <div className="flag-item" key={flag.id}>
          <div className="flag-code">{flag.rule_code}</div>
          <div className="flex-grow-1">
            <div className="fw-semibold">{RULE_NAMES[flag.rule_code]}</div>
            <div className="small text-muted">{flag.reason}</div>
          </div>
          <div className="fw-bold text-danger">+{flag.points}</div>
        </div>
      ))}
    </div>
  )
}

export default FlagList
