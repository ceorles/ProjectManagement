"""
Builds the Functional Requirements document in two formats from one source:

    docs/Functional_Requirements.md   (editable)
    docs/Functional_Requirements.pdf  (for the paper)

Run from the project root:   python docs/build_functional_requirements.py
Needs ReportLab:             pip install reportlab

To change the document, edit SECTIONS below and run the script again, so the
Markdown and the PDF never drift apart. Every requirement listed here is
implemented in the application.
"""
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

TITLE = 'Functional Requirements of the Library Seat & Study Room Reservation Portal'
SUBTITLE = 'Stakeholder: the School Library'
INTRO = (
    'This document lists the functional requirements of the Library Seat & Study Room '
    'Reservation Portal, a web application that lets students request library seats, tables, '
    'computers and the study room, and lets the library staff review and manage those '
    'requests. The requirements describe the system as it is implemented. They reflect the '
    'actual library: one floor (First Floor), a Reading Hall with 15 tables of 6 chairs '
    '(90 seats), a Computer Area with 4 computers, and one study room.'
)
ROLES = [
    ('Admin', 'Manages accounts, library settings and seating, and has access to every function.'),
    ('Librarian', 'Approves or rejects reservation requests and runs daily library operations.'),
    ('Student Assistant', 'A student who helps the Librarian monitor seats and check students in.'),
    ('Student', 'Requests seats, tables, computers or the study room and manages own reservations.'),
]

