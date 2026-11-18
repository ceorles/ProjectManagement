# Functional Requirements of the Library Seat & Study Room Reservation Portal

Stakeholder: the School Library  
Date: November 18, 2026  
Total functional requirements: 139

This document lists the functional requirements of the Library Seat & Study Room Reservation Portal of DLL Library (Dalubhasaan ng Lungsod ng Lucena), a web application that lets students request library seats, whole tables and computers, and lets the library staff review and manage those requests. It also includes a public website with the library's information. The requirements describe the system as it is implemented. They reflect the actual library: one floor (First Floor), a Reading Hall with 15 tables of 6 chairs (90 seats) and a Computer Area with 4 computers.

## User Roles

| Role | Description |
|---|---|
| Admin | Manages accounts, library settings and seating, and has access to every function. |
| Librarian | Approves or rejects reservation requests and runs daily library operations. |
| Student Assistant | A student who helps the Librarian monitor seats and check students in. |
| Student | Requests seats, tables or computers and manages own reservations. |

## 1. User Authentication and Account Management

| ID | Functional Requirement | Description |
|---|---|---|
| FR-001 | Student Registration | Students can create their own account using their name, email, student ID and a password. |
| FR-002 | User Login | Registered users can log in with their email address and password. |
| FR-003 | User Logout | Users can log out, which ends their session on that device. |
| FR-004 | Session Persistence | A logged-in user stays logged in after refreshing or reopening the page. |
| FR-005 | Expired Session Handling | When a session expires, the system asks the user to log in again and returns them to the page they were on. |
| FR-006 | Role-Based Redirection After Login | After logging in, each user is taken to the dashboard of their own role, never to a page left open by the previous user. |
| FR-007 | Password Rules | The system rejects passwords that are too short, too common or made of numbers only. |
| FR-008 | Login Attempt Limiting | The system limits repeated login and registration attempts to protect accounts. |
| FR-009 | Account Creation by Admin | The Admin can create Librarian, Student Assistant, Student and Admin accounts. |
| FR-010 | Account Editing | The Admin can edit the details and role of an existing account. |
| FR-011 | Account Deactivation | The Admin can deactivate an account so that its owner can no longer log in. |
| FR-012 | Account Reactivation | The Admin can reactivate a deactivated account. |
| FR-013 | Password Reset by Admin | The Admin can set a new password for a user who forgot theirs. |
| FR-014 | Account Search and Filtering | The Admin can search accounts by name, email or student ID and filter them by role and status. |

## 2. Role-Based Access Control

| ID | Functional Requirement | Description |
|---|---|---|
| FR-015 | User Roles | The system has four roles: Admin, Librarian, Student Assistant and Student. |
| FR-016 | Role-Based Navigation | Each user sees only the menu items and pages that their role is allowed to use. |
| FR-017 | Server-Side Permission Checks | The server checks the user's role on every request, so restricted actions cannot be done by bypassing the screen. |
| FR-018 | Restricted Page Protection | A user who opens a page that their role may not use sees a "no access" message. |
| FR-019 | No Public Staff Registration | Librarian, Student Assistant and Admin accounts cannot be created through public registration. |
| FR-020 | Student Assistant Role | Student Assistants can view the operations dashboard, the seat map and reservations, and help with check-ins. |
| FR-021 | Student Assistant Restrictions | Student Assistants cannot approve, reject or cancel reservations, manage accounts, change settings or view reports. |
| FR-022 | Seat Management Permission | The Admin can allow a specific Librarian to manage seats. |

## 3. Library Seat Management

