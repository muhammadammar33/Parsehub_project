'use client'

import { useEffect, useState, useCallback } from 'react'
import Modal from './Modal'
import { TrendingUp } from 'lucide-react'

interface Analytics {
  overview: {
    total_runs: number
    completed_runs: number
    total_records_scraped: number
    progress_percentage: number
  }
  performance: {
    items_per_minute: number
    estimated_total_items: number
    average_run_duration_seconds: number
    current_items_count: number
  }
  recovery: {
    in_recovery: boolean
    status: string
    total_recovery_attempts: number
  }
  data_quality: {
    average_completion_percentage: number
    total_fields: number
  }
  timeline: any[]
}

interface MonitoringSession {
  sessionId: number
  projectId: number
  runToken: string
  targetPages: number
  status: 'active' | 'completed' | 'failed' | 'cancelled'
  totalPages: number
  totalRecords: number
  progressPercentage: number
  currentUrl?: string
  errorMessage?: string
  startTime: string
  endTime?: string
}

interface ScrapedRecord {
  id: number
  pageNumber: number
  data: Record<string, any>
  createdAt: string
}

interface AnalyticsModalProps {
  isOpen: boolean
  onClose: () => void
  projectToken: string
  projectTitle: string
  monitoringSession?: MonitoringSession | null
  monitoringData?: ScrapedRecord[]
}

