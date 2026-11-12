import { useState } from 'react'
import { Hourglass, ScanLine, Search, UserCheck } from 'lucide-react'
import Button from '../../components/common/Button'
import Card from '../../components/common/Card'
import { EmptyState, QueryBoundary } from '../../components/common/Feedback'
import { FormError } from '../../components/common/FormControls'
import PageHeader from '../../components/common/PageHeader'
import ReservationCard from '../../components/reservations/ReservationCard'
import '../../components/reservations/reservations.css'
import { POLL } from '../../config'
import { useApiQuery } from '../../hooks/useApiQuery'
import { reportService, reservationService } from '../../services'

/**
 * The librarian's desk. Type the code a student shows (or scan its QR code
 * with a handheld scanner, which types it into the box) to bring up the
 * reservation and confirm the check-in.
 */
export default function CheckInDeskPage() {
  const [code, setCode] = useState('')
  const [found, setFound] = useState(null)
  const [error, setError] = useState(null)
  const [searching, setSearching] = useState(false)
  const lists = useApiQuery(reportService.staffDashboard, [], {
    interval: POLL.reservations, keepPrevious: true,
  })

  const lookup = async (event) => {
    event.preventDefault()
    const entered = code.replace(/\s+/g, '')
    if (!entered || searching) return
    setSearching(true)
    setError(null)
    try {
      setFound(await reservationService.lookup(entered))
    } catch (failure) {
      setFound(null)
      setError(failure.status === 404 ? `No reservation has the code "${entered.toUpperCase()}".` : failure)
    } finally {
      setSearching(false)
    }
  }

  // After an action, show the reservation's new state and refresh the lists.
  const refreshFound = async () => {
    lists.refetch()
    if (!found) return
    try {
      setFound(await reservationService.get(found.id))
    } catch {
      setFound(null)
    }
  }

  return (
    <>
      <PageHeader
        title="Check-in Desk"
        description="Find a reservation by its code and confirm the student's arrival."
      />
      <div className="stack-lg">
        <Card title="Find a reservation" icon={ScanLine}>
          <div className="stack">
            <form className="desk-form" onSubmit={lookup}>
              <input
                className="input" value={code} onChange={(event) => setCode(event.target.value)}
                placeholder="Enter or scan the reservation code" aria-label="Reservation code"
                autoComplete="off" autoCapitalize="characters" spellCheck="false" maxLength={12} autoFocus
              />
              <Button type="submit" size="lg" icon={Search} loading={searching} disabled={!code.trim()}>
                Find
              </Button>
            </form>
            <FormError error={error} />
            {found && (
              <div className="stack-sm">
                <ReservationCard reservation={found} onChanged={refreshFound} showStudent />
                <button type="button" className="link-button small" style={{ alignSelf: 'flex-start' }}
                  onClick={() => { setFound(null); setCode('') }}>
                  Clear and find another
                </button>
              </div>
            )}
          </div>
        </Card>

        <QueryBoundary query={lists} loadingLabel="Loading today's reservations...">
          {(data) => (
            <div className="split split--even">
              <Card title="Awaiting check-in" icon={Hourglass}
                subtitle="Started, but the student has not arrived yet">
                {data.awaiting_check_in.length === 0 ? (
                  <EmptyState compact icon={UserCheck} title="Nobody is overdue"
                    description="Reservations that start without a check-in appear here." />
                ) : (
                  <div className="reservation-list">
                    {data.awaiting_check_in.map((reservation) => (
                      <ReservationCard key={reservation.id} reservation={reservation}
                        onChanged={refreshFound} showStudent />
                    ))}
                  </div>
                )}
              </Card>
              <Card title="Checked in now" icon={UserCheck} subtitle="Check students out when they leave early">
                {data.checked_in.length === 0 ? (
                  <EmptyState compact icon={UserCheck} title="No one is checked in"
                    description="Students who are currently in the library appear here." />
                ) : (
                  <div className="reservation-list">
                    {data.checked_in.map((reservation) => (
                      <ReservationCard key={reservation.id} reservation={reservation}
                        onChanged={refreshFound} showStudent />
                    ))}
                  </div>
                )}
              </Card>
            </div>
          )}
        </QueryBoundary>
      </div>
    </>
  )
}
