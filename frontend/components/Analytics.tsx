'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, Activity } from 'lucide-react'
import StatisticsTable from './StatisticsTable'
import DataViewer from './DataViewer'

interface AnalyticsData {
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

interface AnalyticsProps {
  projectToken: string
}

export default function Analytics({ projectToken }: AnalyticsProps) {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'quality' | 'recovery' | 'statistics' | 'data'>('overview')

  useEffect(() => {
    fetchAnalytics()
    const interval = setInterval(fetchAnalytics, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [projectToken])

  const fetchAnalytics = async () => {
    try {
      setError(null)
      console.log('Fetching analytics for token:', projectToken)
      const response = await fetch(`/api/analytics?token=${projectToken}`)
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`)
      }
      
      const data = await response.json()
      console.log('Analytics data received:', data)
      
      if (data.error) {
        throw new Error(data.error)
      }
      
      setAnalytics(data)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch analytics'
      console.error('Failed to fetch analytics:', message)
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <h3 className="text-lg font-semibold text-red-800 mb-2">⚠️ Error Loading Analytics</h3>
        <p className="text-red-700 mb-4">{error}</p>
        <p className="text-sm text-red-600 mb-4">
          Troubleshooting steps:
        </p>
        <ul className="text-sm text-red-600 list-disc list-inside mb-4 space-y-1">
          <li>Make sure the backend Python environment is set up correctly</li>
          <li>Verify the database file exists at backend/parsehub.db</li>
          <li>Check that the project token is valid</li>
          <li>Try refreshing the page or clicking Analyze again</li>
        </ul>
        <button
          onClick={fetchAnalytics}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
        >
          🔄 Retry
        </button>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-500">Loading analytics...</div>
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-red-500">Failed to load analytics</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex gap-2 border-b overflow-x-auto">
        {(['overview', 'performance', 'quality', 'statistics', 'data', 'recovery'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium capitalize transition-colors whitespace-nowrap ${
              activeTab === tab
                ? 'text-purple-600 border-b-2 border-purple-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MetricCard
            title="Total Runs"
            value={analytics.overview.total_runs}
          />
          <MetricCard
            title="Completed Runs"
            value={analytics.overview.completed_runs}
          />
          <MetricCard
            title="Total Records"
            value={analytics.overview.total_records_scraped}
          />
          <MetricCard
            title="Progress"
            value={`${analytics.overview.progress_percentage}%`}
          />

          {/* Progress Bar */}
          <div className="col-span-full">
            <div className="bg-white rounded-lg p-4">
              <h3 className="font-medium mb-2">Scraping Progress</h3>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-purple-600 h-4 rounded-full transition-all"
                  style={{ width: `${analytics.overview.progress_percentage}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 mt-2">
                {analytics.overview.progress_percentage}% complete
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Performance Tab */}
      {activeTab === 'performance' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MetricCard
            title="Items Per Minute"
            value={analytics.performance.items_per_minute}
          />
          <MetricCard
            title="Current Count"
            value={analytics.performance.current_items_count}
          />
          <MetricCard
            title="Estimated Total"
            value={analytics.performance.estimated_total_items}
          />
          <MetricCard
            title="Avg Duration (sec)"
            value={Math.round(analytics.performance.average_run_duration_seconds)}
          />

          {/* Rate Chart */}
          <div className="col-span-full bg-white rounded-lg p-4">
            <h3 className="font-medium mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Scraping Rate
            </h3>
            <div className="text-center py-4">
              <div className="text-3xl font-bold text-purple-600">
                {analytics.performance.items_per_minute}
              </div>
              <p className="text-gray-600">items per minute</p>
            </div>
          </div>
        </div>
      )}

      {/* Data Quality Tab */}
      {activeTab === 'quality' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MetricCard
            title="Average Completion"
            value={`${analytics.data_quality.average_completion_percentage}%`}
          />
          <MetricCard
            title="Total Fields"
            value={analytics.data_quality.total_fields}
          />

          {/* Quality Gauge */}
          <div className="col-span-full bg-white rounded-lg p-4">
            <h3 className="font-medium mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Data Quality Overview
            </h3>
            <div className="space-y-3">
              <QualityBar
                label="Field Completion"
                value={analytics.data_quality.average_completion_percentage}
              />
            </div>
          </div>
        </div>
      )}

      {/* Recovery Tab */}
      {activeTab === 'recovery' && (
        <div className="space-y-4">
          <div className="bg-white rounded-lg p-4">
            <h3 className="font-medium mb-3">Recovery Status</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <p className="font-semibold capitalize">
                  {analytics.recovery.in_recovery ? '🔄 In Recovery' : '✓ Normal'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Attempts</p>
                <p className="font-semibold">{analytics.recovery.total_recovery_attempts}</p>
              </div>
            </div>
          </div>

          {/* Timeline */}
          {analytics.timeline && analytics.timeline.length > 0 && (
            <div className="bg-white rounded-lg p-4">
              <h3 className="font-medium mb-3">Event Timeline</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {analytics.timeline.slice(0, 10).map((event, idx) => (
                  <div key={idx} className="text-sm border-l-2 border-purple-300 pl-3 py-1">
                    <p className="text-gray-600 text-xs">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                    <p className="font-medium capitalize">{event.type.replace(/_/g, ' ')}</p>
                    {event.details && <p className="text-gray-700">{event.details}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Statistics Tab */}
      {activeTab === 'statistics' && (
        <div className="bg-white rounded-lg p-4">
          <h3 className="font-medium mb-4">Field Statistics</h3>
          <StatisticsTable projectToken={projectToken} />
        </div>
      )}

      {/* Data Tab */}
      {activeTab === 'data' && (
        <div className="bg-white rounded-lg p-4">
          <h3 className="font-medium mb-4">Scraped Data</h3>
          <DataViewer projectToken={projectToken} />
        </div>
      )}

      {/* Export Button */}
      <button
        onClick={() => downloadAnalytics(analytics)}
        className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium transition-colors"
      >
        📥 Download Report
      </button>
    </div>
  )
}

// Sub-components
function MetricCard({
  title,
  value
}: {
  title: string
  value: string | number
}) {
  return (
    <div className="bg-white rounded-lg p-4">
      <p className="text-sm text-gray-600 mb-1">{title}</p>
      <p className="text-2xl font-bold text-purple-600">{value}</p>
    </div>
  )
}

function QualityBar({ label, value }: { label: string; value: number }) {
  const color =
    value >= 80 ? 'bg-green-500' : value >= 60 ? 'bg-yellow-500' : 'bg-red-500'

  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-sm font-semibold">{value}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div className={`${color} h-2 rounded-full`} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

function downloadAnalytics(analytics: AnalyticsData) {
  const csv = generateCSV(analytics)
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `analytics-${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  window.URL.revokeObjectURL(url)
}

function generateCSV(analytics: AnalyticsData): string {
  const lines = [
    'ParseHub Analytics Report',
    `Generated: ${new Date().toLocaleString()}`,
    '',
    '=== OVERVIEW ===',
    `Total Runs,${analytics.overview.total_runs}`,
    `Completed Runs,${analytics.overview.completed_runs}`,
    `Total Records,${analytics.overview.total_records_scraped}`,
    `Progress,%,${analytics.overview.progress_percentage}`,
    '',
    '=== PERFORMANCE ===',
    `Items Per Minute,${analytics.performance.items_per_minute}`,
    `Current Count,${analytics.performance.current_items_count}`,
    `Estimated Total,${analytics.performance.estimated_total_items}`,
    '',
    '=== DATA QUALITY ===',
    `Average Completion,%,${analytics.data_quality.average_completion_percentage}`,
    `Total Fields,${analytics.data_quality.total_fields}`
  ]
  return lines.join('\n')
}
