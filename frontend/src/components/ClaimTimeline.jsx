import StatusBadge from './StatusBadge.jsx'
import { formatDateTime } from '../utils/format.js'

function ClaimTimeline({ events }) {
  if (events.length === 0) {
    return <p className="text-muted mb-0">No events yet.</p>
  }

  return (
    <ul className="timeline">
      {events.map((event) => (
        <li key={event.id}>
          <span className="timeline-dot"></span>
          <div className="d-flex justify-content-between flex-wrap gap-2">
            <StatusBadge status={event.to_status} />
            <small className="text-muted">{formatDateTime(event.created_at)}</small>
          </div>
          <div className="small mt-1">
            <span className="text-muted">By</span> {event.actor_name || 'System'}
          </div>
          {event.note && <div className="small text-muted mt-1">{event.note}</div>}
        </li>
      ))}
    </ul>
  )
}

export default ClaimTimeline
