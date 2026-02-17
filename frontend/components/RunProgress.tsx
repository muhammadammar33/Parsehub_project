'use client'

import React, { useState, useEffect } from 'react'
import { Activity, AlertCircle, CheckCircle, Clock } from 'lucide-react'

interface RunProgressProps {
  projectToken: string
  runToken?: string
  isActive?: boolean
  refreshInterval?: number
}

export default function RunProgress({
  projectToken,
  runToken,
  isActive = false,
  refreshInterval = 3000,
}: RunProgressProps) {
  const [status, setStatus] = useState<any>(null)
  const [shouldAuto, setShouldAuto] = useState(isActive)

  useEffect(() => {
    if (!shouldAuto) {
      return
    }

    const loadStatus = async () => {
      try {
        const url = runToken
          ? `/api/projects/${projectToken}/${runToken}`
          : `/api/projects/${projectToken}`

        const response = await fetch(url)
        if (response.ok) {
          const data = await response.json()
          setStatus(data)
          
          // Stop auto-refresh if run is complete
          if (data.status === 'complete') {
            setShouldAuto(false)
          }
        }
      } catch (err) {
        console.error('Error loading run status:', err)
      }
    }

    loadStatus()
    const interval = setInterval(loadStatus, refreshInterval)
    return () => clearInterval(interval)
  }, [shouldAuto, projectToken, runToken, refreshInterval])

  if (!status) {
    return null
  }

  const totalPages = status.pages_to_scrape || 1
  const currentPage = status.pages_scraped || 0
  const pagesRemaining = Math.max(0, totalPages - currentPage)
  const completionPercentage = (currentPage / totalPages) * 100

  const getStatusIcon = () => {
    if (status.status === 'complete') return <CheckCircle className="w-5 h-5 text-green-600" />
    if (status.status === 'error') return <AlertCircle className="w-5 h-5 text-red-600" />
    return <Activity className="w-5 h-5 text-blue-600 animate-spin" />
  }

  const getStatusColor = () => {
    if (status.status === 'complete') return 'bg-green-50 border-green-200'
    if (status.status === 'error') return 'bg-red-50 border-red-200'
    return 'bg-blue-50 border-blue-200'
  }

  const getStatusText = () => {
    if (status.status === 'complete') return 'Complete'
    if (status.status === 'error') return 'Error'
    return 'Running'
  }

  return (
    <div className={`border rounded-lg p-4 space-y-3 ${getStatusColor()}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <div>
            <p className="font-semibold text-gray-900">Run Progress</p>
            <p className="text-xs text-gray-600 flex items-center gap-1 mt-0.5">
              <Clock className="w-3 h-3" />
              {status.start_time && new Date(status.start_time).toLocaleString()}
            </p>
          </div>
        </div>
        <span className="text-sm font-medium text-gray-600">
          {getStatusText()}
        </span>
      </div>

      {/* Pages Progress */}
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-gray-700 font-medium">Pages</span>
          <span className="text-gray-600">
            {currentPage} / {totalPages}
          </span>
        </div>
        <div className="w-full h-2 bg-gray-200 rounded overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${Math.min(completionPercentage, 100)}%` }}
          />
        </div>
        <div className="text-xs text-gray-600">
          {completionPercentage.toFixed(1)}% complete • {pagesRemaining} remaining
        </div>
      </div>

      {/* Data Stats */}
      {status.records_count !== undefined && (
        <div className="grid grid-cols-2 gap-2 pt-2">
          <div className="bg-white rounded p-2 border border-gray-200">
            <p className="text-xs text-gray-600 font-medium">Records Scraped</p>
            <p className="text-lg font-bold text-gray-900">{status.records_count}</p>
          </div>
          <div className="bg-white rounded p-2 border border-gray-200">
            <p className="text-xs text-gray-600 font-medium">Avg. Rate</p>
            <p className="text-lg font-bold text-gray-900">
              {status.scraping_rate?.items_per_minute || '-'} /min
            </p>
          </div>
        </div>
      )}

      {/* Auto-Recovery Message */}
      {pagesRemaining > 0 && status.status !== 'complete' && (
        <div className="text-xs bg-white bg-opacity-60 p-2 rounded border-l-2 border-blue-400 text-blue-800">
          If this run stops, you can resume from page {currentPage + 1} automatically.
        </div>
      )}

      {status.status === 'error' && status.error && (
        <div className="text-xs bg-white bg-opacity-60 p-2 rounded border-l-2 border-red-400 text-red-800">
          <strong>Error:</strong> {status.error}
        </div>
      )}

      {/* Manual Refresh Button */}
      {!shouldAuto && (
        <button
          onClick={() => setShouldAuto(true)}
          className="w-full py-1 text-xs text-blue-600 hover:text-blue-700 font-medium"
        >
          Resume monitoring
        </button>
      )}
    </div>
  )
}
