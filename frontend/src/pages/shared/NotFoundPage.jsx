import { Search } from 'lucide-react'
import Button from '../../components/common/Button'
import { EmptyState } from '../../components/common/Feedback'

export default function NotFoundPage() {
  return (
    <EmptyState
      icon={Search}
      title="Page not found"
      description="The page you are looking for does not exist or has been moved."
      action={<Button to="/dashboard">Go to my dashboard</Button>}
    />
  )
}
