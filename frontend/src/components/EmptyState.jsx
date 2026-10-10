function EmptyState({ icon = 'bi-inbox', title, text, children }) {
  return (
    <div className="empty-state">
      <i className={`bi ${icon}`}></i>
      <div className="fw-semibold text-dark">{title}</div>
      {text && <div className="small mt-1">{text}</div>}
      {children && <div className="mt-3">{children}</div>}
    </div>
  )
}

export default EmptyState
