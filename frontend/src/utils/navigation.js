import {
  Armchair, Bell, CalendarCheck, ChartColumn, ClipboardList, LayoutDashboard,
  ScanLine, ScrollText, Settings, SlidersHorizontal, User, Users,
} from 'lucide-react'

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
        // Reports are for the Admin only.
        ...(user.role === 'admin' ? [{ to: '/reports', label: 'Reports', icon: ChartColumn }] : []),
      ],
    },
  ]

  if (user.can_manage_resources) {
    sections.push({
      title: 'Resources',
      items: [
        { to: '/manage/seats', label: 'Manage Seats', icon: SlidersHorizontal },
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
