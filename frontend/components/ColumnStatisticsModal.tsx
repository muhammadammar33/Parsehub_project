'use client'

import { useState, useEffect } from 'react'
import { Download, BarChart3 } from 'lucide-react'
import Modal from './Modal'

interface ColumnStatisticsModalProps {
  token: string
  title: string
  isOpen: boolean
  onClose: () => void
}

interface ColumnStats {
  [columnName: string]: {
    [value: string]: number
  }
}

export default function ColumnStatisticsModal({ token, title, isOpen, onClose }: ColumnStatisticsModalProps) {
  const [stats, setStats] = useState<ColumnStats>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && token) {
      fetchAndAnalyzeCSV()
    }
  }, [isOpen, token])

  const fetchAndAnalyzeCSV = async () => {
    setLoading(true)
    setError(null)
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000)

      try {
        const response = await fetch(`/api/analytics?token=${token}&force=true`, {
          signal: controller.signal
        })

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`)
        }

        const result = await response.json()

        if (!result.csv_data) {
          setError('No CSV data found for this project. Try running the project first.')
          setStats({})
          return
        }

        // Parse CSV and calculate statistics
        const columnStats = parseCSVAndCalculateStats(result.csv_data)
        setStats(columnStats)

        // Auto-select first column
        const columns = Object.keys(columnStats)
        if (columns.length > 0) {
          setSelectedColumn(columns[0])
        }
      } finally {
        clearTimeout(timeoutId)
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        setError('Request timed out. The server might be busy.')
      } else {
        setError(err instanceof Error ? err.message : 'Failed to fetch data')
      }
      setStats({})
    } finally {
      setLoading(false)
    }
  }

  const parseCSVAndCalculateStats = (csv: string): ColumnStats => {
    const lines = csv.trim().split('\n')
    if (lines.length < 2) return {}

    const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''))
    const columnStats: ColumnStats = {}

    // Initialize column stats
    headers.forEach(header => {
      columnStats[header] = {}
    })

    // Process each row and count values
    for (let i = 1; i < lines.length; i++) {
      if (!lines[i].trim()) continue

      const values: string[] = []
      let current = ''
      let inQuotes = false

      for (let j = 0; j < lines[i].length; j++) {
        const char = lines[i][j]
        if (char === '"') {
          inQuotes = !inQuotes
        } else if (char === ',' && !inQuotes) {
          values.push(current.trim().replace(/^"|"$/g, ''))
          current = ''
        } else {
          current += char
        }
      }
      values.push(current.trim().replace(/^"|"$/g, ''))

      // Count values for each column
      headers.forEach((header, index) => {
        const value = values[index] || 'N/A'
        const displayValue = value.length > 50 ? value.substring(0, 50) + '...' : value
        columnStats[header][displayValue] = (columnStats[header][displayValue] || 0) + 1
      })
    }

    // Sort values by count (descending)
    Object.keys(columnStats).forEach(column => {
      const sorted = Object.entries(columnStats[column])
        .sort((a, b) => b[1] - a[1])
        .reduce((acc, [value, count]) => {
          acc[value] = count
          return acc
        }, {} as Record<string, number>)
      columnStats[column] = sorted
    })

    return columnStats
  }

  const downloadStatisticsAsJSON = () => {
    const dataStr = JSON.stringify(stats, null, 2)
    const element = document.createElement('a')
    element.setAttribute('href', 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr))
    element.setAttribute('download', `${token}-statistics.json`)
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  const getTotalRecordCount = (): number => {
    if (Object.keys(stats).length === 0) return 0
    const firstColumn = Object.keys(stats)[0]
    return Object.values(stats[firstColumn]).reduce((a, b) => a + b, 0)
  }

  if (!isOpen) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Data Statistics - ${title}`} size="xlarge">
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      ) : error ? (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          Error: {error}
        </div>
      ) : Object.keys(stats).length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No statistical data available
        </div>
      ) : (
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              <span className="font-medium text-gray-700">
                Total Records: <span className="font-bold text-lg">{getTotalRecordCount()}</span>
              </span>
              <span className="text-gray-600 text-sm">
                ({Object.keys(stats).length} columns)
              </span>
            </div>
            <button
              onClick={downloadStatisticsAsJSON}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition"
            >
              <Download className="w-4 h-4" />
              Download Stats
            </button>
          </div>

          {/* Column Selector */}
          <div className="border-b border-gray-300 -mx-6 px-6 py-4 bg-gray-50">
            <label className="text-sm font-medium text-gray-700 block mb-2">Select Column to View:</label>
            <select
              value={selectedColumn || ''}
              onChange={(e) => setSelectedColumn(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            >
              <option value="">-- Choose a column --</option>
              {Object.keys(stats).map(column => (
                <option key={column} value={column}>
                  {column} ({Object.keys(stats[column]).length} unique values)
                </option>
              ))}
            </select>
          </div>

          {/* Statistics Table */}
          {selectedColumn && stats[selectedColumn] ? (
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-800">
                {selectedColumn}
                <span className="text-sm font-normal text-gray-600 ml-2">
                  ({Object.keys(stats[selectedColumn]).length} unique values)
                </span>
              </h3>

              <div className="overflow-x-auto border border-gray-300 rounded-lg max-h-96 overflow-y-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-gray-100 border-b border-gray-300 sticky top-0">
                      <th className="px-4 py-2 text-left text-sm font-semibold text-gray-800 border-r border-gray-300">
                        Value
                      </th>
                      <th className="px-4 py-2 text-right text-sm font-semibold text-gray-800 min-w-24">
                        Count
                      </th>
                      <th className="px-4 py-2 text-right text-sm font-semibold text-gray-800 min-w-28">
                        Percentage
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(stats[selectedColumn]).map(([value, count], index) => {
                      const total = Object.values(stats[selectedColumn]).reduce((a, b) => a + b, 0)
                      const percentage = ((count / total) * 100).toFixed(2)

                      return (
                        <tr
                          key={index}
                          className={`border-b border-gray-200 hover:bg-blue-50 transition ${
                            index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                          }`}
                        >
                          <td className="px-4 py-2 text-sm text-gray-800 font-mono break-words border-r border-gray-300">
                            {value}
                          </td>
                          <td className="px-4 py-2 text-right text-sm font-semibold text-gray-900">
                            {count}
                          </td>
                          <td className="px-4 py-2 text-right text-sm">
                            <div className="flex items-center justify-end gap-2">
                              <div className="w-24 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-blue-600 h-2 rounded-full transition-all"
                                  style={{ width: `${percentage}%` }}
                                ></div>
                              </div>
                              <span className="text-gray-600 min-w-12 text-right">{percentage}%</span>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {/* Summary Stats */}
              <div className="grid grid-cols-3 gap-3 mt-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-xs text-blue-600 font-medium mb-1">Total Count</p>
                  <p className="text-2xl font-bold text-blue-900">
                    {Object.values(stats[selectedColumn]).reduce((a, b) => a + b, 0)}
                  </p>
                </div>
                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                  <p className="text-xs text-green-600 font-medium mb-1">Unique Values</p>
                  <p className="text-2xl font-bold text-green-900">
                    {Object.keys(stats[selectedColumn]).length}
                  </p>
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                  <p className="text-xs text-purple-600 font-medium mb-1">Most Common</p>
                  <p className="font-bold text-purple-900 text-sm truncate">
                    {Object.entries(stats[selectedColumn])[0]?.[0] || 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              Select a column to view statistics
            </div>
          )}
        </div>
      )}
    </Modal>
  )
}
