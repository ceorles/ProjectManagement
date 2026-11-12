import { CalendarX } from 'lucide-react'
import { useLibrary } from '../../hooks/useLibrary'
import { bookableDates, durations, endTime, startTimes } from '../../utils/booking'
import { addDays, formatDate, formatDuration, formatTime } from '../../utils/datetime'
import { SelectField } from '../common/FormControls'

function dayLabel(date, today) {
  if (date === today) return 'Today'
  if (date === addDays(today, 1)) return 'Tomorrow'
  return formatDate(date, { weekday: 'short', month: undefined, day: undefined, year: undefined })
}

/**
 * Choose when: a date, a start time and how long. Only dates and times the
 * library is open and that the booking rules allow are offered.
 */
export default function BookingWindowPicker({ resourceType, window, onChange }) {
  const { overview, now, policy } = useLibrary()
  const dates = bookableDates(overview, now)
  const starts = startTimes(overview, window.date, now)
  const lengths = durations(overview, window.date, window.start, resourceType)

  if (!dates.some((item) => item.isOpen)) {
    return (
      <p className="notice notice--warning">
        <CalendarX size={16} aria-hidden="true" />
        The library has no open days in the next {policy.max_advance_days + 1} days, so nothing can be reserved right now.
      </p>
    )
  }

  return (
    <div className="window-picker">
      <div>
        <p className="field__label" id="window-date-label">Date</p>
        <div className="date-chips" role="radiogroup" aria-labelledby="window-date-label">
          {dates.map((item) => (
            <button
              key={item.date} type="button" role="radio"
              aria-checked={item.date === window.date} disabled={!item.isOpen}
              className={`date-chip ${item.date === window.date ? 'is-selected' : ''}`}
              onClick={() => onChange({ date: item.date })}
              title={item.isOpen ? formatDate(item.date) : `${formatDate(item.date)} - ${item.reason}`}
            >
              <span className="date-chip__day">{dayLabel(item.date, now.date)}</span>
              <span className="date-chip__date">
                {formatDate(item.date, { weekday: undefined, year: undefined })}
              </span>
              {!item.isOpen && <span className="date-chip__closed">Closed</span>}
            </button>
          ))}
        </div>
      </div>

      <div className="window-picker__times">
        <SelectField label="Start time" value={window.start}
          onChange={(event) => onChange({ start: event.target.value })}>
          {starts.map((time) => <option key={time} value={time}>{formatTime(time)}</option>)}
        </SelectField>
        <SelectField label="Duration" value={window.duration}
          onChange={(event) => onChange({ duration: Number(event.target.value) })}>
          {lengths.map((minutes) => (
            <option key={minutes} value={minutes}>
              {formatDuration(minutes)} (until {formatTime(endTime(window.start, minutes))})
            </option>
          ))}
        </SelectField>
      </div>
    </div>
  )
}
