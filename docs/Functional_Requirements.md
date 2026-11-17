# Functional Requirements of the Library Seat & Study Room Reservation Portal

Stakeholder: the School Library  
Date: November 16, 2026  
Total functional requirements: 127

This document lists the functional requirements of the Library Seat & Study Room Reservation Portal, a web application that lets students request library seats, tables, computers and the study room, and lets the library staff review and manage those requests. The requirements describe the system as it is implemented. They reflect the actual library: one floor (First Floor), a Reading Hall with 15 tables of 6 chairs (90 seats), a Computer Area with 4 computers, and one study room.

## User Roles

| Role | Description |
|---|---|
| Admin | Manages accounts, library settings and seating, and has access to every function. |
| Librarian | Approves or rejects reservation requests and runs daily library operations. |
| Student Assistant | A student who helps the Librarian monitor seats and check students in. |
| Student | Requests seats, tables, computers or the study room and manages own reservations. |

## 1. User Authentication and Account Management

| ID | Functional Requirement | Description |
|---|---|---|
| FR-001 | Student Registration | Students can create their own account using their name, email, student ID and a password. |
| FR-002 | User Login | Registered users can log in with their email address and password. |
| FR-003 | User Logout | Users can log out, which ends their session on that device. |
| FR-004 | Session Persistence | A logged-in user stays logged in after refreshing or reopening the page. |
| FR-005 | Expired Session Handling | When a session expires, the system asks the user to log in again and returns them to the page they were on. |
| FR-006 | Password Rules | The system rejects passwords that are too short, too common or made of numbers only. |
| FR-007 | Login Attempt Limiting | The system limits repeated login and registration attempts to protect accounts. |
| FR-008 | Account Creation by Admin | The Admin can create Librarian, Student Assistant, Student and Admin accounts. |
| FR-009 | Account Editing | The Admin can edit the details and role of an existing account. |
| FR-010 | Account Deactivation | The Admin can deactivate an account so that its owner can no longer log in. |
| FR-011 | Account Reactivation | The Admin can reactivate a deactivated account. |
| FR-012 | Password Reset by Admin | The Admin can set a new password for a user who forgot theirs. |
| FR-013 | Account Search and Filtering | The Admin can search accounts by name, email or student ID and filter them by role and status. |

## 2. Role-Based Access Control

| ID | Functional Requirement | Description |
|---|---|---|
| FR-014 | User Roles | The system has four roles: Admin, Librarian, Student Assistant and Student. |
| FR-015 | Role-Based Navigation | Each user sees only the menu items and pages that their role is allowed to use. |
| FR-016 | Server-Side Permission Checks | The server checks the user's role on every request, so restricted actions cannot be done by bypassing the screen. |
| FR-017 | Restricted Page Protection | A user who opens a page that their role may not use sees a "no access" message. |
| FR-018 | No Public Staff Registration | Librarian, Student Assistant and Admin accounts cannot be created through public registration. |
| FR-019 | Student Assistant Role | Student Assistants can view the operations dashboard, the seat map and reservations, and help with check-ins. |
| FR-020 | Student Assistant Restrictions | Student Assistants cannot approve, reject or cancel reservations, manage accounts, change settings or view reports. |
| FR-021 | Seat Management Permission | The Admin can allow a specific Librarian to manage seats. |

## 3. Library Seat Management

| ID | Functional Requirement | Description |
|---|---|---|
| FR-022 | Library Layout | The system represents the actual library: the First Floor with a Reading Hall and a Computer Area. |
| FR-023 | Reading Hall Tables and Seats | The Reading Hall has 15 tables with 6 chairs each, for a total of 90 seats. |
| FR-024 | Unique Seat Identification | Every seat has a unique identifier that shows its table and chair number, such as T03-2. |
| FR-025 | Seat Map | The system shows seats on a visual map where chairs of the same table are grouped around that table. |
| FR-026 | Seat Availability Display | The seat map shows whether each seat is available, requested or reserved, occupied, or unavailable for the chosen time. |
| FR-027 | Seat Details and Daily Schedule | Users can open a seat to see its details and the times it is taken on the chosen day. |
| FR-028 | Seat Feature Highlighting | Users can highlight seats that have a power outlet or a computer. |
| FR-029 | Add, Edit and Delete Seats | Authorized staff can add a seat, edit its number, table, position and features, and delete an unused seat. |
| FR-030 | Seat Features | A seat can be marked as having a power outlet, having a computer, or being wheelchair accessible. |
| FR-031 | Seating Zone Management | Authorized staff can add, edit and delete seating zones. |
| FR-032 | Seat Maintenance Status | Authorized staff can mark a seat as under maintenance or out of service, with a note for students. |
| FR-033 | Reservations Affected by Maintenance | When a seat is taken out of service, its upcoming reservations are cancelled and the students are notified. |
| FR-034 | Preservation of History | Seats and zones that are no longer used are archived instead of deleted, so past reservations remain on record. |