export default function AnalyticsModal({
  isOpen,
  onClose,
  projectToken,
  projectTitle,
  monitoringSession,
  monitoringData = [],
}: AnalyticsModalProps) {
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [refreshCount, setRefreshCount] = useState(0)

  const fetchAnalytics = useCallback(async (showLoading = true, forceRefresh = false) => {
    // If monitoring session is active, use live data instead
    if (monitoringSession?.status === 'active') {
      return
    }
    
    if (showLoading) {
      setLoading(true)
    }
    setError(null)
    try {
      const forceParam = forceRefresh ? '&force=true' : ''
      const response = await fetch(`/api/analytics?token=${projectToken}${forceParam}`)
      if (response.ok) {
        const data = await response.json()
        console.log('Analytics fetched:', data)
        setAnalytics(data)
      } else {
        console.error('Analytics fetch failed:', response.status)
        setError('Failed to load analytics')
      }
    } catch (err) {
      console.error('Error fetching analytics:', err)
      setError('Failed to load analytics data')
    } finally {
      if (showLoading) {
        setLoading(false)
      }
    }
  }, [projectToken, monitoringSession?.status])

  useEffect(() => {
    if (!isOpen) {
      return
    }
    
    // Force refresh on initial open
    fetchAnalytics(true, true)
    // Auto-refresh every 3 seconds while modal is open
    const interval = setInterval(() => {
      setRefreshCount(c => c + 1)
    }, 3000)
    return () => clearInterval(interval)
  }, [isOpen, projectToken, fetchAnalytics])

  // Refresh when refresh count changes
  useEffect(() => {
    if (isOpen && refreshCount > 0) {
      fetchAnalytics(false, false) // silent refresh, use cache
    }
  }, [refreshCount, isOpen, fetchAnalytics])

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`${projectTitle} - Analytics Dashboard`}
      size="large"
    >
      {/* Refresh Controls */}
      <div className="mb-4 flex gap-2">
        <button
          onClick={() => fetchAnalytics(true)}
          disabled={loading}
          className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 rounded font-semibold transition-all"
        >
          {loading ? '⏳ Loading...' : '🔄 Refresh'}
        </button>
        {error && (
          <button
            onClick={() => setError(null)}
            className="px-3 py-1 text-sm bg-slate-600 hover:bg-slate-500 rounded text-slate-200 transition-all"
          >
            ✕ Dismiss Error
          </button>
        )}
      </div>

      {/* Real-time Monitoring Section */}
      {monitoringSession && (
        <div className="mb-6 bg-gradient-to-r from-green-500/20 to-blue-500/20 border border-green-500/30 rounded-lg p-4">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="font-semibold text-white flex items-center gap-2">
                <span className="inline-block w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                Real-Time Monitoring
              </h3>
              <p className="text-sm text-slate-400 mt-1">Status: {monitoringSession.status}</p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-green-400">{monitoringData.length}</p>
              <p className="text-xs text-slate-400">Records Scraped</p>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <p className="text-xs text-slate-400 mb-1">Progress</p>
              <p className="text-lg font-bold text-blue-400">{monitoringSession.progressPercentage?.toFixed(1) || 0}%</p>
            </div>
            <div>
              <p className="text-xs text-slate-400 mb-1">Pages</p>
              <p className="text-lg font-bold text-purple-400">{monitoringSession.totalPages}/{monitoringSession.targetPages}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400 mb-1">Current Page</p>
              <p className="text-lg font-bold text-yellow-400">{monitoringData[monitoringData.length - 1]?.pageNumber || 0}</p>
            </div>
          </div>
          
          <div className="bg-slate-700 rounded-full h-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-green-500 to-blue-500 h-full transition-all"
              style={{
                width: `${Math.min(monitoringSession.progressPercentage || 0, 100)}%`,
              }}
            ></div>
          </div>
          
          {monitoringSession.currentUrl && (
            <p className="text-xs text-slate-400 mt-3 truncate">
              Current URL: {monitoringSession.currentUrl}
            </p>
          )}
          
          {monitoringSession.errorMessage && (
            <p className="text-xs text-red-400 mt-2">
              Error: {monitoringSession.errorMessage}
            </p>
          )}
        </div>
      )}

      {loading && !monitoringSession ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
          <p className="text-slate-400 ml-4">Loading analytics...</p>
        </div>
      ) : error ? (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400">
          {error}
        </div>
      ) : analytics ? (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
              <p className="text-slate-400 text-xs mb-1">Total Runs</p>
              <p className="text-2xl font-bold text-blue-400">
                {analytics.overview?.total_runs || 0}
              </p>
            </div>
            <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
              <p className="text-slate-400 text-xs mb-1">Completed</p>
              <p className="text-2xl font-bold text-green-400">
                {analytics.overview?.completed_runs || 0}
              </p>
            </div>
            <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
              <p className="text-slate-400 text-xs mb-1">Total Records</p>
              <p className="text-2xl font-bold text-purple-400">
                {(analytics.overview?.total_records_scraped || 0).toLocaleString()}
              </p>
            </div>
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
              <p className="text-slate-400 text-xs mb-1">Avg Duration</p>
              <p className="text-2xl font-bold text-yellow-400">
                {(analytics.performance?.average_run_duration_seconds || 0).toFixed(0)}s
              </p>
            </div>
          </div>

          {/* Success Rate */}
          {(analytics.overview?.total_runs || 0) > 0 && (
            <div className="bg-slate-700/20 rounded-lg p-4 border border-slate-700">
              <h3 className="font-semibold text-white mb-3">Success Rate</h3>
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <div className="bg-slate-700 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-green-500 h-full"
                      style={{
                        width: `${((analytics.overview?.completed_runs || 0) / (analytics.overview?.total_runs || 1)) * 100}%`,
                      }}
                    ></div>
                  </div>
                </div>
                <p className="text-sm font-semibold text-slate-200">
                  {(
                    ((analytics.overview?.completed_runs || 0) / (analytics.overview?.total_runs || 1)) *
                    100
                  ).toFixed(0)}
                  %
                </p>
              </div>
            </div>
          )}

          {/* Performance Metrics */}
          <div className="bg-slate-700/20 rounded-lg p-4 border border-slate-700">
            <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Performance Metrics
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Items Per Minute</span>
                <span className="text-slate-200 font-mono">
                  {(analytics.performance?.items_per_minute || 0).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Current Items Count</span>
                <span className="text-slate-200 font-mono">
                  {(analytics.performance?.current_items_count || 0).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Estimated Total</span>
                <span className="text-slate-200 font-mono">
                  {(analytics.performance?.estimated_total_items || 0).toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Recovery Status */}
          <div className="bg-slate-700/20 rounded-lg p-4 border border-slate-700">
            <h3 className="font-semibold text-white mb-3">Recovery Status</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Auto-Recovery</span>
                <span className={`text-slate-200 font-mono ${analytics.recovery?.in_recovery ? 'text-yellow-400' : 'text-green-400'}`}>
                  {analytics.recovery?.in_recovery ? 'Active' : 'Standby'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Status</span>
                <span className="text-slate-200 font-mono text-xs">
                  {analytics.recovery?.status || 'normal'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Recovery Attempts</span>
                <span className="text-slate-200 font-mono">
                  {analytics.recovery?.total_recovery_attempts || 0}
                </span>
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-3">
              📍 System automatically detects when scraping stops and triggers recovery from the last scraped page.
            </p>
          </div>

          {/* Data Quality */}
          <div className="bg-slate-700/20 rounded-lg p-4 border border-slate-700">
            <h3 className="font-semibold text-white mb-3">Data Quality</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Average Completion</span>
                <span className="text-slate-200 font-mono">
                  {(analytics.data_quality?.average_completion_percentage || 0).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Total Fields</span>
                <span className="text-slate-200 font-mono">
                  {analytics.data_quality?.total_fields || 0}
                </span>
              </div>
            </div>
            <div className="mt-3 bg-slate-700 rounded-full h-2 overflow-hidden">
              <div
                className="bg-green-500 h-full"
                style={{ width: `${analytics.data_quality?.average_completion_percentage || 0}%` }}
              />
            </div>
          </div>

          {/* Storage Info */}
          <div className="bg-slate-700/20 rounded-lg p-4 border border-slate-700">
            <h3 className="font-semibold text-white text-sm mb-2">Database Storage</h3>
            <p className="text-xs text-slate-400">
              All project data is automatically stored in SQLite database for persistent analytics, recovery tracking, and deduplication.
            </p>
          </div>

          {/* Export Button */}
          <button
            onClick={() => downloadAnalyticsReport(analytics, projectTitle)}
            className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
          >
            📥 Download Full Report
          </button>
        </div>
      ) : null}
    </Modal>
  )
}

function downloadAnalyticsReport(analytics: Analytics, projectTitle: string) {
  const timestamp = new Date().toLocaleString()
  const csv = [
    'PARSEHUB ANALYTICS REPORT',
    `Project: ${projectTitle}`,
    `Generated: ${timestamp}`,
    '',
    '═══════════════════════════════════════',
    'OVERVIEW',
    '═══════════════════════════════════════',
    `Total Runs,${analytics.overview?.total_runs || 0}`,
    `Completed Runs,${analytics.overview?.completed_runs || 0}`,
    `Total Records Scraped,${analytics.overview?.total_records_scraped || 0}`,
    `Progress (%),${(analytics.overview?.progress_percentage || 0).toFixed(2)}`,
    `Success Rate (%),${((analytics.overview?.completed_runs || 0) / (analytics.overview?.total_runs || 1) * 100).toFixed(2)}`,
    '',
    '═══════════════════════════════════════',
    'PERFORMANCE',
    '═══════════════════════════════════════',
    `Items Per Minute,${(analytics.performance?.items_per_minute || 0).toFixed(2)}`,
    `Current Items Count,${analytics.performance?.current_items_count || 0}`,
    `Estimated Total Items,${analytics.performance?.estimated_total_items || 0}`,
    `Average Duration (seconds),${(analytics.performance?.average_run_duration_seconds || 0).toFixed(2)}`,
    '',
    '═══════════════════════════════════════',
    'DATA QUALITY',
    '═══════════════════════════════════════',
    `Average Completion (%),${(analytics.data_quality?.average_completion_percentage || 0).toFixed(2)}`,
    `Total Fields,${analytics.data_quality?.total_fields || 0}`,
    '',
    '═══════════════════════════════════════',
    'RECOVERY',
    '═══════════════════════════════════════',
    `In Recovery,${analytics.recovery?.in_recovery ? 'Yes' : 'No'}`,
    `Status,${analytics.recovery?.status || 'normal'}`,
    `Total Recovery Attempts,${analytics.recovery?.total_recovery_attempts || 0}`,
    ''
  ].join('\n')

  const blob = new Blob([csv], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `analytics-${projectTitle}-${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  window.URL.revokeObjectURL(url)
}
