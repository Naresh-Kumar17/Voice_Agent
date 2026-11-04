import { useCallback, useEffect, useMemo, useState } from 'react'
import { getAppointments, getDoctors, type Appointment, type Doctor } from './api'

interface LiveCalendarViewProps {
  onNavigateToVoice?: () => void
}

const TIME_SLOTS = [
  '08:30', '09:00', '09:30', '10:00', '10:30', '11:00',
  '11:30', '12:00', '12:30', '13:00', '13:30', '14:00',
  '14:30', '15:00', '15:30', '16:00', '16:30', '17:00'
]

export default function LiveCalendarView({ onNavigateToVoice }: LiveCalendarViewProps) {
  // Default to today's date
  const todayStr = useMemo(() => {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }, [])

  const [selectedDate, setSelectedDate] = useState<string>(todayStr)
  const [selectedDoctorId, setSelectedDoctorId] = useState<string>('all')
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedAppt, setSelectedAppt] = useState<Appointment | null>(null)
  const [lastSyncTime, setLastSyncTime] = useState<string>('')
  const [autoSync, setAutoSync] = useState(true)

  // Fetch doctors list once
  useEffect(() => {
    getDoctors()
      .then(docs => setDoctors(docs))
      .catch(err => console.error('Failed to load doctors:', err))
  }, [])

  // Fetch appointments for selected date
  const loadAppointments = useCallback(async () => {
    try {
      setError(null)
      const data = await getAppointments(selectedDate)
      setAppointments(data)
      const now = new Date()
      setLastSyncTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
    } catch (err: any) {
      console.error('Failed to fetch appointments:', err)
      setError(err?.message || 'Failed to sync appointments')
    } finally {
      setLoading(false)
    }
  }, [selectedDate])

  useEffect(() => {
    setLoading(true)
    void loadAppointments()
  }, [loadAppointments])

  // Periodic polling every 4 seconds when autoSync is true
  useEffect(() => {
    if (!autoSync) return
    const interval = setInterval(() => {
      void loadAppointments()
    }, 4000)
    return () => clearInterval(interval)
  }, [autoSync, loadAppointments])

  // Filtered doctors list
  const displayDoctors = useMemo(() => {
    if (selectedDoctorId === 'all') return doctors
    return doctors.filter(d => d.doctor_id === selectedDoctorId)
  }, [doctors, selectedDoctorId])

  // Statistics for the selected date
  const stats = useMemo(() => {
    const total = appointments.length
    const confirmed = appointments.filter(a => a.status === 'CONFIRMED').length
    const cancelled = appointments.filter(a => a.status === 'CANCELLED').length
    const doctorBookings = doctors.map(d => ({
      name: d.doctor_name,
      count: appointments.filter(a => a.doctor_id === d.doctor_id && a.status === 'CONFIRMED').length
    }))
    return { total, confirmed, cancelled, doctorBookings }
  }, [appointments, doctors])

  // Helper to format ISO date to readable string
  const formatDateHeading = (dateStr: string) => {
    try {
      const [y, m, d] = dateStr.split('-').map(Number)
      const dt = new Date(y, m - 1, d)
      return dt.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
    } catch {
      return dateStr
    }
  }

  // Quick date pickers
  const setQuickDate = (offsetDays: number) => {
    const dt = new Date()
    dt.setDate(dt.getDate() + offsetDays)
    const y = dt.getFullYear()
    const m = String(dt.getMonth() + 1).padStart(2, '0')
    const d = String(dt.getDate()).padStart(2, '0')
    setSelectedDate(`${y}-${m}-${d}`)
  }

  // Check if slot falls in doctor's working hours
  const isWithinHours = (doctor: Doctor, slot: string) => {
    return slot >= doctor.working_hours_start && slot < doctor.working_hours_end
  }

  return (
    <div className="calendar-dashboard-container">
      {/* Top Banner / Sync Bar */}
      <div className="calendar-top-strip">
        <div className="calendar-title-group">
          <div className="calendar-badge">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zm0-12H5V6h14v2z" />
            </svg>
            <span>CLINIC APPOINTMENT DATABASE</span>
          </div>
          <h2>Live Doctor Calendar & Appointment Grid</h2>
          <p className="calendar-subtitle">
            Displays appointments saved by the backend and refreshes every 4 seconds. Calendar availability and event writes are handled by the booking service.
          </p>
        </div>

        <div className="calendar-sync-controls">
          <div className="sync-status-pill" title="Live sync polling every 4 seconds">
            <span className={`sync-indicator-dot ${autoSync ? 'pulsing' : ''}`} />
            <span className="sync-label">
              {autoSync ? 'Live Sync Active' : 'Sync Paused'}
            </span>
            {lastSyncTime && <span className="sync-timestamp">({lastSyncTime})</span>}
          </div>

          <button
            className="btn-refresh-calendar"
            onClick={() => void loadAppointments()}
            disabled={loading}
            title="Refresh now"
          >
            <svg
              className={`refresh-icon ${loading ? 'spinning' : ''}`}
              viewBox="0 0 24 24"
              width="14"
              height="14"
              fill="currentColor"
            >
              <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" />
            </svg>
            <span>Sync Now</span>
          </button>

          <button
            className={`btn-toggle-auto ${autoSync ? 'active' : ''}`}
            onClick={() => setAutoSync(!autoSync)}
            title="Toggle automatic background sync"
          >
            {autoSync ? 'Auto-Sync: ON' : 'Auto-Sync: OFF'}
          </button>
        </div>
      </div>

      {/* KPI Stats Summary Grid */}
      <div className="calendar-kpi-bar">
        <div className="kpi-card">
          <span className="kpi-label">TOTAL BOOKINGS</span>
          <span className="kpi-value text-glow-cyan">{stats.total}</span>
          <span className="kpi-meta">For {selectedDate}</span>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">CONFIRMED SCHEDULED</span>
          <span className="kpi-value text-glow-emerald">{stats.confirmed}</span>
          <span className="kpi-meta">Confirmed in clinic database</span>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">ACTIVE PHYSICIANS</span>
          <span className="kpi-value text-glow-indigo">{doctors.length}</span>
          <span className="kpi-meta">Dr. Khan, Patel, Chen</span>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">APPOINTMENT SOURCE</span>
          <span className="kpi-value text-glow-indigo">Clinic database</span>
          <span className="kpi-meta">Auto-refreshes every 4 seconds</span>
        </div>
      </div>

      {/* Date Navigation & Doctor Filter Controls */}
      <div className="calendar-filter-toolbar">
        {/* Date Selector Row */}
        <div className="date-nav-group">
          <button
            className={`btn-date-pill ${selectedDate === todayStr ? 'active' : ''}`}
            onClick={() => setQuickDate(0)}
          >
            Today
          </button>
          <button
            className={`btn-date-pill ${
              selectedDate ===
              new Date(Date.now() + 86400000).toISOString().split('T')[0]
                ? 'active'
                : ''
            }`}
            onClick={() => setQuickDate(1)}
          >
            Tomorrow
          </button>
          <div className="date-input-wrapper">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
              <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zm0-12H5V6h14v2z" />
            </svg>
            <input
              type="date"
              className="calendar-date-picker"
              value={selectedDate}
              onChange={e => setSelectedDate(e.target.value)}
              aria-label="Select calendar date"
            />
          </div>
          <span className="selected-date-display">
            📅 {formatDateHeading(selectedDate)}
          </span>
        </div>

        {/* Doctor Tabs Filter */}
        <div className="doctor-filter-tabs">
          <button
            className={`filter-tab ${selectedDoctorId === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedDoctorId('all')}
          >
            All Doctors ({doctors.length})
          </button>
          {doctors.map(d => (
            <button
              key={d.doctor_id}
              className={`filter-tab ${selectedDoctorId === d.doctor_id ? 'active' : ''}`}
              onClick={() => setSelectedDoctorId(d.doctor_id)}
            >
              {d.doctor_name}
              <small className="filter-tab-specialty">({d.specialization})</small>
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="calendar-error-banner">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Main Authentic Calendar Schedule Grid */}
      <div className="schedule-grid-wrapper">
        <div
          className="schedule-grid-container"
          style={{
            gridTemplateColumns: `80px repeat(${displayDoctors.length}, minmax(260px, 1fr))`
          }}
        >
          {/* Header Row: Time Axis Top-Left + Doctor Column Headers */}
          <div className="grid-header-corner">
            <span>TIME</span>
          </div>

          {displayDoctors.map(doctor => {
            const countForDoctor = appointments.filter(
              a => a.doctor_id === doctor.doctor_id && a.status === 'CONFIRMED'
            ).length
            return (
              <div key={doctor.doctor_id} className="grid-header-doctor">
                <div className="doctor-header-avatar">
                  {doctor.doctor_name.replace('Dr. ', '').charAt(0)}
                </div>
                <div className="doctor-header-info">
                  <strong className="doctor-name">{doctor.doctor_name}</strong>
                  <span className="doctor-specialty">{doctor.specialization}</span>
                  <div className="doctor-hours-badge">
                    <span>🕒 {doctor.working_hours_start} – {doctor.working_hours_end}</span>
                    <span className="badge-count-pill">{countForDoctor} booked</span>
                  </div>
                </div>
              </div>
            )
          })}

          {/* Time Slot Rows */}
          {TIME_SLOTS.map(slot => (
            <div key={slot} className="grid-row-contents" style={{ display: 'contents' }}>
              {/* Time Label Cell */}
              <div className="grid-time-cell">
                <span className="time-text">{slot}</span>
              </div>

              {/* Doctor Cells for this Time Slot */}
              {displayDoctors.map(doctor => {
                const onDuty = isWithinHours(doctor, slot)
                const matchingAppt = appointments.find(
                  a => a.doctor_id === doctor.doctor_id && a.start_time === slot
                )

                if (!onDuty) {
                  return (
                    <div
                      key={`${doctor.doctor_id}-${slot}`}
                      className="grid-slot-cell off-duty"
                      title={`${doctor.doctor_name} is off duty at ${slot}`}
                    >
                      <span className="off-duty-label">Off Duty</span>
                    </div>
                  )
                }

                if (matchingAppt) {
                  const isConfirmed = matchingAppt.status === 'CONFIRMED'
                  return (
                    <div
                      key={`${doctor.doctor_id}-${slot}`}
                      className={`grid-slot-cell booked ${isConfirmed ? 'is-confirmed' : 'is-cancelled'}`}
                      onClick={() => setSelectedAppt(matchingAppt)}
                      role="button"
                      tabIndex={0}
                    >
                      <div className="slot-booked-card">
                        <div className="booked-top">
                          <span className="patient-name">
                            👤 {matchingAppt.patient_name}
                          </span>
                          <span className={`status-pill ${matchingAppt.status.toLowerCase()}`}>
                            {matchingAppt.status}
                          </span>
                        </div>

                        <div className="booked-details">
                          <span className="booked-time-range">
                            🕒 {matchingAppt.start_time} – {matchingAppt.end_time}
                          </span>
                          <span className="booked-phone">📞 {matchingAppt.contact_number}</span>
                        </div>

                        <div className="booked-type-badge">
                          <span>{matchingAppt.appointment_type || 'Consultation'}</span>
                        </div>

                        {matchingAppt.calendar_event_id && (
                          <div className="booked-gcal-ref" title={matchingAppt.calendar_event_id}>
                            <svg viewBox="0 0 24 24" width="11" height="11" fill="#34A853">
                              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                            </svg>
                            <span>Calendar ref: {matchingAppt.calendar_event_id}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                }

                return (
                  <div
                    key={`${doctor.doctor_id}-${slot}`}
                    className="grid-slot-cell available"
                  >
                    <span className="available-indicator">Open Slot</span>
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Quick Navigation Footer */}
      <div className="calendar-footer-action">
        <div className="calendar-footer-info">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
          </svg>
          <span>
            Every voice booking made through Rachel immediately syncs to this schedule and reserves the slot in the clinic's Google Calendar.
          </span>
        </div>
        {onNavigateToVoice && (
          <button className="button button-action-secondary" onClick={onNavigateToVoice}>
            <span>✦ Test Booking with Rachel</span>
          </button>
        )}
      </div>

      {/* Appointment Details Modal Drawer */}
      {selectedAppt && (
        <div className="modal-backdrop" onClick={() => setSelectedAppt(null)}>
          <div
            className="calendar-modal"
            onClick={e => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="modal-header">
              <div className="modal-title-group">
                <span className="modal-eyebrow">APPOINTMENT VERIFICATION REPORT</span>
                <h3>Appointment Details</h3>
              </div>
              <button
                className="btn-modal-close"
                onClick={() => setSelectedAppt(null)}
                aria-label="Close dialog"
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div className="detail-status-banner confirmed">
                <div className="status-banner-icon">
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                  </svg>
                </div>
                <div>
                  <strong>Appointment Successfully Verified & Placed</strong>
                  <p>Slot is locked in clinic SQLite DB and synchronized with Google Calendar.</p>
                </div>
              </div>

              <div className="modal-details-grid">
                <div className="detail-item">
                  <span className="detail-label">APPOINTMENT ID</span>
                  <span className="detail-value mono">{selectedAppt.appointment_id}</span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">STATUS</span>
                  <span className={`status-pill ${selectedAppt.status.toLowerCase()}`}>
                    {selectedAppt.status}
                  </span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">PATIENT NAME</span>
                  <span className="detail-value">{selectedAppt.patient_name}</span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">CONTACT PHONE</span>
                  <span className="detail-value">{selectedAppt.contact_number}</span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">ASSIGNED PHYSICIAN</span>
                  <span className="detail-value highlight">{selectedAppt.doctor_name}</span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">DOCTOR ID</span>
                  <span className="detail-value mono">{selectedAppt.doctor_id}</span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">APPOINTMENT DATE</span>
                  <span className="detail-value">{selectedAppt.appointment_date}</span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">TIME WINDOW</span>
                  <span className="detail-value">
                    {selectedAppt.start_time} – {selectedAppt.end_time} (30 mins)
                  </span>
                </div>

                <div className="detail-item full-width">
                  <span className="detail-label">GOOGLE CALENDAR EVENT ID</span>
                  <span className="detail-value mono event-id-chip">
                    {selectedAppt.calendar_event_id || 'Not assigned'}
                  </span>
                </div>

                {selectedAppt.message && (
                  <div className="detail-item full-width">
                    <span className="detail-label">CONFIRMATION MESSAGE</span>
                    <p className="detail-message-box">{selectedAppt.message}</p>
                  </div>
                )}
              </div>
            </div>

            <div className="modal-footer">
              <button
                className="button button-action-secondary"
                onClick={() => setSelectedAppt(null)}
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
