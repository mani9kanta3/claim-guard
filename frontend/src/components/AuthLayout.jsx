const FEATURES = [
  { icon: 'bi-file-earmark-text', text: 'An LLM reads the hospital bill and compares it with the claim form' },
  { icon: 'bi-shield-exclamation', text: '8 explainable fraud rules plus an ML model score every claim' },
  { icon: 'bi-lock', text: 'Row-locked settlement, so a claim can never be paid twice' },
  { icon: 'bi-clock-history', text: 'Every status change is recorded in an audit timeline' },
]

function AuthLayout({ children }) {
  return (
    <div className="auth-page">
      <section className="auth-hero">
        <div className="d-flex align-items-center gap-2 fs-5 fw-bold">
          <span className="brand-icon">
            <i className="bi bi-shield-fill-check"></i>
          </span>
          ClaimGuard
        </div>

        <div className="my-auto">
          <h1 className="mb-3">
            Health insurance claims,
            <br />
            checked for fraud.
          </h1>
          <p className="mb-5" style={{ color: '#c7d2fe', maxWidth: 460 }}>
            Policyholders submit reimbursement claims, officers review them with clear risk reasons, and money is
            settled exactly once.
          </p>
          {FEATURES.map((feature) => (
            <div className="auth-feature" key={feature.text}>
              <i className={`bi ${feature.icon}`}></i>
              <span>{feature.text}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="auth-form-side">
        <div className="auth-card">{children}</div>
      </section>
    </div>
  )
}

export default AuthLayout
