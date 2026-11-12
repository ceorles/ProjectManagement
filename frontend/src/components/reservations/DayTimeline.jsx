import { formatTime, formatTimeRange, timeToMinutes } from '../../utils/datetime'

const LABELS = { confirmed: 'Reserved', checked_in: 'In use' }

function hourMarks(opens, closes) {
  const marks = []
  const step = closes - opens > 8 * 60 ? 120 : 60
  for (let minutes = Math.ceil(opens / 60) * 60; minutes <= closes; minutes += step) {
    marks.push(minutes)
  }
  return marks
}

/**
 * One day of a seat or room as a bar from opening to closing time, with the
 * booked intervals and (optionally) the window being considered. The same
 * information is listed as text underneath.
 */
export default function DayTimeline({ schedule, selection }) {
  if (!schedule.is_open) {
    return <p className="muted small">{schedule.closed_reason || 'The library is closed on this day.'}</p>
  }
  const opens = timeToMinutes(schedule.opens_at)
  const closes = timeToMinutes(schedule.closes_at)
  const span = closes - opens
  const place = (start, end) => ({
    left: `${(Math.max(timeToMinutes(start), opens) - opens) / span * 100}%`,
    width: `${(Math.min(timeToMinutes(end), closes) - Math.max(timeToMinutes(start), opens)) / span * 100}%`,
  })

  return (
    <div className="timeline">
      <div className="timeline__bar" aria-hidden="true">
        {schedule.blocks.map((block) => (
          <span
            key={`${block.start_time}-${block.status}`}
            className={`timeline__block timeline__block--${block.is_mine ? 'mine' : block.status}`}
            style={place(block.start_time, block.end_time)}
            title={`${formatTimeRange(block.start_time, block.end_time)} - ${block.is_mine ? 'Your reservation' : LABELS[block.status]}`}
          />
        ))}
        {selection?.start && (
          <span className="timeline__selection" style={place(selection.start, selection.end)} />
        )}
      </div>
      <div className="timeline__axis" aria-hidden="true">
        {hourMarks(opens, closes).map((minutes) => (
          <span key={minutes} style={{ left: `${(minutes - opens) / span * 100}%` }}>
            {formatTime(`${Math.floor(minutes / 60)}:00`).replace(':00', '')}
          </span>
        ))}
      </div>

      {schedule.blocks.length === 0 ? (
        <p className="small muted">
          No reservations on this day yet. Open {formatTimeRange(schedule.opens_at, schedule.closes_at)}.
        </p>
      ) : (
        <ul className="timeline__list">
          {schedule.blocks.map((block) => (
            <li key={`${block.start_time}-${block.status}`}>
              <span className={`timeline__swatch timeline__block--${block.is_mine ? 'mine' : block.status}`} aria-hidden="true" />
              <span className="strong">{formatTimeRange(block.start_time, block.end_time)}</span>
              <span className="muted">
                {block.is_mine ? 'Your reservation' : LABELS[block.status]}
                {block.student_name && ` - ${block.student_name}`}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