# (section title, [(requirement, description), ...])
SECTIONS = [
    ('User Authentication and Account Management', [
        ('Student Registration', 'Students can create their own account using their name, email, student ID and a password.'),
        ('User Login', 'Registered users can log in with their email address and password.'),
        ('User Logout', 'Users can log out, which ends their session on that device.'),
        ('Session Persistence', 'A logged-in user stays logged in after refreshing or reopening the page.'),
        ('Expired Session Handling', 'When a session expires, the system asks the user to log in again and returns them to the page they were on.'),
        ('Password Rules', 'The system rejects passwords that are too short, too common or made of numbers only.'),
        ('Login Attempt Limiting', 'The system limits repeated login and registration attempts to protect accounts.'),
        ('Account Creation by Admin', 'The Admin can create Librarian, Student Assistant, Student and Admin accounts.'),
        ('Account Editing', 'The Admin can edit the details and role of an existing account.'),
        ('Account Deactivation', 'The Admin can deactivate an account so that its owner can no longer log in.'),
        ('Account Reactivation', 'The Admin can reactivate a deactivated account.'),
        ('Password Reset by Admin', 'The Admin can set a new password for a user who forgot theirs.'),
        ('Account Search and Filtering', 'The Admin can search accounts by name, email or student ID and filter them by role and status.'),
    ]),
    ('Role-Based Access Control', [
        ('User Roles', 'The system has four roles: Admin, Librarian, Student Assistant and Student.'),
        ('Role-Based Navigation', 'Each user sees only the menu items and pages that their role is allowed to use.'),
        ('Server-Side Permission Checks', 'The server checks the user\'s role on every request, so restricted actions cannot be done by bypassing the screen.'),
        ('Restricted Page Protection', 'A user who opens a page that their role may not use sees a "no access" message.'),
        ('No Public Staff Registration', 'Librarian, Student Assistant and Admin accounts cannot be created through public registration.'),
        ('Student Assistant Role', 'Student Assistants can view the operations dashboard, the seat map and reservations, and help with check-ins.'),
        ('Student Assistant Restrictions', 'Student Assistants cannot approve, reject or cancel reservations, manage accounts, change settings or view reports.'),
        ('Seat Management Permission', 'The Admin can allow a specific Librarian to manage seats.'),
    ]),
    ('Library Seat Management', [
        ('Library Layout', 'The system represents the actual library: the First Floor with a Reading Hall and a Computer Area.'),
        ('Reading Hall Tables and Seats', 'The Reading Hall has 15 tables with 6 chairs each, for a total of 90 seats.'),
        ('Unique Seat Identification', 'Every seat has a unique identifier that shows its table and chair number, such as T03-2.'),
        ('Seat Map', 'The system shows seats on a visual map where chairs of the same table are grouped around that table.'),
        ('Seat Availability Display', 'The seat map shows whether each seat is available, requested or reserved, occupied, or unavailable for the chosen time.'),
        ('Seat Details and Daily Schedule', 'Users can open a seat to see its details and the times it is taken on the chosen day.'),
        ('Seat Feature Highlighting', 'Users can highlight seats that have a power outlet or a computer.'),
        ('Add, Edit and Delete Seats', 'Authorized staff can add a seat, edit its number, table, position and features, and delete an unused seat.'),
        ('Seat Features', 'A seat can be marked as having a power outlet, having a computer, or being wheelchair accessible.'),
        ('Seating Zone Management', 'Authorized staff can add, edit and delete seating zones.'),
        ('Seat Maintenance Status', 'Authorized staff can mark a seat as under maintenance or out of service, with a note for students.'),
        ('Reservations Affected by Maintenance', 'When a seat is taken out of service, its upcoming reservations are cancelled and the students are notified.'),
        ('Preservation of History', 'Seats and zones that are no longer used are archived instead of deleted, so past reservations remain on record.'),
    ]),
    ('Reservation Scheduling Rules', [
        ('Date Selection', 'Students can choose a reservation date within the allowed number of days in advance.'),
        ('Time and Duration Selection', 'Students can choose a start time and a duration in 30-minute steps.'),
        ('Operating Hours Enforcement', 'The system only accepts reservations that fall within the library\'s opening hours.'),
        ('Closure Day Enforcement', 'The system does not accept reservations on days when the library is closed.'),
        ('Past Time Prevention', 'The system does not accept reservations for a date or time that has already passed.'),
        ('Duration Limits', 'The system enforces the minimum and maximum length of a reservation.'),
        ('Reservation Limits per Student', 'The system limits how many active reservations and how many reservations per day a student may have.'),
        ('One Place at a Time', 'A student cannot hold two reservations that overlap in time.'),
        ('Booking Suspension for Repeated No-Shows', 'A student who misses too many reservations within a set period cannot make new reservations.'),
    ]),
    ('Seat, Table and Group Reservation', [
        ('Individual Seat Reservation', 'Students can request one available seat for a chosen date and time.'),
        ('Two-Seat Reservation', 'Students can request up to two seats without giving a reason.'),
        ('Group Seat Reservation', 'Students can request three to six seats in one request.'),
        ('Whole-Table Reservation', 'Students can request an entire table of six seats with a single selection.'),
        ('Reason for Group Requests', 'The system requires a reason when a student requests more than two seats, including a whole table.'),
        ('Seat Limit per Request', 'One request can cover at most six seats, all in the same area.'),
        ('Review Before Submitting', 'The system shows the selected seats, date and time for the student to review before the request is sent.'),
        ('Availability Verification', 'The server checks that every requested seat is free before saving the request.'),
        ('Double-Booking Prevention', 'The system prevents two reservations from holding the same seat at the same time, even when they are submitted at the same moment.'),
        ('Pending Requests Hold Seats', 'Seats in a pending request are held so that other students cannot request them for the same time.'),
    ]),
    ('Computer Reservation', [
        ('Computer Area', 'The system has a Computer Area with exactly four reservable computers, separate from the 90 seats.'),
        ('Computer Reservation', 'Students can request one available computer for a chosen date and time.'),
        ('One Computer per Request', 'The system does not allow more than one computer in a single reservation.'),
        ('One Student per Computer', 'A computer can be held by only one student during a given time.'),
        ('No Overlapping Computer Use', 'A student cannot hold two computers for overlapping times.'),
        ('Approval of Computer Requests', 'Computer reservations follow the same Librarian approval process as seat reservations.'),
    ]),
    ('Study Room Reservation', [
        ('Study Room Availability', 'Users can see whether the library\'s study room is available for a chosen date and time.'),
        ('Study Room Details and Schedule', 'Users can view the room\'s capacity, facilities and its schedule for the chosen day.'),
        ('Study Room Request', 'Students can request the study room by giving the number of people and the purpose.'),
        ('Group Size Rule', 'The system checks that the number of people fits the room\'s minimum group size and capacity.'),
        ('Inviting Classmates', 'Students can add classmates to a room request by entering their student IDs.'),
    ]),
    ('Reservation Approval and Management', [
        ('Pending Status on Submission', 'Every reservation request submitted by a student is saved with the status Pending.'),
        ('No Automatic Confirmation', 'A student\'s request is never shown as Confirmed until a Librarian approves it.'),
        ('Request Review', 'The Librarian can view the student\'s name and ID, the date and time, the seats requested, the number of seats, the reason, the submission date and the status.'),
        ('Reservation Approval', 'The Librarian can approve a pending request, which changes its status to Confirmed.'),
        ('Reservation Rejection', 'The Librarian can reject a pending request, with an optional reason, which changes its status to Rejected.'),
        ('Approval Authority', 'Only a Librarian or the Admin can approve or reject reservation requests.'),
        ('Release of Rejected Requests', 'When a request is rejected, its seats become available to other students again.'),
        ('Expiry of Unreviewed Requests', 'A request that is not reviewed before its reserved time is cancelled automatically and its seats are released.'),
        ('Withdrawing a Request', 'A student can withdraw their own pending request at any time.'),
        ('Cancellation by Student', 'A student can cancel their own confirmed reservation before it starts.'),
        ('Cancellation by Staff', 'A Librarian or the Admin can cancel a reservation and give the student a reason.'),
        ('Reservation on Behalf of a Student', 'A Librarian or the Admin can make a reservation for a student, which is confirmed immediately.'),
        ('Reservation Status Tracking', 'Each reservation has a status: Pending, Confirmed, Checked in, Completed, Cancelled, Rejected or No-show.'),
        ('My Reservations', 'Students can view their upcoming reservations and their reservation history.'),
        ('Reservation Details', 'Users can open a reservation to see its details, its status and the history of what happened to it.'),
        ('Reservation List for Staff', 'Library staff can view all reservations and search or filter them by student, code, date, status and type.'),
        ('Reservation Code', 'Every reservation receives a unique reference code.'),
    ]),
    ('Notifications', [
        ('New Request Notification to Librarians', 'The system notifies every Librarian when a student submits a reservation request.'),
        ('New Request Notification to Admin', 'The system also notifies the Admin when a student submits a reservation request.'),
        ('Request Received Notification', 'The student is notified that their request was sent and is waiting for approval.'),
        ('Approval Notification', 'The student is notified when their request is approved.'),
        ('Rejection Notification', 'The student is notified when their request is rejected, together with the reason given.'),
        ('Cancellation and Expiry Notifications', 'The student is notified when their reservation is cancelled or their request expires.'),
        ('Reminder Notification', 'The student is reminded shortly before a confirmed reservation starts.'),
        ('Check-in and No-Show Notifications', 'The student is notified when they are checked in and when a reservation is marked as a no-show.'),
        ('Invitation Notification', 'A classmate added to a study room reservation is notified.'),
        ('Unread Notification Count', 'The system shows the number of unread notifications on the notification bell and in the menu.'),
        ('Notification List', 'Users can view their notifications, mark them as read and delete them.'),
        ('Link to Reservation', 'Selecting a notification opens the reservation it refers to.'),
        ('Stored Notifications', 'Notifications are saved in the database and remain available after the page is refreshed.'),
    ]),
    ('Check-in and Library Operations', [
        ('Student Self Check-in', 'A student can check in to their confirmed reservation during the check-in period.'),
        ('Check-in Period', 'Check-in opens shortly before the start time and closes after a grace period.'),
        ('Check-in Code', 'A confirmed reservation shows its code as text and as a QR code for the student to present.'),
        ('Check-in Desk', 'Library staff can find a reservation by entering its code and confirm the student\'s arrival.'),
        ('Check-in by Staff', 'A Librarian, a Student Assistant or the Admin can check a student in.'),
        ('Check-out', 'A student or a staff member can check out, which ends the reservation and frees the seat.'),
        ('Automatic Completion', 'A checked-in reservation is completed automatically when its end time is reached.'),
        ('Automatic No-Show', 'A confirmed reservation that is not checked in during the check-in period is marked as a no-show and its seat is released.'),
        ('Manual No-Show', 'A Librarian or the Admin can mark a reservation as a no-show after it has started.'),
        ('Live Occupancy Monitoring', 'Library staff can see how many seats and computers are occupied, reserved, available and unavailable.'),
        ('Occupant Information for Staff', 'Library staff can see which student has requested or is using a seat.'),
    ]),
    ('Dashboards and Reports', [
        ('Student Dashboard', 'Students see their current and upcoming reservations, their statistics, current availability and their booking standing.'),
        ('Operations Dashboard', 'Librarians and Student Assistants see pending requests, today\'s reservations, students checked in and those awaiting check-in.'),
        ('Pending Request Count', 'The operations dashboard shows how many requests are waiting for approval.'),
        ('Admin Dashboard', 'The Admin sees totals of accounts, seats and reservations, current occupancy, trends and recent activity.'),
        ('Usage Reports', 'Librarians and the Admin can view reservation totals, daily trends, busiest times, most-used seats and outcomes for a chosen period.'),
        ('Report Table View', 'Each chart in the reports can also be shown as a table of numbers.'),
        ('Activity Log', 'The Admin can view a record of logins, reservation actions and changes to accounts, seats and settings.'),
        ('Activity Log Filtering', 'The Admin can search the activity log and filter it by area and date.'),
    ]),
    ('Library Settings', [
        ('Operating Hours Management', 'The Admin can set the opening and closing time for each day of the week.'),
        ('Closure Day Management', 'The Admin can add and remove days on which the library is closed.'),
        ('Reservation Rule Configuration', 'The Admin can set booking limits, durations, the advance-booking period, check-in times and the no-show limit.'),
        ('Self Check-in Setting', 'The Admin can turn student self check-in on or off.'),
        ('Reservations Affected by Schedule Changes', 'When hours change or a closure is added, reservations that no longer fit are cancelled and the students are notified.'),
    ]),
    ('Profile Management', [
        ('View Profile', 'Users can view their own account details and role.'),
        ('Update Profile', 'Users can update their name, mobile number, program and year level.'),
        ('Change Password', 'Users can change their password by entering their current password and a new one.'),
    ]),
    ('Other System Functions', [
        ('Automatic Data Refresh', 'Seat availability, dashboards and notifications refresh automatically every few seconds.'),
        ('Form Draft Preservation', 'Information entered in a form is kept when the page is refreshed and cleared after submission or logout.'),
        ('Responsive Layout', 'The system adapts to desktop, laptop, tablet and mobile screens, with a menu button on smaller screens.'),
        ('Installable Application', 'Users can install the system on a phone or computer and open it like an app.'),
        ('Offline Notice', 'When there is no connection, the system says so and does not allow reservation actions until the connection returns.'),
        ('Action Confirmation', 'The system asks for confirmation before actions such as cancelling, rejecting or deactivating.'),
    ]),
]


