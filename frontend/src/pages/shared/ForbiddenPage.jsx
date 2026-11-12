import { ShieldCheck } from 'lucide-react'
import Button from '../../components/common/Button'
import { EmptyState } from '../../components/common/Feedback'

/** Shown when a signed-in user opens a page their role may not use. */
export default function ForbiddenPage() {
  return (
    <EmptyState
      icon={ShieldCheck}
      title="You do not have access to this page"
      description="This part of the portal is limited to other roles. If you think this is a mistake, contact the library administrator."
      action={<Button to="/dashboard">Go to my dashboard</Button>}
    />
  )
}
