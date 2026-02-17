'use client'

import { useState, useEffect } from 'react'
import { Activity, TrendingUp, Download, Zap, RefreshCw } from 'lucide-react'
import Modal from './Modal'

interface ProjectData {
  token: string
  title: string
  owner_email: string
  last_run?: {
    status: string
    pages: number
    start_time: string
    end_time?: string
    run_token: string
  } | null
  analytics?: {
    overview?: {
      total_runs: number
      completed_runs: number
      total_records_scraped: number
      progress_percentage: number
    }
  }
}

interface AllProjectsAnalyticsModalProps {
  isOpen: boolean
  onClose: () => void
  projects: ProjectData[]
}

export default function AllProjectsAnalyticsModal({
  isOpen,
  onClose,
  projects,
}: AllProjectsAnalyticsModalProps) {
  const [projectsWithAnalytics, setProjectsWithAnalytics] = useState<ProjectData[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'all' | 'summary' | 'progress'>('all')
  const [runningProjects, setRunningProjects] = useState<ProjectData[]>([])
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (isOpen && projects.length > 0) {
      fetchAllAnalytics()
      fetchRunningProjects()
    }
  }, [isOpen, projects])

  // Auto-refresh progress for running projects every 3 seconds
  useEffect(() => {
    if (isOpen && activeTab === 'progress') {
      const interval = setInterval(() => {
        fetchRunningProjects()
      }, 3000)
      setRefreshInterval(interval)
      return () => {
        clearInterval(interval)
      }
    }
    return void 0
  }, [isOpen, activeTab])

  // Clean up interval on unmount
  useEffect(() => {
    return () => {
      if (refreshInterval) clearInterval(refreshInterval)
    }
  }, [refreshInterval])

  const fetchRunningProjects = async () => {
    try {
      const response = await fetch('/api/projects')
      if (response.ok) {
        const data = await response.json()
        const running = (data.projects || []).filter(
          (p: ProjectData) => p.last_run?.status === 'running'
        )
        setRunningProjects(running)
      }
    } catch (err) {
      console.warn('Failed to fetch running projects:', err)
    }
  }

  const fetchAllAnalytics = async () => {
    setLoading(true)
    try {
      const projectsData = await Promise.all(
        projects.map(async (project) => {
          try {
            const response = await fetch(`/api/analytics?token=${project.token}`)
            if (response.ok) {
              const analytics = await response.json()
              return {
                ...project,
                analytics,
              }
            }
            return project
          } catch (err) {
            console.warn(`Failed to fetch analytics for ${project.token}:`, err)
            return project
          }
        })
      )
      setProjectsWithAnalytics(projectsData)
      // Also fetch running projects on analytics load
      fetchRunningProjects()
    } finally {
      setLoading(false)
    }
  }

  const calculateTotalStats = () => {
    let totalProjects = projects.length
    let totalRuns = 0
    let totalRecords = 0
    let completedRuns = 0

    projectsWithAnalytics.forEach((project) => {
      if (project.analytics?.overview) {
        totalRuns += project.analytics.overview.total_runs || 0
        totalRecords += project.analytics.overview.total_records_scraped || 0
        completedRuns += project.analytics.overview.completed_runs || 0
      }
    })

    return { totalProjects, totalRuns, totalRecords, completedRuns }
  }

  const downloadAnalyticsReport = () => {
    const stats = calculateTotalStats()
    const projectDetails = projectsWithAnalytics.map(p => ({
      name: p.title,
      token: p.token,
      owner: p.owner_email,
      lastRun: p.last_run?.start_time,
      lastRunStatus: p.last_run?.status,
      pagesScraped: p.last_run?.pages,
      totalRecords: p.analytics?.overview?.total_records_scraped || 0,
      totalRuns: p.analytics?.overview?.total_runs || 0,
      completedRuns: p.analytics?.overview?.completed_runs || 0,
    }))

    const report = {
      timestamp: new Date().toISOString(),
      summary: stats,
      projects: projectDetails,
    }

    const dataStr = JSON.stringify(report, null, 2)
    const element = document.createElement('a')
    element.setAttribute('href', 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr))
    element.setAttribute('download', `all-projects-analytics-${Date.now()}.json`)
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  if (!isOpen) return null

  const stats = calculateTotalStats()

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="All Projects Analytics" size="xlarge">
      <div className="space-y-4">
        {/* Tab Navigation */}
        <div className="flex gap-2 border-b border-gray-300 -mx-6 px-6 overflow-x-auto">
          <button
            onClick={() => setActiveTab('summary')}
            className={`py-3 px-4 font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === 'summary'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            Summary
          </button>
          <button
            onClick={() => setActiveTab('all')}
            className={`py-3 px-4 font-medium border-b-2 transition whitespace-nowrap ${
              activeTab === 'all'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            All Projects ({projects.length})
          </button>
          <button
            onClick={() => setActiveTab('progress')}
            className={`py-3 px-4 font-medium border-b-2 transition whitespace-nowrap flex items-center gap-1 ${
              activeTab === 'progress'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            <Zap className="w-4 h-4" />
            Progress ({runningProjects.length})
          </button>
        </div>

        {/* Summary Tab */}
        {activeTab === 'summary' && (
          <div className="space-y-4">
            {/* Top Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-4 h-4 text-blue-600" />
                  <p className="text-xs text-blue-600 font-medium">Total Projects</p>
                </div>
                <p className="text-3xl font-bold text-blue-900">{stats.totalProjects}</p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-4 h-4 text-green-600" />
                  <p className="text-xs text-green-600 font-medium">Total Runs</p>
                </div>
                <p className="text-3xl font-bold text-green-900">{stats.totalRuns}</p>
              </div>

              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-4 h-4 text-purple-600" />
                  <p className="text-xs text-purple-600 font-medium">Completed Runs</p>
                </div>
                <p className="text-3xl font-bold text-purple-900">{stats.completedRuns}</p>
              </div>

              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-4 h-4 text-orange-600" />
                  <p className="text-xs text-orange-600 font-medium">Total Records</p>
                </div>
                <p className="text-3xl font-bold text-orange-900">{stats.totalRecords.toLocaleString()}</p>
              </div>
            </div>

            {/* Breakdown by Project */}
            <div className="mt-6">
              <h3 className="font-semibold text-gray-800 mb-3">Records Per Project</h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {projectsWithAnalytics
                  .sort((a, b) => (b.analytics?.overview?.total_records_scraped || 0) - (a.analytics?.overview?.total_records_scraped || 0))
                  .map((project) => {
                    const recordCount = project.analytics?.overview?.total_records_scraped || 0
                    const percentage = stats.totalRecords > 0 ? ((recordCount / stats.totalRecords) * 100) : 0

                    return (
                      <div key={project.token} className="flex items-center gap-3">
                        <div className="flex-1">
                          <div className="flex justify-between mb-1">
                            <span className="text-sm font-medium text-gray-700 truncate">{project.title}</span>
                            <span className="text-sm font-bold text-gray-900">{recordCount.toLocaleString()}</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${percentage}%` }}
                            ></div>
                          </div>
                        </div>
                        <span className="text-xs text-gray-600 min-w-12 text-right">{percentage.toFixed(1)}%</span>
                      </div>
                    )
                  })}
              </div>
            </div>

            <button
              onClick={downloadAnalyticsReport}
              className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition"
            >
              <Download className="w-4 h-4" />
              Download Full Report
            </button>
          </div>
        )}

        {/* All Projects Tab */}
        {activeTab === 'all' && (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              </div>
            ) : projectsWithAnalytics.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No projects available
              </div>
            ) : (
              projectsWithAnalytics.map((project) => {
                const isRunning = runningProjects.some(rp => rp.token === project.token)
                return (
                <div
                  key={project.token}
                  className={`border rounded-lg p-4 hover:border-blue-400 transition ${
                    isRunning
                      ? 'bg-orange-50 border-orange-300'
                      : 'bg-gray-50 border-gray-300'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-gray-800">{project.title}</h4>
                        {isRunning && (
                          <span className="flex items-center gap-1 px-2 py-1 bg-orange-200 text-orange-800 rounded-full text-xs font-medium">
                            <Zap className="w-3 h-3" />
                            RUNNING
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 mt-1">Owner: {project.owner_email}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-blue-600">
                        {project.analytics?.overview?.total_records_scraped || 0}
                      </p>
                      <p className="text-xs text-gray-600">Records</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 mt-3 text-xs">
                    <div className="bg-white p-2 rounded border border-gray-200">
                      <p className="text-gray-600">Total Runs</p>
                      <p className="font-bold text-gray-800">{project.analytics?.overview?.total_runs || 0}</p>
                    </div>
                    <div className="bg-white p-2 rounded border border-gray-200">
                      <p className="text-gray-600">Completed</p>
                      <p className="font-bold text-green-600">{project.analytics?.overview?.completed_runs || 0}</p>
                    </div>
                    <div className="bg-white p-2 rounded border border-gray-200">
                      <p className="text-gray-600">Last Status</p>
                      <p className={`font-bold capitalize ${isRunning ? 'text-orange-600' : 'text-gray-800'}`}>
                        {isRunning ? `Running (${project.last_run?.pages || 0} pages)` : project.last_run?.status || 'N/A'}
                      </p>
                    </div>
                  </div>

                  {project.last_run?.start_time && (
                    <p className="text-xs text-gray-500 mt-2">
                      Last run: {new Date(project.last_run.start_time).toLocaleDateString()} at{' '}
                      {new Date(project.last_run.start_time).toLocaleTimeString()}
                    </p>
                  )}
                </div>
                )
              })
            )}
          </div>
        )}

        {/* Progress Tab - Real-time Running Projects */}
        {activeTab === 'progress' && (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm font-semibold text-gray-700">
                  {runningProjects.length === 0 ? 'No projects running' : `${runningProjects.length} project${runningProjects.length !== 1 ? 's' : ''} running`}
                </p>
                <p className="text-xs text-gray-500">Page counts update every 3 seconds</p>
              </div>
              <button
                onClick={fetchRunningProjects}
                className="p-2 hover:bg-gray-100 rounded-lg transition"
                title="Refresh now"
              >
                <RefreshCw className="w-4 h-4 text-blue-600" />
              </button>
            </div>

            {runningProjects.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <Zap className="w-12 h-12 text-gray-300 mb-3" />
                <p className="text-gray-500 font-medium">No projects running</p>
                <p className="text-xs text-gray-400 mt-1">Projects will appear here when they start running</p>
              </div>
            ) : (
              runningProjects.map((project) => {
                const pages = project.last_run?.pages || 0
                const estimatedPages = Math.max(pages, 10) // Use page count as estimate
                const progressPercent = Math.min((pages / estimatedPages) * 100, 95) // Cap at 95% until completed

                return (
                  <div
                    key={project.token}
                    className="bg-gradient-to-r from-orange-50 to-orange-50 border border-orange-300 rounded-lg p-4"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Zap className="w-4 h-4 text-orange-600 animate-pulse" />
                          <h4 className="font-semibold text-gray-800">{project.title}</h4>
                        </div>
                        <p className="text-xs text-gray-600">Token: {project.token.substring(0, 8)}...</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold text-orange-600">{pages}</p>
                        <p className="text-xs text-gray-600">pages scraped</p>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="space-y-1">
                      <div className="w-full bg-orange-200 rounded-full h-3 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-orange-500 to-orange-600 h-3 rounded-full transition-all duration-500 animate-pulse"
                          style={{ width: `${progressPercent}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-600 text-right">{progressPercent.toFixed(0)}% in progress</p>
                    </div>

                    {/* Start Time */}
                    {project.last_run?.start_time && (
                      <p className="text-xs text-gray-500 mt-2">
                        Started: {new Date(project.last_run.start_time).toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                )
              })
            )}
          </div>
        )}
      </div>
    </Modal>
  )
}

