import { useState } from 'react'
import { DoorOpen, Pencil, Plus, Trash2, Wrench } from 'lucide-react'
import { Link } from 'react-router-dom'
import Badge from '../../components/common/Badge'
import Button from '../../components/common/Button'
import ConfirmDialog from '../../components/common/ConfirmDialog'
import DataTable from '../../components/common/DataTable'
import { EmptyState, QueryBoundary } from '../../components/common/Feedback'
import { SearchInput } from '../../components/common/FormControls'
import PageHeader from '../../components/common/PageHeader'
import ResourceStatusDialog from '../../components/common/ResourceStatusDialog'
import RoomFormModal from '../../components/rooms/RoomFormModal'
import '../../components/rooms/rooms.css'
import { useAction } from '../../hooks/useAction'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useDebounce } from '../../hooks/useDebounce'
import { libraryService, roomService } from '../../services'
import { RESOURCE_STATUS } from '../../utils/constants'

/** Admins (and librarians the admin has allowed) maintain study rooms here. */
export default function ManageRoomsPage() {
  const [search, setSearch] = useState('')
  const term = useDebounce(search.trim())
  const rooms = useApiQuery(() => roomService.list({ search: term, page_size: 100 }), [term], { keepPrevious: true })
  const floors = useApiQuery(libraryService.floors, [])
  const facilities = useApiQuery(roomService.facilities, [])
  const [dialog, setDialog] = useState(null) // { type, room? }

  const close = () => setDialog(null)
  const reload = () => {
    close()
    rooms.refetch()
  }
  const [remove, removing] = useAction((room) => roomService.remove(room.id), {
    success: 'Study room deleted.', onSuccess: reload, onError: close,
  })

  const columns = [
    {
      key: 'name', header: 'Room', primary: true,
      render: (room) => (
        <>
          <Link to={`/rooms/${room.id}`} className="strong">{room.name}</Link>
          <span className="muted small"> · {room.code}</span>
        </>
      ),
    },
    { key: 'floor', header: 'Floor', render: (room) => room.floor_detail.name },
    { key: 'capacity', header: 'Group size', render: (room) => `${room.min_occupancy}-${room.capacity} people` },
    {
      key: 'facilities', header: 'Facilities',
      render: (room) => (room.facility_details.length
        ? `${room.facility_details.length} facilities`
        : <span className="muted">None</span>),
    },
    {
      key: 'status', header: 'Status',
      render: (room) => (
        <span title={room.status_note || undefined}>
          <Badge tone={RESOURCE_STATUS[room.status].tone} dot>{RESOURCE_STATUS[room.status].label}</Badge>
        </span>
      ),
    },
    {
      key: 'actions', header: 'Actions',
      render: (room) => (
        <>
          <Button size="sm" variant="secondary" icon={Pencil} onClick={() => setDialog({ type: 'form', room })}>Edit</Button>
          <Button size="sm" variant="secondary" icon={Wrench} onClick={() => setDialog({ type: 'status', room })}>Availability</Button>
          <Button size="sm" variant="danger-soft" icon={Trash2} aria-label={`Delete ${room.name}`}
            onClick={() => setDialog({ type: 'delete', room })} />
        </>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Manage Study Rooms"
        description="Add rooms, describe their facilities, and take rooms out of service."
        actions={(
          <Button icon={Plus} onClick={() => setDialog({ type: 'form' })} disabled={!floors.data?.length}>
            Add room
          </Button>
        )}
      />

      <section className="card">
        <div className="toolbar">
          <SearchInput value={search} onChange={setSearch} placeholder="Search by room name or number" />
        </div>
        <QueryBoundary query={rooms} loadingLabel="Loading study rooms...">
          {(data) => (data.results.length === 0 ? (
            <EmptyState
              icon={DoorOpen}
              title={term ? 'No rooms match your search' : 'No study rooms yet'}
              description={term ? 'Try another name or room number.' : 'Add the first study room so students can reserve it.'}
              action={!term && floors.data?.length > 0 && (
                <Button icon={Plus} onClick={() => setDialog({ type: 'form' })}>Add room</Button>
              )}
            />
          ) : (
            <DataTable columns={columns} rows={data.results} caption="Study rooms" />
          ))}
        </QueryBoundary>
      </section>

      {dialog?.type === 'form' && (
        <RoomFormModal
          room={dialog.room} floors={floors.data ?? []} facilities={facilities.data ?? []}
          onClose={close} onSaved={reload} onFacilityAdded={facilities.refetch}
        />
      )}
      {dialog?.type === 'status' && (
        <ResourceStatusDialog
          name={dialog.room.name} current={dialog.room.status} note={dialog.room.status_note}
          save={(data) => roomService.setStatus(dialog.room.id, data)} onClose={close} onSaved={reload}
        />
      )}
      <ConfirmDialog
        open={dialog?.type === 'delete'} onClose={close} busy={removing}
        onConfirm={() => remove(dialog.room)} title={`Delete ${dialog?.room?.name}?`}
        confirmLabel="Delete room"
      >
        <p>
          A room that has ever been reserved cannot be deleted (its history is kept); mark it out
          of service instead.
        </p>
      </ConfirmDialog>
    </>
  )
}
