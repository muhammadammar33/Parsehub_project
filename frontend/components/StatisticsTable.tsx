'use client'

import React, { useState, useEffect } from 'react'
import { BarChart3, Loader, AlertCircle } from 'lucide-react'

interface Field {
  name: string
  total_count: number
  filled_count: number
  empty_count: number
  completion_percentage: number
  unique_count: number
  sample_values: string[]
}

interface StatisticsTableProps {
  projectToken: string
  projectId?: number
  refreshTrigger?: number
}

export default function StatisticsTable({
  projectToken,
  projectId,
  refreshTrigger = 0,
}: StatisticsTableProps) {
  const [statistics, setStatistics] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [sortBy, setSortBy] = useState<'name' | 'completion' | 'unique'>('completion')
  const [sortDesc, setSortDesc] = useState(true)

  useEffect(() => {
    loadStatistics()
  }, [projectToken, projectId, refreshTrigger])

  const loadStatistics = async () => {
    setIsLoading(true)
    setError('')

    try {
      const params = new URLSearchParams()
      if (projectId) {
        params.append('projectId', projectId.toString())
      } else {
        params.append('token', projectToken)
      }

      const response = await fetch(`/api/analytics/statistics?${params.toString()}`)

      if (!response.ok) {
        throw new Error('Failed to load statistics')
      }

      const data = await response.json()
      setStatistics(data.statistics)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader className="w-5 h-5 text-blue-600 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-start gap-2 p-4 bg-red-50 border border-red-200 rounded">
        <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-medium text-red-800">Failed to load statistics</p>
          <p className="text-sm text-red-700 mt-1">{error}</p>
          <button
            onClick={loadStatistics}
            className="text-sm text-red-600 hover:text-red-700 mt-2 font-medium"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (!statistics || !statistics.fields || statistics.fields.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <BarChart3 className="w-8 h-8 mx-auto mb-2 text-gray-400" />
        <p>No data available yet</p>
      </div>
    )
  }

  // Sort fields
  let sortedFields = [...statistics.fields]
  if (sortBy === 'completion') {
    sortedFields.sort((a, b) => {
      const diff = a.completion_percentage - b.completion_percentage
      return sortDesc ? -diff : diff
    })
  } else if (sortBy === 'unique') {
    sortedFields.sort((a, b) => {
      const diff = a.unique_count - b.unique_count
      return sortDesc ? -diff : diff
    })
  } else {
    sortedFields.sort((a, b) => {
      return sortDesc
        ? b.name.localeCompare(a.name)
        : a.name.localeCompare(b.name)
    })
  }

  const handleSort = (field: 'name' | 'completion' | 'unique') => {
    if (sortBy === field) {
      setSortDesc(!sortDesc)
    } else {
      setSortBy(field)
      setSortDesc(true)
    }
  }

  const getCompletionColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-green-100 text-green-800'
    if (percentage >= 70) return 'bg-yellow-100 text-yellow-800'
    if (percentage >= 50) return 'bg-orange-100 text-orange-800'
    return 'bg-red-100 text-red-800'
  }

  const getCompletionBarColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-green-500'
    if (percentage >= 70) return 'bg-yellow-500'
    if (percentage >= 50) return 'bg-orange-500'
    return 'bg-red-500'
  }

  return (
    <div className="space-y-4">
      {statistics.average_completion !== undefined && (
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-blue-50 p-3 rounded border border-blue-200">
            <p className="text-xs text-blue-600 font-medium">Overall Completion</p>
            <p className="text-2xl font-bold text-blue-900">
              {statistics.average_completion.toFixed(1)}%
            </p>
          </div>
          <div className="bg-purple-50 p-3 rounded border border-purple-200">
            <p className="text-xs text-purple-600 font-medium">Total Fields</p>
            <p className="text-2xl font-bold text-purple-900">
              {statistics.total_fields}
            </p>
          </div>
          <div className="bg-indigo-50 p-3 rounded border border-indigo-200">
            <p className="text-xs text-indigo-600 font-medium">Fully Complete</p>
            <p className="text-2xl font-bold text-indigo-900">
              {statistics.fields.filter((f: Field) => f.completion_percentage === 100).length}
            </p>
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th
                className="px-4 py-2 text-left font-semibold text-gray-700 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('name')}
              >
                Field Name {sortBy === 'name' && (sortDesc ? '▼' : '▲')}
              </th>
              <th className="px-4 py-2 text-center font-semibold text-gray-700">
                Total
              </th>
              <th className="px-4 py-2 text-center font-semibold text-gray-700">
                Filled
              </th>
              <th className="px-4 py-2 text-center font-semibold text-gray-700">
                Empty
              </th>
              <th
                className="px-4 py-2 text-center font-semibold text-gray-700 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('completion')}
              >
                Completion {sortBy === 'completion' && (sortDesc ? '▼' : '▲')}
              </th>
              <th
                className="px-4 py-2 text-center font-semibold text-gray-700 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('unique')}
              >
                Unique {sortBy === 'unique' && (sortDesc ? '▼' : '▲')}
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedFields.map((field: Field, idx: number) => (
              <tr key={idx} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900 max-w-xs truncate">
                  {field.name}
                </td>
                <td className="px-4 py-3 text-center text-gray-600">
                  {field.total_count}
                </td>
                <td className="px-4 py-3 text-center text-gray-600">
                  {field.filled_count}
                </td>
                <td className="px-4 py-3 text-center text-gray-600">
                  {field.empty_count}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-gray-200 rounded overflow-hidden">
                      <div
                        className={`h-full ${getCompletionBarColor(field.completion_percentage)}`}
                        style={{ width: `${field.completion_percentage}%` }}
                      />
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap ${getCompletionColor(
                        field.completion_percentage
                      )}`}
                    >
                      {field.completion_percentage.toFixed(1)}%
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 text-center text-gray-600">
                  {field.unique_count}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="text-xs text-gray-500">
        Showing {sortedFields.length} fields •{' '}
        <button
          onClick={loadStatistics}
          className="text-blue-600 hover:text-blue-700 font-medium"
        >
          Refresh
        </button>
      </div>
    </div>
  )
}
