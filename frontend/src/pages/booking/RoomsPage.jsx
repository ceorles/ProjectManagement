import { CircleAlert, DoorOpen } from 'lucide-react'
import Card from '../../components/common/Card'
import { EmptyState, QueryBoundary } from '../../components/common/Feedback'
import { Checkbox } from '../../components/common/FormControls'
import PageHeader from '../../components/common/PageHeader'
import BookingWindowPicker from '../../components/reservations/BookingWindowPicker'
import '../../components/reservations/reservations.css'
import RoomCard from '../../components/rooms/RoomCard'
import '../../components/rooms/rooms.css'
import { POLL } from '../../config'
import { useApiQuery } from '../../hooks/useApiQuery'
import { useAuth } from '../../hooks/useAuth'
import { useBookingWindow } from '../../hooks/useBookingWindow'
import { useFormDraft } from '../../hooks/useFormDraft'
import { useLibrary } from '../../hooks/useLibrary'
import { roomService } from '../../services'
import { formatDate, formatTimeRange } from '../../utils/datetime'

/** Browse study rooms and see which are free for a chosen time. */
export default function RoomsPage() {
  const { isStaff } = useAuth()
  const { floors } = useLibrary()
  // The chosen time is shared with the room page, so it carries over.
  const { window, setWindow, params, end } = useBookingWindow('room-window', 'room')
  const filters = useFormDraft('room-filters', { floor: '', people: '', availableOnly: false })
  const { floor, people, availableOnly } = filters.values

  const availability = useApiQuery(
    () => roomService.availability({ ...params, floor }),
    [params?.date, params?.start, params?.end, floor],
    { interval: POLL.availability, enabled: Boolean(params), keepPrevious: true },
  )

  const visible = (rooms) => rooms.filter((room) => (
    (!people || room.capacity >= Number(people))
    && (!availableOnly || room.state === 'available')
  ))

  return (
    <>
      <PageHeader
        title="Study Rooms"
        description={isStaff
          ? 'Live view of every study room. Open a room to see its schedule or reserve it for a student.'
          : 'Choose when your group wants to meet, then pick a room that is free.'}
      />

      <Card title="When do you need a room?" icon={DoorOpen}>
        <BookingWindowPicker resourceType="room" window={window} onChange={setWindow} />
      </Card>

      <div className="room-filters">
        <select className="input select" aria-label="Floor" value={floor}
          onChange={(event) => filters.setField('floor', event.target.value)}>
          <option value="">All floors</option>
          {floors.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
        <select className="input select" aria-label="Group size" value={people}
          onChange={(event) => filters.setField('people', event.target.value)}>
          <option value="">Any group size</option>
          {[2, 4, 6, 8, 10].map((size) => <option key={size} value={size}>Fits {size} or more</option>)}
        </select>
        <Checkbox label="Only show available rooms" checked={availableOnly}
          onChange={(event) => filters.setField('availableOnly', event.target.checked)} />
      </div>

      {!params ? (
        <EmptyState icon={DoorOpen} title="Nothing to show yet"
          description="There is no bookable time in the coming days." />
      ) : (
        <QueryBoundary query={availability} loadingLabel="Loading study rooms...">
          {(data) => {
            const rooms = visible(data.rooms)
            return (
              <div className="stack">
                {!data.bookable && (
                  <p className="notice notice--warning">
                    <CircleAlert size={16} aria-hidden="true" /> {data.bookable_reason}
                  </p>
                )}
                <p className="small soft">
                  <strong>{data.summary.available}</strong> of {data.summary.total} rooms available on{' '}
                  {formatDate(window.date, { year: undefined })}, {formatTimeRange(window.start, end)}
                </p>
                {rooms.length === 0 ? (
                  <EmptyState icon={DoorOpen} title="No rooms match"
                    description="Try another time, or clear the filters to see every room." />
                ) : (
                  <div className="room-grid">
                    {rooms.map((room) => <RoomCard key={room.id} room={room} staff={isStaff} />)}
                  </div>
                )}
              </div>
            )
          }}
        </QueryBoundary>
      )}
    </>
  )
}
