import React, { useEffect, useState } from 'react'
import { api, type Doctor } from './api'

interface DoctorCardsProps {
  onSelectDoctor?: (doctor: Doctor) => void
}

export const DoctorCards: React.FC<DoctorCardsProps> = ({ onSelectDoctor }) => {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true
    api<Doctor[]>('/api/v1/doctors')
      .then(data => {
        if (isMounted) {
          setDoctors(data)
          setLoading(false)
        }
      })
      .catch(err => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Could not fetch doctors.')
          setLoading(false)
        }
      })
    return () => {
      isMounted = false
    }
  }, [])

  if (loading) {
    return (
      <div className="doctors-loading">
        <span className="spinner" />
        <span>Loading clinic physicians & schedules…</span>
      </div>
    )
  }

  if (error || doctors.length === 0) {
    return null
  }

  const getSpecialtyIcon = (spec: string) => {
    const s = spec.toLowerCase()
    if (s.includes('cardio')) return '❤️'
    if (s.includes('derma')) return '✨'
    return '🩺'
  }

  return (
    <div className="doctors-bento-section">
      <div className="bento-header">
        <div>
          <span className="eyebrow">
            <span className="eyebrow-dot" />
            ATTENDING PHYSICIANS
          </span>
          <h3 className="bento-title">Our Medical Specialists</h3>
        </div>
        <span className="bento-subtitle">Direct live calendar synchronization with Rachel</span>
      </div>

      <div className="doctors-grid">
        {doctors.map(doc => (
          <div
            key={doc.doctor_id}
            className="doctor-bento-card"
            onClick={() => onSelectDoctor?.(doc)}
            role="button"
            tabIndex={0}
            title={`Ask Rachel to book with ${doc.doctor_name}`}
          >
            <div className="doctor-card-top">
              <span className="doctor-avatar-badge">{getSpecialtyIcon(doc.specialization)}</span>
              <span className="doctor-status-pill">
                <i className="status-dot online" />
                Available Today
              </span>
            </div>

            <div className="doctor-info">
              <strong className="doctor-name">{doc.doctor_name}</strong>
              <span className="doctor-specialty">{doc.specialization}</span>
            </div>

            <div className="doctor-hours">
              <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
              <span>Hours: {doc.working_hours_start} – {doc.working_hours_end}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
export default DoctorCards
