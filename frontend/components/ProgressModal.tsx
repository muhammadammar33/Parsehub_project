'use client'

import React, { useState, useEffect } from 'react'
import { CheckCircle, Clock, AlertCircle, X } from 'lucide-react'

interface ProgressModalProps {
  isOpen: boolean
  onClose: () => void
  sessionId: number
  projectName: string
}

interface SessionProgress {
  session_id: number
  project_name: string
  total_pages_target: number
  pages_completed: number
  current_iteration: number
  status: string
  percentage: number
  iterations_completed: number
  total_iterations_needed: number
  estimated_remaining_time: string
  runs: Array<{
    iteration: number
    pages: string
    records: number
    status: string
    completed_at: string | null
  }>
}

export default function ProgressModal({
  isOpen,
  onClose,
  sessionId,
  projectName,
}: ProgressModalProps) {
  const [progress, setProgress] = useState<SessionProgress | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [autoClose, setAutoClose] = useState(false)

  useEffect(() => {
    if (!isOpen) return

    const fetchProgress = async () => {
      try {
        const response = await fetch(`/api/projects/incremental/progress?session_id=${sessionId}`)
        
        const data = await response.json()
        
        // Check if response has an error field
        if (data.error || !response.ok) {
          setError(data.error || 'Failed to fetch progress')
          setLoading(false)
          return
        }

        setProgress(data as SessionProgress)
        setLoading(false)
        setError('')

        // Auto-close when complete
        if (data.status === 'completed') {
          setAutoClose(true)
          setTimeout(() => {
            onClose()
          }, 3000)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch progress')
        setLoading(false)
      }
    }

    // Initial fetch
    fetchProgress()

    // Poll every 5 seconds
    const interval = setInterval(fetchProgress, 5000)

    return () => clearInterval(interval)
  }, [isOpen, sessionId, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-orange-500 to-orange-600 text-white p-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">{projectName}</h2>
            <p className="text-orange-100 text-sm">Session #{sessionId} - Incremental Scraping</p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-orange-700 p-2 rounded"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading && !progress ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600 mb-2"></div>
              <p className="text-gray-600">Fetching session progress...</p>
            </div>
          ) : error && !progress ? (
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-red-900">Unable to Load Progress</p>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                  <p className="text-xs text-red-600 mt-2">
                    The system is trying to fetch your session progress. This might be because:
                  </p>
                  <ul className="text-xs text-red-600 mt-1 ml-4 list-disc">
                    <li>The session hasn't started executing yet</li>
                    <li>The backend service is initializing</li>
                    <li>There's a temporary connection issue</li>
                  </ul>
                </div>
              </div>
              <div className="text-center text-sm text-gray-600">
                The modal will automatically retry every 5 seconds...
              </div>
            </div>
          ) : progress ? (
            <div className="space-y-6">
              {/* Overall Progress */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    Pages Scraped
                  </span>
                  <span className="text-sm font-semibold text-gray-900">
                    {progress.pages_completed} / {progress.total_pages_target}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-orange-500 to-orange-600 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${progress.percentage}%` }}
                  ></div>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-sm text-gray-600">{progress.percentage}% Complete</span>
                  <span className="text-sm text-gray-600">
                    ETA: {progress.estimated_remaining_time}
                  </span>
                </div>
              </div>

              {/* Status Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 border border-blue-200 rounded p-4">
                  <p className="text-sm text-gray-600">Iterations Completed</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {progress.iterations_completed} / {progress.total_iterations_needed}
                  </p>
                </div>
                <div className="bg-green-50 border border-green-200 rounded p-4">
                  <p className="text-sm text-gray-600">Current Status</p>
                  <p className="text-lg font-semibold text-green-600 capitalize">
                    {progress.status === 'completed' ? '✅ Complete' : '⏳ Running'}
                  </p>
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded p-4">
                  <p className="text-sm text-gray-600">Data Collected</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {progress.runs.reduce((sum, r) => sum + r.records, 0)} records
                  </p>
                </div>
              </div>

              {/* Iteration Details */}
              {progress.runs.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3">Iteration Details</h3>
                  <div className="space-y-2 max-h-[300px] overflow-y-auto">
                    {progress.runs.map((run) => (
                      <div
                        key={run.iteration}
                        className={`flex items-center justify-between p-3 rounded border ${
                          run.status === 'completed'
                            ? 'bg-green-50 border-green-200'
                            : run.status === 'running'
                              ? 'bg-blue-50 border-blue-200'
                              : 'bg-gray-50 border-gray-200'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          {run.status === 'completed' ? (
                            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                          ) : run.status === 'running' ? (
                            <Clock className="w-5 h-5 text-blue-600 flex-shrink-0 animate-spin" />
                          ) : (
                            <div className="w-5 h-5 rounded-full border-2 border-gray-300 flex-shrink-0" />
                          )}
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              Iteration {run.iteration}
                            </p>
                            <p className="text-xs text-gray-600">Pages {run.pages}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-semibold text-gray-900">
                            {run.records}
                          </p>
                          <p className="text-xs text-gray-600">records</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Auto-close message */}
              {autoClose && (
                <div className="bg-green-50 border border-green-200 rounded p-4 text-center">
                  <p className="text-sm text-green-700 font-medium">
                    ✅ Scraping completed! Window will close in 3 seconds...
                  </p>
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        {!autoClose && (
          <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 p-4 flex justify-end gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Close
            </button>
            {progress?.status !== 'completed' && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <div className="animate-pulse w-2 h-2 rounded-full bg-orange-600"></div>
                Live Updates
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
