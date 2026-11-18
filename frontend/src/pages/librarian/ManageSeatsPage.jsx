import { useState } from 'react'
import { Armchair, Pencil, Plus, Trash2, Wrench } from 'lucide-react'
import Badge from '../../components/common/Badge'
import Button from '../../components/common/Button'
import Card from '../../components/common/Card'
import ConfirmDialog from '../../components/common/ConfirmDialog'
import DataTable from '../../components/common/DataTable'
import { EmptyState, QueryBoundary } from '../../components/common/Feedback'
import PageHeader from '../../components/common/PageHeader'
import { SeatFormModal, ZoneFormModal } from '../../components/seats/SeatForms'
import SeatMap from '../../components/seats/SeatMap'
import SeatStatusDialog from '../../components/seats/SeatStatusDialog'
import TableStatusDialog from '../../components/seats/TableStatusDialog'
import '../../components/seats/seats.css'
import { useAction } from '../../hooks/useAction'
import { useApiQuery } from '../../hooks/useApiQuery'
import { libraryService, seatService } from '../../services'
import { RESOURCE_STATUS, SEAT_FEATURES, TABLE_STATE, ZONE_TYPES } from '../../utils/constants'

/** Admins (and librarians the admin has allowed) maintain zones and seats here. */
export default function ManageSeatsPage() {
  const floors = useApiQuery(libraryService.floors, [])
  const zones = useApiQuery(() => seatService.zones(), [])
  const [zoneId, setZoneId] = useState(null)
  const [dialog, setDialog] = useState(null) // { type, seat?, zone? }

  const zone = zones.data?.find((item) => item.id === zoneId) ?? zones.data?.[0] ?? null
  const seats = useApiQuery(
    () => seatService.list({ zone: zone.id, page_size: 200 }), [zone?.id],
    { enabled: Boolean(zone), keepPrevious: true },
  )
  // Each table's state, worked out by the server from its seats and reservations.
  const tables = useApiQuery(
    () => seatService.tables(zone.id), [zone?.id],
    { enabled: Boolean(zone), keepPrevious: true },
  )

  const close = () => setDialog(null)
  const reload = () => {
    close()
    floors.refetch()
    zones.refetch()
    seats.refetch()
    tables.refetch()
  }

  const [removeSeat, removingSeat] = useAction((seat) => seatService.remove(seat.id), {
    success: 'Seat deleted.', onSuccess: reload, onError: close,
  })
  const [removeZone, removingZone] = useAction((target) => seatService.deleteZone(target.id), {
    success: 'Zone deleted.', onSuccess: () => { setZoneId(null); reload() }, onError: close,
  })

  const columns = [
    { key: 'number', header: 'Seat', primary: true, render: (seat) => <span className="strong">{seat.number}</span> },
    {
      key: 'position', header: 'Position',
      render: (seat) => (seat.table_number && seat.number.includes('-')
        ? `Chair ${seat.number.split('-').pop()}`
        : `Row ${seat.row}, column ${seat.col}`),
    },
    {
      key: 'features', header: 'Features',
      render: (seat) => {
        const names = SEAT_FEATURES.filter((feature) => seat[feature.key]).map((feature) => feature.label)
        return names.length ? names.join(', ') : <span className="muted">None</span>
      },
    },
    {
      key: 'status', header: 'Status',
      render: (seat) => (
        <span title={seat.status_note || undefined}>
          <Badge tone={RESOURCE_STATUS[seat.status].tone} dot>{RESOURCE_STATUS[seat.status].label}</Badge>
        </span>
      ),
    },
    {
      key: 'actions', header: 'Actions',
      render: (seat) => (
        <>
          <Button size="sm" variant="secondary" icon={Pencil} onClick={() => setDialog({ type: 'seat', seat })}>Edit</Button>
          <Button size="sm" variant="secondary" icon={Wrench} onClick={() => setDialog({ type: 'status', seat })}>Availability</Button>
          <Button size="sm" variant="danger-soft" icon={Trash2} aria-label={`Delete seat ${seat.number}`}
            onClick={() => setDialog({ type: 'delete-seat', seat })} />
        </>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Manage Seats"
        description="The library's seating areas: place seats and tables on the map, and take seats out of service."
        actions={(
          <Button icon={Plus} onClick={() => setDialog({ type: 'zone' })} disabled={!floors.data?.length}>Add zone</Button>
        )}
      />

      <QueryBoundary query={zones} loadingLabel="Loading zones...">
        {(zoneList) => (zoneList.length === 0 ? (
          <div className="card">
            <EmptyState icon={Armchair} title="No seating zones yet"
              description={floors.data?.length
                ? 'Add a zone, then place seats in it.'
                : 'Run "python manage.py setup_library" to create the library layout.'}
              action={floors.data?.length > 0
                && <Button icon={Plus} onClick={() => setDialog({ type: 'zone' })}>Add zone</Button>} />
          </div>
        ) : (
          <div className="stack-lg">
            <div className="zone-list">
              {zoneList.map((item) => (
                <button key={item.id} type="button" onClick={() => setZoneId(item.id)}
                  className={`zone-card ${item.id === zone.id ? 'is-active' : ''}`} aria-pressed={item.id === zone.id}>
                  <span className="strong">{item.name}</span>
                  <span className="muted small">{item.floor_detail.name} · {ZONE_TYPES[item.zone_type]}</span>
                  <span className="small">
                    {item.zone_type === 'computer' ? `${item.seat_count} computers` : `${item.seat_count} seats`}
                  </span>
                </button>
              ))}
            </div>

            <Card
              title={zone.name}
              subtitle={`${zone.floor_detail.name} · ${ZONE_TYPES[zone.zone_type]}`}
              padded={false}
              action={(
                <div className="row-wrap">
                  <Button size="sm" variant="secondary" icon={Pencil} onClick={() => setDialog({ type: 'zone', zone })}>Edit zone</Button>
                  <Button size="sm" variant="danger-soft" icon={Trash2} onClick={() => setDialog({ type: 'delete-zone', zone })}>Delete</Button>
                  <Button size="sm" icon={Plus} onClick={() => setDialog({ type: 'seat' })}>Add seat</Button>
                </div>
              )}
            >
              <QueryBoundary query={seats} loadingLabel="Loading seats...">
                {(data) => (data.results.length === 0 ? (
                  <EmptyState icon={Armchair} title="This zone has no seats yet"
                    description="Add seats and give each a position on the zone's grid."
                    action={<Button icon={Plus} onClick={() => setDialog({ type: 'seat' })}>Add seat</Button>} />
                ) : (
                  <>
                    <div className="seat-zones">
                      <p className="small muted" style={{ marginBottom: 12 }}>
                        Layout preview. Select a seat to edit it.
                      </p>
                      <SeatMap
                        zone={{
                          ...zone,
                          seats: data.results.map((seat) => ({
                            ...seat, state: seat.status === 'active' ? 'available' : 'unavailable',
                          })),
                        }}
                        onSelect={(seat) => setDialog({ type: 'seat', seat })}
                        onSelectTable={(table) => setDialog({ type: 'table', number: table.number })}
                        tablesAlwaysEnabled
                      />
                    </div>
                    {(tables.data ?? []).length > 0 && (
                      <div className="table-groups">
                        {tables.data.map((table) => {
                          const state = TABLE_STATE[table.state]
                          const rows = data.results.filter((seat) => seat.table_number === table.table_number)
                          return (
                            <section key={table.table_number} className="table-group"
                              aria-label={`Table ${table.table_number}`}>
                              <header className="table-group__header">
                                <h3 className="table-group__title">Table {table.table_number}</h3>
                                <Badge tone={state.tone} dot>{state.label}</Badge>
                                <span className="table-group__meta">
                                  {table.available_seats} of {table.total_seats} in service
                                  {table.reservations.length > 0
                                    && ` · ${table.reservations.length} reservation${table.reservations.length === 1 ? '' : 's'}`}
                                </span>
                                <span className="table-group__action">
                                  <Button size="sm" variant="secondary" icon={Wrench}
                                    onClick={() => setDialog({ type: 'table', number: table.table_number })}>
                                    Manage table
                                  </Button>
                                </span>
                              </header>
                              <DataTable columns={columns} rows={rows} caption={`Seats of table ${table.table_number}`} />
                            </section>
                          )
                        })}
                      </div>
                    )}
                    {data.results.some((seat) => !seat.table_number) && (
                      <DataTable columns={columns} rows={data.results.filter((seat) => !seat.table_number)}
                        caption={`Seats in ${zone.name}`} />
                    )}
                  </>
                ))}
              </QueryBoundary>
            </Card>
          </div>
        ))}
      </QueryBoundary>

      {dialog?.type === 'zone' && (
        <ZoneFormModal zone={dialog.zone} floors={floors.data ?? []} onClose={close}
          onSaved={(saved) => { setZoneId(saved.id); reload() }} />
      )}
      {dialog?.type === 'seat' && (
        <SeatFormModal seat={dialog.seat} zone={zone} onClose={close} onSaved={reload} />
      )}
      {dialog?.type === 'status' && (
        <SeatStatusDialog seat={dialog.seat} onClose={close} onSaved={reload} />
      )}
      {dialog?.type === 'table' && (
        <TableStatusDialog zoneId={zone.id} tableNumber={dialog.number} onClose={close} onSaved={reload} />
      )}
      <ConfirmDialog
        open={dialog?.type === 'delete-seat'} onClose={close} busy={removingSeat}
        onConfirm={() => removeSeat(dialog.seat)} title={`Delete seat ${dialog?.seat?.number}?`}
        confirmLabel="Delete seat"
      >
        <p>
          The seat is removed from the map. A seat that has ever been reserved cannot be deleted
          (its history is kept); mark it out of service instead.
        </p>
      </ConfirmDialog>
      <ConfirmDialog
        open={dialog?.type === 'delete-zone'} onClose={close} busy={removingZone}
        onConfirm={() => removeZone(dialog.zone)} title={`Delete ${dialog?.zone?.name}?`}
        confirmLabel="Delete zone"
      >
        <p>Only a zone with no seats can be deleted. Remove or move its seats first.</p>
      </ConfirmDialog>
    </>
  )
}