## 4. Reservation Scheduling Rules

| ID | Functional Requirement | Description |
|---|---|---|
| FR-035 | Date Selection | Students can choose a reservation date within the allowed number of days in advance. |
| FR-036 | Time and Duration Selection | Students can choose a start time and a duration in 30-minute steps. |
| FR-037 | Operating Hours Enforcement | The system only accepts reservations that fall within the library's opening hours. |
| FR-038 | Closure Day Enforcement | The system does not accept reservations on days when the library is closed. |
| FR-039 | Past Time Prevention | The system does not accept reservations for a date or time that has already passed. |
| FR-040 | Duration Limits | The system enforces the minimum and maximum length of a reservation. |
| FR-041 | Reservation Limits per Student | The system limits how many active reservations and how many reservations per day a student may have. |
| FR-042 | One Place at a Time | A student cannot hold two reservations that overlap in time. |
| FR-043 | Booking Suspension for Repeated No-Shows | A student who misses too many reservations within a set period cannot make new reservations. |

## 5. Seat, Table and Group Reservation

| ID | Functional Requirement | Description |
|---|---|---|
| FR-044 | Individual Seat Reservation | Students can request one available seat for a chosen date and time. |
| FR-045 | Two-Seat Reservation | Students can request up to two seats without giving a reason. |
| FR-046 | Group Seat Reservation | Students can request three to six seats in one request. |
| FR-047 | Whole-Table Reservation | Students can request an entire table of six seats with a single selection. |
| FR-048 | Reason for Group Requests | The system requires a reason when a student requests more than two seats, including a whole table. |
| FR-049 | Seat Limit per Request | One request can cover at most six seats, all in the same area. |
| FR-050 | Review Before Submitting | The system shows the selected seats, date and time for the student to review before the request is sent. |
| FR-051 | Availability Verification | The server checks that every requested seat is free before saving the request. |
| FR-052 | Double-Booking Prevention | The system prevents two reservations from holding the same seat at the same time, even when they are submitted at the same moment. |
| FR-053 | Pending Requests Hold Seats | Seats in a pending request are held so that other students cannot request them for the same time. |

## 6. Computer Reservation

| ID | Functional Requirement | Description |
|---|---|---|
| FR-054 | Computer Area | The system has a Computer Area with exactly four reservable computers, separate from the 90 seats. |
| FR-055 | Computer Reservation | Students can request one available computer for a chosen date and time. |
| FR-056 | One Computer per Request | The system does not allow more than one computer in a single reservation. |
| FR-057 | One Student per Computer | A computer can be held by only one student during a given time. |
| FR-058 | No Overlapping Computer Use | A student cannot hold two computers for overlapping times. |
| FR-059 | Approval of Computer Requests | Computer reservations follow the same Librarian approval process as seat reservations. |

## 7. Study Room Reservation

| ID | Functional Requirement | Description |
|---|---|---|
| FR-060 | Study Room Availability | Users can see whether the library's study room is available for a chosen date and time. |
| FR-061 | Study Room Details and Schedule | Users can view the room's capacity, facilities and its schedule for the chosen day. |
| FR-062 | Study Room Request | Students can request the study room by giving the number of people and the purpose. |
| FR-063 | Group Size Rule | The system checks that the number of people fits the room's minimum group size and capacity. |
| FR-064 | Inviting Classmates | Students can add classmates to a room request by entering their student IDs. |

## 8. Reservation Approval and Management

| ID | Functional Requirement | Description |
|---|---|---|
| FR-065 | Pending Status on Submission | Every reservation request submitted by a student is saved with the status Pending. |
| FR-066 | No Automatic Confirmation | A student's request is never shown as Confirmed until a Librarian approves it. |
| FR-067 | Request Review | The Librarian can view the student's name and ID, the date and time, the seats requested, the number of seats, the reason, the submission date and the status. |
| FR-068 | Reservation Approval | The Librarian can approve a pending request, which changes its status to Confirmed. |
| FR-069 | Reservation Rejection | The Librarian can reject a pending request, with an optional reason, which changes its status to Rejected. |
| FR-070 | Approval Authority | Only a Librarian or the Admin can approve or reject reservation requests. |
| FR-071 | Release of Rejected Requests | When a request is rejected, its seats become available to other students again. |
| FR-072 | Expiry of Unreviewed Requests | A request that is not reviewed before its reserved time is cancelled automatically and its seats are released. |
| FR-073 | Withdrawing a Request | A student can withdraw their own pending request at any time. |
| FR-074 | Cancellation by Student | A student can cancel their own confirmed reservation before it starts. |
| FR-075 | Cancellation by Staff | A Librarian or the Admin can cancel a reservation and give the student a reason. |
| FR-076 | Reservation on Behalf of a Student | A Librarian or the Admin can make a reservation for a student, which is confirmed immediately. |
| FR-077 | Reservation Status Tracking | Each reservation has a status: Pending, Confirmed, Checked in, Completed, Cancelled, Rejected or No-show. |
| FR-078 | My Reservations | Students can view their upcoming reservations and their reservation history. |
| FR-079 | Reservation Details | Users can open a reservation to see its details, its status and the history of what happened to it. |
| FR-080 | Reservation List for Staff | Library staff can view all reservations and search or filter them by student, code, date, status and type. |
| FR-081 | Reservation Code | Every reservation receives a unique reference code. |

