const STEPS = ['SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'SETTLED']
const STEP_LABELS = ['Submitted', 'Under review', 'Approved', 'Paid']

function StatusStepper({ status }) {
  if (status === 'REJECTED') {
    return (
      <div className="stepper">
        <div className="step done">
          <div className="step-bar"></div>Submitted
        </div>
        <div className="step done">
          <div className="step-bar"></div>Reviewed
        </div>
        <div className="step failed">
          <div className="step-bar"></div>Rejected
        </div>
      </div>
    )
  }

  const currentStatus = status === 'INVESTIGATION' ? 'UNDER_REVIEW' : status
  const currentIndex = STEPS.indexOf(currentStatus)

  return (
    <div className="stepper">
      {STEPS.map((step, index) => (
        <div key={step} className={`step ${index <= currentIndex ? 'done' : ''}`}>
          <div className="step-bar"></div>
          {step === 'UNDER_REVIEW' && status === 'INVESTIGATION' ? 'Being verified' : STEP_LABELS[index]}
        </div>
      ))}
    </div>
  )
}

export default StatusStepper
