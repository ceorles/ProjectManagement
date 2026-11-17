import { Check, Clock, UserRound, Wrench } from 'lucide-react'
import { AVAILABILITY } from '../../utils/constants'

const STATE_ICON = { reserved: Clock, occupied: UserRound, unavailable: Wrench, mine: Check }

/** Seats grouped by the table they belong to, with the area each table covers. */
function tablesOf(seats) {
  const tables = new Map()
  seats.forEach((seat) => {
    if (seat.table_number == null) return
    const table = tables.get(seat.table_number) || {
      number: seat.table_number, seats: [],
      top: seat.row, bottom: seat.row, left: seat.col, right: seat.col,
    }
    table.seats.push(seat)
    table.top = Math.min(table.top, seat.row)
    table.bottom = Math.max(table.bottom, seat.row)
    table.left = Math.min(table.left, seat.col)
    table.right = Math.max(table.right, seat.col)
    tables.set(seat.table_number, table)
  })
  return [...tables.values()].sort((a, b) => a.number - b.number)
}

/**
 * Grid tracks: full size where there are seats, a medium strip for the table
 * top between two rows of chairs, and a narrow one for an aisle.
 */
function tracks(count, used, tableTop) {
  return Array.from({ length: count }, (_, index) => {
    if (used.has(index + 1)) return 'var(--seat)'
    return tableTop.has(index + 1) ? 'calc(var(--seat) * 0.7)' : 'calc(var(--seat) * 0.45)'
  }).join(' ')
}

/**
 * A zone drawn as its real grid of seats. Each seat is a button coloured by
 * its state for the chosen time; an icon repeats the state so that colour is
 * never the only cue. Chairs of the same table are drawn around a shared,
 * labelled table top. Empty grid cells are the aisles.
 *
 * `onSelectTable`, when given, makes a table's label a button that picks all
 * of its chairs at once.
 */
export default function SeatMap({ zone, selectedIds = [], onSelect, onSelectTable, dimmed }) {
  const usedRows = new Set(zone.seats.map((seat) => seat.row))
  const usedCols = new Set(zone.seats.map((seat) => seat.col))
  const tables = tablesOf(zone.seats)
  const tableRows = new Set()
  tables.forEach((table) => {
    for (let row = table.top; row <= table.bottom; row += 1) tableRows.add(row)
  })

  return (
    <div className="seat-map">
      <div
        className="seat-map__grid" role="group" aria-label={`Seats in ${zone.name}`}
        style={{
          '--cols': zone.cols,
          gridTemplateColumns: tracks(zone.cols, usedCols, new Set()),
          gridTemplateRows: tracks(zone.rows, usedRows, tableRows),
        }}
      >
        {tables.map((table) => {
          const free = table.seats.every((seat) => seat.state === 'available')
          const label = `Table ${table.number}`
          return (
            <div
              key={`table-${table.number}`} className="seat-table"
              style={{
                gridRow: `${table.top} / ${table.bottom + 1}`,
                gridColumn: `${table.left} / ${table.right + 1}`,
              }}
            >
              {onSelectTable ? (
                <button
                  type="button" className="seat-table__label" disabled={!free}
                  onClick={() => onSelectTable(table, zone)}
                  aria-label={free
                    ? `${label}: select all ${table.seats.length} seats`
                    : `${label}: not all seats are available`}
                  title={free ? 'Select the whole table' : 'Some seats at this table are taken'}
                >
                  {label}
                </button>
              ) : <span className="seat-table__label">{label}</span>}
            </div>
          )
        })}

        {zone.seats.map((seat) => {
          const Icon = STATE_ICON[seat.state]
          const selected = selectedIds.includes(seat.id)
          const where = seat.table_number != null ? `, table ${seat.table_number}` : ''
          return (
            <button
              key={seat.id} type="button"
              className={[
                'seat', `seat--${seat.state}`,
                selected && 'is-selected', dimmed?.(seat) && 'is-dimmed',
              ].filter(Boolean).join(' ')}
              style={{ gridRow: seat.row, gridColumn: seat.col }}
              onClick={() => onSelect(seat, zone)}
              aria-label={`Seat ${seat.number}${where}, ${AVAILABILITY[seat.state].label.toLowerCase()}`}
              aria-pressed={selected}
              title={`Seat ${seat.number} - ${AVAILABILITY[seat.state].label}`}
            >
              {Icon && <Icon className="seat__icon" aria-hidden="true" />}
              <span className="seat__number">
                {/* T03-2 is shown as its chair number: the table label says the rest. */}
                {seat.table_number != null && seat.number.includes('-')
                  ? seat.number.split('-').pop()
                  : seat.number}
              </span>
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
    { state: 'reserved', label: 'Requested or reserved' },
    { state: 'occupied', label: 'Occupied' },
    !staff && { state: 'mine', label: 'Yours' },
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