| ID | Functional Requirement | Description |
|---|---|---|
| FR-023 | Library Layout | The system represents the actual library: the First Floor with a Reading Hall and a Computer Area. |
| FR-024 | Reading Hall Tables and Seats | The Reading Hall has 15 tables with 6 chairs each, for a total of 90 seats. |
| FR-025 | Unique Seat Identification | Every seat has a unique identifier that shows its table and chair number, such as T03-2. |
| FR-026 | Seat Map | The system shows seats on a visual map where chairs of the same table are grouped around that table. |
| FR-027 | Seat Availability Display | The seat map shows whether each seat is available, requested or reserved, occupied, or unavailable for the chosen time. |
| FR-028 | Seat Details and Daily Schedule | Users can open a seat to see its details and the times it is taken on the chosen day. |
| FR-029 | Seat Feature Highlighting | Users can highlight seats that have a power outlet or a computer. |
| FR-030 | Add, Edit and Delete Seats | Authorized staff can add a seat, edit its number, table, position and features, and delete an unused seat. |
| FR-031 | Seat Features | A seat can be marked as having a power outlet, having a computer, or being wheelchair accessible. |
| FR-032 | Seating Zone Management | Authorized staff can add, edit and delete seating zones. |
| FR-033 | Seat Maintenance Status | Authorized staff can mark a seat as under maintenance or out of service, with a note for students. |
| FR-034 | Whole-Table Availability | Authorized staff can take all six seats of a table out of service, or restore them, in one action. |
| FR-035 | Table Status Display | The system shows whether each table is fully available, partially available, reserved or out of service. |
| FR-036 | Independent Seat Availability | A seat that was out of service on its own stays out of service when its table is restored. |
| FR-037 | Reservations Affected by Maintenance | Before a seat or table is taken out of service, staff see the reservations affected and must confirm; those students are then notified. |
| FR-038 | Preservation of History | Seats and zones that are no longer used are archived instead of deleted, so past reservations remain on record. |

## 4. Reservation Scheduling Rules

| ID | Functional Requirement | Description |
|---|---|---|
| FR-039 | Date Selection | Students can choose a reservation date within the allowed number of days in advance. |
| FR-040 | Time and Duration Selection | Students can choose a start time and a duration in 30-minute steps. |
| FR-041 | Operating Hours Enforcement | The system only accepts reservations that fall within the library's opening hours. |
| FR-042 | Closure Day Enforcement | The system does not accept reservations on days when the library is closed. |
| FR-043 | Past Time Prevention | The system does not accept reservations for a date or time that has already passed. |
| FR-044 | Duration Limits | The system enforces the minimum and maximum length of a reservation. |
| FR-045 | Reservation Limits per Student | The system limits how many active reservations and how many reservations per day a student may have. |
| FR-046 | One Place at a Time | A student cannot hold two reservations that overlap in time. |
| FR-047 | Booking Suspension for Repeated No-Shows | A student who misses too many reservations within a set period cannot make new reservations. |

## 5. Seat, Table and Group Reservation

| ID | Functional Requirement | Description |
|---|---|---|
| FR-048 | Individual Seat Reservation | Students can request one available seat for a chosen date and time. |
| FR-049 | Two-Seat Reservation | Students can request up to two seats without giving a reason. |
| FR-050 | Group Seat Reservation | Students can request three to six seats in one request. |
| FR-051 | Whole-Table Reservation | Students can request an entire table of six seats with a single selection. |
| FR-052 | Reason for Group Requests | The system requires a reason when a student requests more than two seats, including a whole table. |
| FR-053 | Seat Limit per Request | One request can cover at most six seats, all in the same area. |
| FR-054 | Review Before Submitting | The system shows the selected seats, date and time for the student to review before the request is sent. |
| FR-055 | Availability Verification | The server checks that every requested seat is free before saving the request. |
| FR-056 | Double-Booking Prevention | The system prevents two reservations from holding the same seat at the same time, even when they are submitted at the same moment. |
| FR-057 | Pending Requests Hold Seats | Seats in a pending request are held so that other students cannot request them for the same time. |

## 6. Computer Reservation

| ID | Functional Requirement | Description |
|---|---|---|
| FR-058 | Computer Area | The system has a Computer Area with exactly four reservable computers, separate from the 90 seats. |
| FR-059 | Computer Reservation | Students can request one available computer for a chosen date and time. |
| FR-060 | One Computer per Request | The system does not allow more than one computer in a single reservation. |
| FR-061 | One Student per Computer | A computer can be held by only one student during a given time. |
| FR-062 | No Overlapping Computer Use | A student cannot hold two computers for overlapping times. |
| FR-063 | Approval of Computer Requests | Computer reservations follow the same Librarian approval process as seat reservations. |

## 7. Reservation Approval and Management

