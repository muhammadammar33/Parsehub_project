'use client'

import { useState } from 'react'
import { ChevronDown, Play, Clock, BarChart3, FileJson } from 'lucide-react'
import SchedulerModal from './SchedulerModal'
import ColumnStatisticsModal from './ColumnStatisticsModal'
import CSVDataModal from './CSVDataModal'

interface Project {
  token: string
  name?: string
}

interface BrandCollapsibleProps {
  brand: string
  projects: Project[]
  onRunAll: (brand: string) => Promise<void>
  onRunProject: (token: string) => Promise<void>
}

export default function BrandCollapsible({
  brand,
  projects,
  onRunAll,
  onRunProject,
}: BrandCollapsibleProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [pageInputs, setPageInputs] = useState<{ [key: string]: string }>({})
  const [loading, setLoading] = useState(false)
  const [showScheduler, setShowScheduler] = useState(false)
  const [selectedProjectForSchedule, setSelectedProjectForSchedule] = useState<string | null>(null)
  const [showStatsModal, setShowStatsModal] = useState(false)
  const [showCSVModal, setShowCSVModal] = useState(false)
  const [selectedProjectToken, setSelectedProjectToken] = useState<string | null>(null)
  const [selectedProjectName, setSelectedProjectName] = useState<string | null>(null)

  const handlePageChange = (token: string, value: string) => {
    setPageInputs(prev => ({
      ...prev,
      [token]: value
    }))
  }

  const handleRunAll = async () => {
    setLoading(true)
    try {
      await onRunAll(brand)
    } finally {
      setLoading(false)
    }
  }

  const handleRunProject = async (token: string) => {
    setLoading(true)
    try {
      await onRunProject(token)
    } finally {
      setLoading(false)
    }
  }

  const handleScheduleClick = (token: string) => {
    setSelectedProjectForSchedule(token)
    setShowScheduler(true)
  }

  const handleViewStats = (token: string, name: string) => {
    setSelectedProjectToken(token)
    setSelectedProjectName(name)
    setShowStatsModal(true)
  }

  const handleViewCSV = (token: string, name: string) => {
    setSelectedProjectToken(token)
    setSelectedProjectName(name)
    setShowCSVModal(true)
  }

  return (
    <div className="border border-gray-300 rounded-lg mb-4 bg-white shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between bg-gradient-to-r from-blue-50 to-blue-100 hover:from-blue-100 hover:to-blue-200 transition-all"
      >
        <div className="flex items-center gap-3">
          <ChevronDown
            size={20}
            className={`transform transition-transform ${
              isOpen ? 'rotate-180' : ''
            } text-blue-600`}
          />
          <h3 className="text-lg font-semibold text-gray-800">{brand}</h3>
          <span className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-medium">
            {projects.length}
          </span>
        </div>

        {isOpen && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleRunAll()
            }}
            disabled={loading}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            <Play size={16} />
            Run All
          </button>
        )}
      </button>

      {/* Content */}
      {isOpen && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="space-y-4">
            {projects.map((project) => (
              <div
                key={project.token}
                className="bg-white p-4 rounded-lg border border-gray-200 hover:border-blue-400 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-800 mb-2">
                      {project.name}
                    </h4>
                    <p className="text-sm text-gray-600 mb-3">
                      Token: <code className="bg-gray-100 px-2 py-1 rounded text-xs">{project.token}</code>
                    </p>

                    {/* Pages Input */}
                    <div className="mb-3">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Total Pages to Scrape
                      </label>
                      <input
                        type="number"
                        min="1"
                        placeholder="Enter number of pages"
                        value={pageInputs[project.token] || ''}
                        onChange={(e) =>
                          handlePageChange(project.token, e.target.value)
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => handleRunProject(project.token)}
                    disabled={loading}
                    className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                  >
                    <Play size={16} />
                    Run
                  </button>
                  <button
                    onClick={() => handleScheduleClick(project.token)}
                    className="flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                  >
                    <Clock size={16} />
                    Schedule
                  </button>
                  <button
                    onClick={() => handleViewStats(project.token, project.name || '')}
                    className="flex items-center justify-center gap-2 bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                  >
                    <BarChart3 size={16} />
                    Statistics
                  </button>
                  <button
                    onClick={() => handleViewCSV(project.token, project.name || '')}
                    className="flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                  >
                    <FileJson size={16} />
                    View CSV
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scheduler Modal */}
      {showScheduler && selectedProjectForSchedule && (
        <SchedulerModal
          projectToken={selectedProjectForSchedule}
          onClose={() => {
            setShowScheduler(false)
            setSelectedProjectForSchedule(null)
          }}
          onSchedule={(time) => {
            console.log(`Scheduled for ${time}`)
            setShowScheduler(false)
          }}
        />
      )}

      {/* Data Modal */}
      {showStatsModal && selectedProjectToken && selectedProjectName && (
        <ColumnStatisticsModal
          token={selectedProjectToken}
          title={selectedProjectName}
          isOpen={showStatsModal}
          onClose={() => {
            setShowStatsModal(false)
            setSelectedProjectToken(null)
            setSelectedProjectName(null)
          }}
        />
      )}

      {/* CSV Data Modal */}
      {showCSVModal && selectedProjectToken && selectedProjectName && (
        <CSVDataModal
          token={selectedProjectToken}
          title={selectedProjectName}
          isOpen={showCSVModal}
          onClose={() => {
            setShowCSVModal(false)
            setSelectedProjectToken(null)
            setSelectedProjectName(null)
          }}
        />
      )}
    </div>
  )
}
