import { Check, Clock, UserRound, Wrench } from 'lucide-react'
import { AVAILABILITY } from '../../utils/constants'

const STATE_ICON = { reserved: Clock, occupied: UserRound, unavailable: Wrench, mine: Check }

/** The zone's tables in order, each with its own chairs (seat number order). */
function tablesOf(seats) {
  const tables = new Map()
  seats.forEach((seat) => {
    if (seat.table_number == null) return
    if (!tables.has(seat.table_number)) tables.set(seat.table_number, [])
    tables.get(seat.table_number).push(seat)
  })
  return [...tables.entries()]
    .sort(([a], [b]) => a - b)
    .map(([number, chairs]) => ({
      number,
      seats: [...chairs].sort((a, b) => a.number.localeCompare(b.number, undefined, { numeric: true })),
    }))
}

/** Grid tracks for seats that are not at a table: narrow where there is an aisle. */
function tracks(count, used) {
  return Array.from({ length: count }, (_, index) => (
    used.has(index + 1) ? 'var(--seat)' : 'calc(var(--seat) * 0.45)'
  )).join(' ')
}

function SeatButton({ seat, zone, selected, dimmed, onSelect, placed }) {
  const Icon = STATE_ICON[seat.state]
  const where = seat.table_number != null ? `, table ${seat.table_number}` : ''
  return (
    <button
      type="button"
      className={['seat', `seat--${seat.state}`, selected && 'is-selected', dimmed && 'is-dimmed']
        .filter(Boolean).join(' ')}
      style={placed ? { gridRow: seat.row, gridColumn: seat.col } : undefined}
      onClick={() => onSelect(seat, zone)}
      aria-label={`Seat ${seat.number}${where}, ${AVAILABILITY[seat.state].label.toLowerCase()}`}
      aria-pressed={selected}
      title={`Seat ${seat.number} - ${AVAILABILITY[seat.state].label}`}
    >
      {Icon && <Icon className="seat__icon" aria-hidden="true" />}
      <span className="seat__number">
        {/* T03-2 is shown as its chair number: the table's name says the rest. */}
        {seat.table_number != null && seat.number.includes('-')
          ? seat.number.split('-').pop()
          : seat.number}
      </span>
    </button>
  )
}

/**
 * A zone drawn as its seats. Each seat is a button coloured by its state for
 * the chosen time; an icon repeats the state so that colour is never the only
 * cue. Every table is its own group: all of its chairs, then the next table.
 *
 * `onSelectTable`, when given, makes a table's name a button. By default it
 * picks all the chairs of a free table; `tablesAlwaysEnabled` keeps it active
 * whatever the chairs' state (used when managing tables).
 */
export default function SeatMap({
  zone, selectedIds = [], onSelect, onSelectTable, dimmed, tablesAlwaysEnabled = false,
}) {
  const tables = tablesOf(zone.seats)
  const loose = zone.seats.filter((seat) => seat.table_number == null)
  const usedRows = new Set(loose.map((seat) => seat.row))
  const usedCols = new Set(loose.map((seat) => seat.col))
  const seatProps = (seat) => ({
    seat, zone, onSelect, selected: selectedIds.includes(seat.id), dimmed: dimmed?.(seat),
  })

  return (
    <div className="seat-map">
      {tables.length > 0 && (
        <div className="seat-tables">
          {tables.map((table) => {
            const free = table.seats.every((seat) => seat.state === 'available')
            const enabled = tablesAlwaysEnabled || free
            const label = `Table ${table.number}`
            return (
              <div key={table.number} className="seat-table" role="group" aria-label={label}>
                {table.seats.slice(0, 3).map((seat) => <SeatButton key={seat.id} {...seatProps(seat)} />)}
                <div className="seat-table__top">
                  {onSelectTable ? (
                    <button
                      type="button" className="seat-table__label" disabled={!enabled}
                      onClick={() => onSelectTable(table, zone)}
                      aria-label={tablesAlwaysEnabled
                        ? `Manage ${label}`
                        : free
                          ? `${label}: select all ${table.seats.length} seats`
                          : `${label}: not all seats are available`}
                      title={tablesAlwaysEnabled
                        ? 'Manage this table'
                        : free ? 'Select the whole table' : 'Some seats at this table are taken'}
                    >
                      {label}
                    </button>
                  ) : <span className="seat-table__label">{label}</span>}
                </div>
                {table.seats.slice(3).map((seat) => <SeatButton key={seat.id} {...seatProps(seat)} />)}
              </div>
            )
          })}
        </div>
      )}

      {loose.length > 0 && (
        <div
          className="seat-map__grid" role="group" aria-label={`Seats in ${zone.name}`}
          style={{
            '--cols': zone.cols,
            gridTemplateColumns: tracks(zone.cols, usedCols),
            gridTemplateRows: tracks(zone.rows, usedRows),
          }}
        >
          {loose.map((seat) => <SeatButton key={seat.id} placed {...seatProps(seat)} />)}
        </div>
      )}
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