| ID | Functional Requirement | Description |
|---|---|---|
| FR-064 | Pending Status on Submission | Every reservation request submitted by a student is saved with the status Pending. |
| FR-065 | No Automatic Confirmation | A student's request is never shown as Confirmed until a Librarian approves it. |
| FR-066 | Request Review | The Librarian can view the student's name and ID, the date and time, the seats requested, the number of seats, the reason, the submission date and the status. |
| FR-067 | Reservation Approval | The Librarian can approve a pending request, which changes its status to Confirmed. |
| FR-068 | Reservation Rejection | The Librarian can reject a pending request, with an optional reason, which changes its status to Rejected. |
| FR-069 | Approval Authority | Only a Librarian or the Admin can approve or reject reservation requests. |
| FR-070 | Release of Rejected Requests | When a request is rejected, its seats become available to other students again. |
| FR-071 | Expiry of Unreviewed Requests | A request that is not reviewed before its reserved time is cancelled automatically and its seats are released. |
| FR-072 | Withdrawing a Request | A student can withdraw their own pending request at any time. |
| FR-073 | Cancellation by Student | A student can cancel their own confirmed reservation before it starts. |
| FR-074 | Cancellation by Staff | A Librarian or the Admin can cancel a reservation and give the student a reason. |
| FR-075 | Reservation on Behalf of a Student | A Librarian or the Admin can make a reservation for a student, which is confirmed immediately. |
| FR-076 | Reservation Status Tracking | Each reservation has a status: Pending, Confirmed, Checked in, Completed, Cancelled, Rejected or No-show. |
| FR-077 | My Reservations | Students can view their upcoming reservations and their reservation history. |
| FR-078 | Reservation Details | Users can open a reservation to see its details, its status and the history of what happened to it. |
| FR-079 | Reservation List for Staff | Library staff can view all reservations and search or filter them by student, code, date, status and type. |
| FR-080 | Reservation Code | Every reservation receives a unique reference code. |

## 8. Notifications

| ID | Functional Requirement | Description |
|---|---|---|
| FR-081 | New Request Notification to Librarians | The system notifies every Librarian when a student submits a reservation request. |
| FR-082 | New Request Notification to Admin | The system also notifies the Admin when a student submits a reservation request. |
| FR-083 | Request Received Notification | The student is notified that their request was sent and is waiting for approval. |
| FR-084 | Approval Notification | The student is notified when their request is approved. |
| FR-085 | Rejection Notification | The student is notified when their request is rejected, together with the reason given. |
| FR-086 | Cancellation and Expiry Notifications | The student is notified when their reservation is cancelled or their request expires. |
| FR-087 | Reminder Notification | The student is reminded shortly before a confirmed reservation starts. |
| FR-088 | Check-in and No-Show Notifications | The student is notified when they are checked in and when a reservation is marked as a no-show. |
| FR-089 | Unread Notification Count | The system shows the number of unread notifications on the notification bell and in the menu. |
| FR-090 | Notification List | Users can view their notifications, mark them as read and delete them. |
| FR-091 | Link to Reservation | Selecting a notification opens the reservation it refers to. |
| FR-092 | Stored Notifications | Notifications are saved in the database and remain available after the page is refreshed. |

## 9. Check-in and Library Operations

| ID | Functional Requirement | Description |
|---|---|---|
| FR-093 | Student Self Check-in | A student can check in to their confirmed reservation during the check-in period. |
| FR-094 | Check-in Period | Check-in opens shortly before the start time and closes exactly 15 minutes after the start time. |
| FR-095 | Check-in Code | A confirmed reservation shows its code as text and as a QR code for the student to present. |
| FR-096 | Check-in Desk | Library staff can find a reservation by entering its code and confirm the student's arrival. |
| FR-097 | Check-in by Staff | A Librarian, a Student Assistant or the Admin can check a student in. |
| FR-098 | Check-out | A student or a staff member can check out, which ends the reservation and frees the seat. |
| FR-099 | Automatic Completion | A checked-in reservation is completed automatically when its end time is reached. |
| FR-100 | Automatic No-Show Cancellation | The server automatically cancels a confirmed reservation as a no-show when nobody checks in within 15 minutes of the start time. |
| FR-101 | Release After No-Show | All seats or the computer of a no-show reservation become available to other students for the remaining time. |
| FR-102 | No-Show Notification | The student is notified that the reservation was automatically cancelled and why. |
| FR-103 | Manual No-Show | A Librarian or the Admin can mark a reservation as a no-show after it has started. |
| FR-104 | Live Occupancy Monitoring | Library staff can see how many seats and computers are occupied, reserved, available and unavailable. |
| FR-105 | Occupant Information for Staff | Library staff can see which student has requested or is using a seat. |

