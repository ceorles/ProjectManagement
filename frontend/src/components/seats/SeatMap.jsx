import { Check, Clock, UserRound, Wrench } from 'lucide-react'
import { AVAILABILITY } from '../../utils/constants'

const STATE_ICON = { reserved: Clock, occupied: UserRound, unavailable: Wrench, mine: Check }

/** Grid tracks: a full-size track where there are seats, a narrow one for an aisle. */
function tracks(count, used) {
  return Array.from({ length: count }, (_, index) => (
    used.has(index + 1) ? 'var(--seat)' : 'calc(var(--seat) * 0.45)'
  )).join(' ')
}

/**
 * A zone drawn as its real grid of seats. Each seat is a button coloured by
 * its state for the chosen time; an icon repeats the state so that colour is
 * never the only cue. Empty grid cells are the aisles.
 */
export default function SeatMap({ zone, selectedId, onSelect, dimmed }) {
  const usedRows = new Set(zone.seats.map((seat) => seat.row))
  const usedCols = new Set(zone.seats.map((seat) => seat.col))
  return (
    <div className="seat-map">
      <div
        className="seat-map__grid" role="group" aria-label={`Seats in ${zone.name}`}
        style={{
          '--cols': zone.cols,
          gridTemplateColumns: tracks(zone.cols, usedCols),
          gridTemplateRows: tracks(zone.rows, usedRows),
        }}
      >
        {zone.seats.map((seat) => {
          const Icon = STATE_ICON[seat.state]
          const isDimmed = dimmed?.(seat)
          return (
            <button
              key={seat.id} type="button"
              className={[
                'seat', `seat--${seat.state}`,
                seat.id === selectedId && 'is-selected', isDimmed && 'is-dimmed',
              ].filter(Boolean).join(' ')}
              style={{ gridRow: seat.row, gridColumn: seat.col }}
              onClick={() => onSelect(seat, zone)}
              aria-label={`Seat ${seat.number}, ${AVAILABILITY[seat.state].label.toLowerCase()}`}
              aria-pressed={seat.id === selectedId}
              title={`Seat ${seat.number} - ${AVAILABILITY[seat.state].label}`}
            >
              {Icon && <Icon className="seat__icon" aria-hidden="true" />}
              <span className="seat__number">{seat.number}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export function SeatLegend({ staff = false }) {
  const items = [
    { state: 'available', label: 'Available' },
    { state: 'reserved', label: 'Reserved' },
    { state: 'occupied', label: 'Occupied' },
    !staff && { state: 'mine', label: 'Your reservation' },
    { state: 'unavailable', label: 'Unavailable' },
  ].filter(Boolean)
  return (
    <ul className="seat-legend" aria-label="Seat colours">
      {items.map((item) => {
        const Icon = STATE_ICON[item.state]
        return (
          <li key={item.state}>
            <span className={`seat seat--${item.state} seat--swatch`} aria-hidden="true">
              {Icon && <Icon className="seat__icon" />}
            </span>
            {item.label}
          </li>
        )
      })}
    </ul>
  )
}
