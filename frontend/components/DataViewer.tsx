'use client'

import React, { useState, useEffect } from 'react'
import { Eye, Loader, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react'

interface DataViewerProps {
  projectToken: string
  projectId?: number
  refreshTrigger?: number
}

export default function DataViewer({
  projectToken,
  projectId,
  refreshTrigger = 0,
}: DataViewerProps) {
  const [data, setData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(10)
  const [selectedRecord, setSelectedRecord] = useState<any>(null)
  const [showDetail, setShowDetail] = useState(false)

  useEffect(() => {
    loadData()
  }, [projectToken, projectId, refreshTrigger])

  const loadData = async () => {
    setIsLoading(true)
    setError('')

    try {
      const params = new URLSearchParams()
      if (projectId) {
        params.append('projectId', projectId.toString())
      } else {
        params.append('token', projectToken)
      }

      const response = await fetch(`/api/data?${params.toString()}`)

      if (!response.ok) {
        throw new Error('Failed to load data')
      }

      const result = await response.json()
      setData(result.data || [])
      setCurrentPage(1)
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
          <p className="font-medium text-red-800">Failed to load data</p>
          <p className="text-sm text-red-700 mt-1">{error}</p>
          <button
            onClick={loadData}
            className="text-sm text-red-600 hover:text-red-700 mt-2 font-medium"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Eye className="w-8 h-8 mx-auto mb-2 text-gray-400" />
        <p>No data available yet</p>
      </div>
    )
  }

  // Pagination
  const totalPages = Math.ceil(data.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const currentData = data.slice(startIndex, endIndex)

  // Get all unique keys for columns
  const allKeys = new Set<string>()
  data.forEach((item: any) => {
    if (typeof item === 'object') {
      Object.keys(item).forEach((key) => {
        if (key !== 'page_number') {
          allKeys.add(key)
        }
      })
    }
  })
  const columns = Array.from(allKeys).sort()

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-blue-50 p-3 rounded border border-blue-200">
          <p className="text-xs text-blue-600 font-medium">Total Records</p>
          <p className="text-2xl font-bold text-blue-900">{data.length}</p>
        </div>
        <div className="bg-purple-50 p-3 rounded border border-purple-200">
          <p className="text-xs text-purple-600 font-medium">Columns</p>
          <p className="text-2xl font-bold text-purple-900">{columns.length}</p>
        </div>
      </div>

      <div className="overflow-x-auto border rounded">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-3 py-2 text-left font-semibold text-gray-700 w-12">
                #
              </th>
              {columns.slice(0, 5).map((col) => (
                <th
                  key={col}
                  className="px-3 py-2 text-left font-semibold text-gray-700"
                >
                  {col}
                </th>
              ))}
              {columns.length > 5 && (
                <th className="px-3 py-2 text-left font-semibold text-gray-700">
                  +{columns.length - 5} more
                </th>
              )}
              <th className="px-3 py-2 text-center font-semibold text-gray-700 w-12">
                View
              </th>
            </tr>
          </thead>
          <tbody>
            {currentData.map((item: any, idx: number) => (
              <tr key={startIndex + idx} className="border-b hover:bg-gray-50">
                <td className="px-3 py-2 text-gray-600 font-medium">
                  {startIndex + idx + 1}
                </td>
                {columns.slice(0, 5).map((col) => (
                  <td
                    key={col}
                    className="px-3 py-2 text-gray-600 max-w-xs truncate text-xs"
                  >
                    {item[col] ? String(item[col]).substring(0, 50) : '-'}
                  </td>
                ))}
                {columns.length > 5 && (
                  <td className="px-3 py-2 text-gray-400 text-xs">
                    {columns.length - 5} more fields
                  </td>
                )}
                <td className="px-3 py-2 text-center">
                  <button
                    onClick={() => {
                      setSelectedRecord(item)
                      setShowDetail(true)
                    }}
                    className="text-blue-600 hover:text-blue-700 font-medium text-xs"
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Showing {startIndex + 1} to {Math.min(endIndex, data.length)} of{' '}
          {data.length} records
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="p-1 border border-gray-300 rounded hover:bg-gray-50 disabled:text-gray-300 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-sm text-gray-600 px-2">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className="p-1 border border-gray-300 rounded hover:bg-gray-50 disabled:text-gray-300 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Detail Modal */}
      {showDetail && selectedRecord && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg max-w-2xl max-h-96 overflow-auto p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Record Details</h3>
              <button
                onClick={() => setShowDetail(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ×
              </button>
            </div>
            <div className="space-y-2">
              {Object.entries(selectedRecord).map(([key, value]) => (
                <div key={key} className="flex border-b pb-2">
                  <div className="font-semibold text-gray-700 w-32 flex-shrink-0">
                    {key}:
                  </div>
                  <div className="text-gray-600 flex-1 break-words">
                    {value ? String(value) : '-'}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowDetail(false)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="text-xs text-gray-500">
        <button
          onClick={loadData}
          className="text-blue-600 hover:text-blue-700 font-medium"
        >
          Refresh Data
        </button>
      </div>
    </div>
  )
}