## 10. Dashboards and Reports

| ID | Functional Requirement | Description |
|---|---|---|
| FR-106 | Student Dashboard | Students see their current and upcoming reservations, their statistics, current availability and their booking standing. |
| FR-107 | Operations Dashboard | Librarians and Student Assistants see pending requests, today's reservations, students checked in and those awaiting check-in. |
| FR-108 | Pending Request Count | The operations dashboard shows how many requests are waiting for approval. |
| FR-109 | Admin Dashboard | The Admin sees totals of accounts, seats and reservations, current occupancy, trends and recent activity. |
| FR-110 | Usage Reports | Librarians and the Admin can view reservation totals, daily trends, busiest times, most-used seats and outcomes for a chosen period. |
| FR-111 | Report Table View | Each chart in the reports can also be shown as a table of numbers. |
| FR-112 | Activity Log | The Admin can view a record of logins, reservation actions and changes to accounts, seats and settings. |
| FR-113 | Activity Log Filtering | The Admin can search the activity log and filter it by area and date. |

## 11. Library Settings

| ID | Functional Requirement | Description |
|---|---|---|
| FR-114 | Operating Hours Management | The Admin can set the opening and closing time for each day of the week. |
| FR-115 | Closure Day Management | The Admin can add and remove days on which the library is closed. |
| FR-116 | Reservation Rule Configuration | The Admin can set booking limits, durations, the advance-booking period, check-in times and the no-show limit. |
| FR-117 | Self Check-in Setting | The Admin can turn student self check-in on or off. |
| FR-118 | Reservations Affected by Schedule Changes | When hours change or a closure is added, reservations that no longer fit are cancelled and the students are notified. |

## 12. Profile Management

| ID | Functional Requirement | Description |
|---|---|---|
| FR-119 | View Profile | Users can view their own account details and role. |
| FR-120 | Update Profile | Users can update their name, mobile number, program and year level. |
| FR-121 | Change Password | Users can change their password by entering their current password and a new one. |

## 13. Public Website (Landing Page)

| ID | Functional Requirement | Description |
|---|---|---|
| FR-122 | Public Landing Page | Visitors can open the DLL Library website without logging in. |
| FR-123 | Landing Page Navigation | The website header has Home, Our Services, About and Contact links, an Install button and a Login button. |
| FR-124 | Library Information Display | The website shows the library name, tagline, introduction, services, library card requirements, rules and personnel. |
| FR-125 | Library Hours Display | The website shows the library hours from the same opening hours setting used for reservations. |
| FR-126 | Contact Information Display | The website shows the library's address, telephone, email and Facebook page. |
| FR-127 | Back to Website from Login | The login page has a Back button that returns to the website when it is opened in a browser. |
| FR-128 | Library Information Management | The Admin can edit the library name, tagline, introduction and contact information in Library Settings. |
| FR-129 | Landing Page Content Management | The Admin can add, edit, reorder and remove library services, library card steps, rules, personnel and library photos. |
| FR-130 | Personnel and Library Photos | The Admin can upload a photo for each library staff member and photos of the library for the website. |
| FR-131 | Read-Only Public Content | Visitors and non-admin users can read the website content but cannot change it. |

## 14. Other System Functions

| ID | Functional Requirement | Description |
|---|---|---|
| FR-132 | Automatic Data Refresh | Seat availability, dashboards and notifications refresh automatically every few seconds. |
| FR-133 | Form Draft Preservation | Information entered in a form is kept when the page is refreshed and cleared after submission or logout. |
| FR-134 | Responsive Layout | The system adapts to desktop, laptop, tablet and mobile screens, with a menu button on smaller screens. |
| FR-135 | Installable Application | Users can install the system on a phone or computer from the Install button on the landing page or in the sidebar; instructions are shown when the browser does not offer installation. |
| FR-136 | Installed App Start | The installed app opens directly on the login page, or on the user's dashboard when already logged in, without showing the public website. |
| FR-137 | Installed App Session | Users of the installed app stay logged in after closing and reopening it, until they log out or the session expires. |
| FR-138 | Offline Notice | When there is no connection, the system says so and does not allow reservation actions until the connection returns. |
| FR-139 | Action Confirmation | The system asks for confirmation before actions such as cancelling, rejecting or deactivating. |
