import { ChevronRight, MapPin, Users, Wrench } from 'lucide-react'
import { Link } from 'react-router-dom'
import { AVAILABILITY } from '../../utils/constants'
import { formatTimeRange } from '../../utils/datetime'
import Badge from '../common/Badge'

/** A study room with its availability for the chosen time. */
export default function RoomCard({ room, staff = false }) {
  const state = AVAILABILITY[room.state]
  return (
    <Link to={`/rooms/${room.id}`} className={`room-card room-card--${room.state}`}>
      <div className="room-card__top">
        <div className="grow">
          <p className="room-card__code">{room.code}</p>
          <h3 className="room-card__name">{room.name}</h3>
        </div>
        <Badge tone={state.tone} dot>{state.label}</Badge>
      </div>

      <ul className="room-card__meta">
        <li><MapPin size={14} aria-hidden="true" /> {room.floor.name}</li>
        <li>
          <Users size={14} aria-hidden="true" />
          {room.min_occupancy === room.capacity
            ? `${room.capacity} people`
            : `${room.min_occupancy}-${room.capacity} people`}
        </li>
      </ul>

      {room.description && <p className="room-card__description">{room.description}</p>}

      {room.facilities.length > 0 && (
        <div className="chips">
          {room.facilities.slice(0, 4).map((name) => <span key={name} className="chip">{name}</span>)}
          {room.facilities.length > 4 && <span className="chip">+{room.facilities.length - 4}</span>}
        </div>
      )}

      {room.state === 'unavailable' && (
        <p className="room-card__note">
          <Wrench size={14} aria-hidden="true" /> {room.status_note || 'Out of service'}
        </p>
      )}
      {room.blocks.length > 0 && (
        <p className="room-card__note">
          Booked {room.blocks.map((block) => formatTimeRange(block.start_time, block.end_time)).join(', ')}
          {staff && room.blocks[0].student_name && ` · ${room.blocks[0].student_name}`}
        </p>
      )}

      <span className="room-card__cta">
        {room.state === 'available' ? 'View and reserve' : 'View schedule'}
        <ChevronRight size={16} aria-hidden="true" />
      </span>
    </Link>
  )
}