## 9. Notifications

| ID | Functional Requirement | Description |
|---|---|---|
| FR-082 | New Request Notification to Librarians | The system notifies every Librarian when a student submits a reservation request. |
| FR-083 | New Request Notification to Admin | The system also notifies the Admin when a student submits a reservation request. |
| FR-084 | Request Received Notification | The student is notified that their request was sent and is waiting for approval. |
| FR-085 | Approval Notification | The student is notified when their request is approved. |
| FR-086 | Rejection Notification | The student is notified when their request is rejected, together with the reason given. |
| FR-087 | Cancellation and Expiry Notifications | The student is notified when their reservation is cancelled or their request expires. |
| FR-088 | Reminder Notification | The student is reminded shortly before a confirmed reservation starts. |
| FR-089 | Check-in and No-Show Notifications | The student is notified when they are checked in and when a reservation is marked as a no-show. |
| FR-090 | Invitation Notification | A classmate added to a study room reservation is notified. |
| FR-091 | Unread Notification Count | The system shows the number of unread notifications on the notification bell and in the menu. |
| FR-092 | Notification List | Users can view their notifications, mark them as read and delete them. |
| FR-093 | Link to Reservation | Selecting a notification opens the reservation it refers to. |
| FR-094 | Stored Notifications | Notifications are saved in the database and remain available after the page is refreshed. |

## 10. Check-in and Library Operations

| ID | Functional Requirement | Description |
|---|---|---|
| FR-095 | Student Self Check-in | A student can check in to their confirmed reservation during the check-in period. |
| FR-096 | Check-in Period | Check-in opens shortly before the start time and closes after a grace period. |
| FR-097 | Check-in Code | A confirmed reservation shows its code as text and as a QR code for the student to present. |
| FR-098 | Check-in Desk | Library staff can find a reservation by entering its code and confirm the student's arrival. |
| FR-099 | Check-in by Staff | A Librarian, a Student Assistant or the Admin can check a student in. |
| FR-100 | Check-out | A student or a staff member can check out, which ends the reservation and frees the seat. |
| FR-101 | Automatic Completion | A checked-in reservation is completed automatically when its end time is reached. |
| FR-102 | Automatic No-Show | A confirmed reservation that is not checked in during the check-in period is marked as a no-show and its seat is released. |
| FR-103 | Manual No-Show | A Librarian or the Admin can mark a reservation as a no-show after it has started. |
| FR-104 | Live Occupancy Monitoring | Library staff can see how many seats and computers are occupied, reserved, available and unavailable. |
| FR-105 | Occupant Information for Staff | Library staff can see which student has requested or is using a seat. |

## 11. Dashboards and Reports

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

## 12. Library Settings

| ID | Functional Requirement | Description |
|---|---|---|
| FR-114 | Operating Hours Management | The Admin can set the opening and closing time for each day of the week. |
| FR-115 | Closure Day Management | The Admin can add and remove days on which the library is closed. |
| FR-116 | Reservation Rule Configuration | The Admin can set booking limits, durations, the advance-booking period, check-in times and the no-show limit. |
| FR-117 | Self Check-in Setting | The Admin can turn student self check-in on or off. |
| FR-118 | Reservations Affected by Schedule Changes | When hours change or a closure is added, reservations that no longer fit are cancelled and the students are notified. |

## 13. Profile Management

| ID | Functional Requirement | Description |
|---|---|---|
| FR-119 | View Profile | Users can view their own account details and role. |
| FR-120 | Update Profile | Users can update their name, mobile number, program and year level. |
| FR-121 | Change Password | Users can change their password by entering their current password and a new one. |

## 14. Other System Functions

| ID | Functional Requirement | Description |
|---|---|---|
| FR-122 | Automatic Data Refresh | Seat availability, dashboards and notifications refresh automatically every few seconds. |
| FR-123 | Form Draft Preservation | Information entered in a form is kept when the page is refreshed and cleared after submission or logout. |
| FR-124 | Responsive Layout | The system adapts to desktop, laptop, tablet and mobile screens, with a menu button on smaller screens. |
| FR-125 | Installable Application | Users can install the system on a phone or computer and open it like an app. |
| FR-126 | Offline Notice | When there is no connection, the system says so and does not allow reservation actions until the connection returns. |
| FR-127 | Action Confirmation | The system asks for confirmation before actions such as cancelling, rejecting or deactivating. |