def numbered():
    """[(section number, title, [(FR-001, name, description), ...])]"""
    number = 0
    out = []
    for index, (title, items) in enumerate(SECTIONS, start=1):
        rows = []
        for name, description in items:
            number += 1
            rows.append((f'FR-{number:03d}', name, description))
        out.append((index, title, rows))
    return out, number


def build_markdown(path, today):
    sections, total = numbered()
    lines = [f'# {TITLE}', '', f'{SUBTITLE}  ', f'Date: {today}  ',
             f'Total functional requirements: {total}', '', INTRO, '', '## User Roles', '',
             '| Role | Description |', '|---|---|']
    lines += [f'| {role} | {text} |' for role, text in ROLES]
    for index, title, rows in sections:
        lines += ['', f'## {index}. {title}', '', '| ID | Functional Requirement | Description |',
                  '|---|---|---|']
        lines += [f'| {code} | {name} | {text} |' for code, name, text in rows]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return total


def build_pdf(path, today):
    sections, total = numbered()
    navy = colors.HexColor('#103479')
    rule = colors.HexColor('#b9c3d6')
    base = dict(fontName='Times-Roman', fontSize=10.5, leading=13.5)
    styles = {
        'title': ParagraphStyle('title', fontName='Times-Bold', fontSize=18, leading=23,
                                alignment=TA_CENTER, textColor=navy, spaceAfter=6),
        'subtitle': ParagraphStyle('subtitle', fontName='Times-Roman', fontSize=11.5, leading=15,
                                   alignment=TA_CENTER, textColor=colors.HexColor('#35405a')),
        'body': ParagraphStyle('body', **base, alignment=4, spaceAfter=8),
        'heading': ParagraphStyle('heading', fontName='Times-Bold', fontSize=13, leading=16,
                                  textColor=navy, spaceBefore=14, spaceAfter=6),
        'cell': ParagraphStyle('cell', **base),
        'cellbold': ParagraphStyle('cellbold', **{**base, 'fontName': 'Times-Bold'}),
        'head': ParagraphStyle('head', fontName='Times-Bold', fontSize=10.5, leading=13.5,
                               textColor=colors.white),
    }

    def table(header, rows, widths):
        data = [[Paragraph(text, styles['head']) for text in header]]
        for row in rows:
            data.append([
                Paragraph(str(value), styles['cellbold' if column == 0 else 'cell'])
                for column, value in enumerate(row)
            ])
        grid = Table(data, colWidths=widths, repeatRows=1)
        grid.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), navy),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, rule),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f6fb')]),
            ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        return grid

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(rule)
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, 1.6 * cm, A4[0] - doc.rightMargin, 1.6 * cm)
        canvas.setFont('Times-Roman', 9)
        canvas.setFillColor(colors.HexColor('#4d5874'))
        canvas.drawString(doc.leftMargin, 1.15 * cm,
                          'Library Seat & Study Room Reservation Portal - Functional Requirements')
        canvas.drawRightString(A4[0] - doc.rightMargin, 1.15 * cm, f'Page {doc.page}')
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(path), pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2.2 * cm,
        bottomMargin=2.4 * cm, title=TITLE, author='Project Management Group',
        subject='Functional requirements')
    width = A4[0] - doc.leftMargin - doc.rightMargin

    story = [
        Paragraph(TITLE, styles['title']),
        Paragraph(f'{SUBTITLE} &nbsp;|&nbsp; {today} &nbsp;|&nbsp; {total} functional requirements',
                  styles['subtitle']),
        Spacer(1, 14),
        Paragraph(INTRO, styles['body']),
        Paragraph('User Roles', styles['heading']),
        table(['Role', 'Description'], ROLES, [3.6 * cm, width - 3.6 * cm]),
    ]
    widths = [1.9 * cm, 4.7 * cm, width - 6.6 * cm]
    for index, title, rows in sections:
        heading = Paragraph(f'{index}. {title}', styles['heading'])
        grid = table(['ID', 'Functional Requirement', 'Description'], rows, widths)
        # Keep a heading with the start of its table rather than alone at a page end.
        story.append(KeepTogether([heading, Spacer(1, 1)]))
        story.append(grid)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return total


if __name__ == '__main__':
    folder = Path(__file__).resolve().parent
    today = date.today().strftime('%B %d, %Y').replace(' 0', ' ')
    count = build_markdown(folder / 'Functional_Requirements.md', today)
    build_pdf(folder / 'Functional_Requirements.pdf', today)
    print(f'Wrote {count} requirements to Functional_Requirements.md and .pdf in {folder}')
