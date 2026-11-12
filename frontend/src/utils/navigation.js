import {
  Armchair, Bell, Building2, CalendarCheck, ChartColumn, ClipboardList, DoorOpen, LayoutDashboard,
  ScanLine, ScrollText, Settings, SlidersHorizontal, User, Users,
} from 'lucide-react'

/**
 * Sidebar sections for a user. Hiding a link here is only for convenience:
 * the routes are guarded separately and the backend checks every request.
 */
export function navigationFor(user) {
  const account = {
    title: 'Account',
    items: [
      { to: '/notifications', label: 'Notifications', icon: Bell, badge: 'notifications' },
      { to: '/profile', label: 'Profile', icon: User },
    ],
  }

  if (user.role === 'student') {
    return [
      {
        title: 'Reserve',
        items: [
          { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
          { to: '/seats', label: 'Reserve a Seat', icon: Armchair },
          { to: '/rooms', label: 'Study Rooms', icon: DoorOpen },
          { to: '/reservations', label: 'My Reservations', icon: CalendarCheck },
        ],
      },
      account,
    ]
  }

  const sections = [
    {
      title: 'Operations',
      items: [
        { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/desk', label: 'Check-in Desk', icon: ScanLine },
        { to: '/manage/reservations', label: 'Reservations', icon: ClipboardList },
        { to: '/seats', label: 'Seat Map', icon: Armchair },
        { to: '/rooms', label: 'Study Rooms', icon: DoorOpen },
        { to: '/reports', label: 'Reports', icon: ChartColumn },
      ],
    },
  ]

  if (user.can_manage_resources) {
    sections.push({
      title: 'Resources',
      items: [
        { to: '/manage/seats', label: 'Manage Seats', icon: SlidersHorizontal },
        { to: '/manage/rooms', label: 'Manage Rooms', icon: Building2 },
      ],
    })
  }

  if (user.role === 'admin') {
    sections.push({
      title: 'Administration',
      items: [
        { to: '/admin/users', label: 'Users', icon: Users },
        { to: '/admin/settings', label: 'Library Settings', icon: Settings },
        { to: '/admin/activity', label: 'Activity Log', icon: ScrollText },
      ],
    })
  }

  sections.push(account)
  return sections
}
