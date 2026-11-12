import { useState } from 'react'
import { Armchair, Layers, Pencil, Plus, Trash2, Wrench } from 'lucide-react'
import Badge from '../../components/common/Badge'
import Button from '../../components/common/Button'
import Card from '../../components/common/Card'
import ConfirmDialog from '../../components/common/ConfirmDialog'
import DataTable from '../../components/common/DataTable'
import { EmptyState, QueryBoundary } from '../../components/common/Feedback'
import PageHeader from '../../components/common/PageHeader'
import ResourceStatusDialog from '../../components/common/ResourceStatusDialog'
import '../../components/rooms/rooms.css'
import { FloorsModal, SeatFormModal, ZoneFormModal } from '../../components/seats/SeatForms'
import SeatMap from '../../components/seats/SeatMap'
import '../../components/seats/seats.css'
import { useAction } from '../../hooks/useAction'
import { useApiQuery } from '../../hooks/useApiQuery'
import { libraryService, seatService } from '../../services'
import { RESOURCE_STATUS, SEAT_FEATURES, ZONE_TYPES } from '../../utils/constants'

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

  const close = () => setDialog(null)
  const reload = () => {
    close()
    floors.refetch()
    zones.refetch()
    seats.refetch()
  }

  const [removeSeat, removingSeat] = useAction((seat) => seatService.remove(seat.id), {
    success: 'Seat deleted.', onSuccess: reload, onError: close,
  })
  const [removeZone, removingZone] = useAction((target) => seatService.deleteZone(target.id), {
    success: 'Zone deleted.', onSuccess: () => { setZoneId(null); reload() }, onError: close,
  })

  const columns = [
    { key: 'number', header: 'Seat', primary: true, render: (seat) => <span className="strong">{seat.number}</span> },
    { key: 'position', header: 'Position', render: (seat) => `Row ${seat.row}, column ${seat.col}` },
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
        description="Set up seating zones, place seats on the map, and take seats out of service."
        actions={(
          <>
            <Button variant="secondary" icon={Layers} onClick={() => setDialog({ type: 'floors' })}>Floors</Button>
            <Button icon={Plus} onClick={() => setDialog({ type: 'zone' })} disabled={!floors.data?.length}>Add zone</Button>
          </>
        )}
      />

      <QueryBoundary query={zones} loadingLabel="Loading zones...">
        {(zoneList) => (zoneList.length === 0 ? (
          <div className="card">
            <EmptyState icon={Armchair} title="No seating zones yet"
              description={floors.data?.length
                ? 'Add a zone, then place seats in it.'
                : 'Start by adding a floor, then a zone on that floor.'}
              action={floors.data?.length
                ? <Button icon={Plus} onClick={() => setDialog({ type: 'zone' })}>Add zone</Button>
                : <Button icon={Layers} onClick={() => setDialog({ type: 'floors' })}>Add a floor</Button>} />
          </div>
        ) : (
          <div className="stack-lg">
            <div className="zone-list">
              {zoneList.map((item) => (
                <button key={item.id} type="button" onClick={() => setZoneId(item.id)}
                  className={`zone-card ${item.id === zone.id ? 'is-active' : ''}`} aria-pressed={item.id === zone.id}>
                  <span className="strong">{item.name}</span>
                  <span className="muted small">{item.floor_detail.name} · {ZONE_TYPES[item.zone_type]}</span>
                  <span className="small">{item.seat_count} seats · {item.rows} x {item.cols} grid</span>
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
                      />
                    </div>
                    <DataTable columns={columns} rows={data.results} caption={`Seats in ${zone.name}`} />
                  </>
                ))}
              </QueryBoundary>
            </Card>
          </div>
        ))}
      </QueryBoundary>

      {dialog?.type === 'floors' && (
        <FloorsModal floors={floors.data ?? []} onClose={close} onChanged={() => floors.refetch()} />
      )}
      {dialog?.type === 'zone' && (
        <ZoneFormModal zone={dialog.zone} floors={floors.data ?? []} onClose={close}
          onSaved={(saved) => { setZoneId(saved.id); reload() }} />
      )}
      {dialog?.type === 'seat' && (
        <SeatFormModal seat={dialog.seat} zone={zone} onClose={close} onSaved={reload} />
      )}
      {dialog?.type === 'status' && (
        <ResourceStatusDialog
          name={`Seat ${dialog.seat.number}`} current={dialog.seat.status} note={dialog.seat.status_note}
          save={(data) => seatService.setStatus(dialog.seat.id, data)} onClose={close} onSaved={reload}
        />
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
