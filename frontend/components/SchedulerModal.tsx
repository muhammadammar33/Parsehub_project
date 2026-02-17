'use client'

import { useState } from 'react'
import Modal from './Modal'

interface SchedulerModalProps {
  projectToken: string
  onClose: () => void
  onSchedule: (scheduledTime: string) => void
}

export default function SchedulerModal({
  projectToken,
  onClose,
  onSchedule,
}: SchedulerModalProps) {
  const [scheduleType, setScheduleType] = useState<'once' | 'recurring'>('once')
  const [date, setDate] = useState('')
  const [time, setTime] = useState('')
  const [frequency, setFrequency] = useState<'daily' | 'weekly' | 'monthly'>('daily')
  const [dayOfWeek, setDayOfWeek] = useState('monday')
  const [loading, setLoading] = useState(false)

  const handleSchedule = async () => {
    if (!date || !time) {
      alert('Please select both date and time')
      return
    }

    setLoading(true)
    try {
      const scheduledDateTime = `${date}T${time}`
      
      const response = await fetch('/api/projects/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectToken,
          scheduleType,
          scheduledTime: scheduledDateTime,
          frequency: scheduleType === 'recurring' ? frequency : undefined,
          dayOfWeek: scheduleType === 'recurring' && frequency === 'weekly' ? dayOfWeek : undefined,
        }),
      })

      if (response.ok) {
        alert(`✅ Scheduled successfully for ${scheduledDateTime}`)
        onSchedule(scheduledDateTime)
        onClose()
      } else {
        alert('Failed to schedule')
      }
    } catch (error) {
      console.error('Schedule error:', error)
      alert('Error scheduling run')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal isOpen={true} onClose={onClose} title="Schedule Run">
      <div className="space-y-4">
        {/* Schedule Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Schedule Type
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => setScheduleType('once')}
              className={`flex-1 py-2 px-3 rounded-lg font-medium transition-colors ${
                scheduleType === 'once'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Run Once
            </button>
            <button
              onClick={() => setScheduleType('recurring')}
              className={`flex-1 py-2 px-3 rounded-lg font-medium transition-colors ${
                scheduleType === 'recurring'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Recurring
            </button>
          </div>
        </div>

        {/* Date & Time */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Time
            </label>
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
        </div>

        {/* Recurring Options */}
        {scheduleType === 'recurring' && (
          <div className="space-y-3 p-3 bg-purple-50 rounded-lg">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Frequency
              </label>
              <select
                value={frequency}
                onChange={(e) => setFrequency(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>

            {frequency === 'weekly' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Day of Week
                </label>
                <select
                  value={dayOfWeek}
                  onChange={(e) => setDayOfWeek(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="monday">Monday</option>
                  <option value="tuesday">Tuesday</option>
                  <option value="wednesday">Wednesday</option>
                  <option value="thursday">Thursday</option>
                  <option value="friday">Friday</option>
                  <option value="saturday">Saturday</option>
                  <option value="sunday">Sunday</option>
                </select>
              </div>
            )}
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-2 pt-4">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSchedule}
            disabled={loading}
            className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
          >
            {loading ? 'Scheduling...' : 'Schedule'}
          </button>
        </div>
      </div>
    </Modal>
  )
}
