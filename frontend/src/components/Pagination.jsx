function Pagination({ page, totalPages, onPageChange }) {
  if (totalPages <= 1) {
    return null
  }

  return (
    <div className="d-flex justify-content-between align-items-center mt-3">
      <span className="small text-muted">
        Page {page} of {totalPages}
      </span>
      <div className="btn-group">
        <button className="btn btn-sm btn-outline-secondary" disabled={page === 1} onClick={() => onPageChange(page - 1)}>
          <i className="bi bi-chevron-left"></i> Previous
        </button>
        <button
          className="btn btn-sm btn-outline-secondary"
          disabled={page === totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Next <i className="bi bi-chevron-right"></i>
        </button>
      </div>
    </div>
  )
}

export default Pagination
