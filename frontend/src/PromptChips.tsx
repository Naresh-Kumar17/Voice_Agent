import React from 'react'

interface PromptChip {
  id: string
  icon: string
  label: string
  utterance: string
}

const PROMPT_CHIPS: PromptChip[] = [
  {
    id: 'book',
    icon: '📅',
    label: 'Book Dr. Khan',
    utterance: 'I would like to book an appointment with Dr. Ahmed Khan tomorrow at 10 AM.',
  },
  {
    id: 'hours',
    icon: '🕒',
    label: 'Clinic Hours',
    utterance: 'What are the clinic opening and closing hours?',
  },
  {
    id: 'doctors',
    icon: '🩺',
    label: 'Doctors & Specialties',
    utterance: 'Which doctors and medical specialties are available at the clinic?',
  },
  {
    id: 'reschedule',
    icon: '🔄',
    label: 'Reschedule Visit',
    utterance: 'I need to reschedule my existing appointment to another day.',
  },
  {
    id: 'location',
    icon: '📍',
    label: 'Address & Parking',
    utterance: 'Where is the clinic located and is patient parking available?',
  },
]

interface PromptChipsProps {
  onSelectPrompt?: (utterance: string) => void
  activeCall: boolean
}

export const PromptChips: React.FC<PromptChipsProps> = ({ onSelectPrompt, activeCall }) => {
  return (
    <div className="prompt-chips-container" aria-label="Quick patient voice suggestions">
      <div className="prompt-chips-label">
        <span className="chips-sparkle">✦</span>
        <span>TRY SAYING TO RACHEL:</span>
      </div>
      <div className="prompt-chips-list">
        {PROMPT_CHIPS.map(chip => (
          <button
            key={chip.id}
            className="prompt-chip"
            onClick={() => onSelectPrompt?.(chip.utterance)}
            title={`Example: "${chip.utterance}"`}
          >
            <span className="chip-icon">{chip.icon}</span>
            <span className="chip-label">{chip.label}</span>
          </button>
        ))}
      </div>
      {activeCall && (
        <span className="prompt-hint-text">
          💡 You can speak these sentences naturally into your microphone anytime Rachel is listening.
        </span>
      )}
    </div>
  )
}
export default PromptChips

