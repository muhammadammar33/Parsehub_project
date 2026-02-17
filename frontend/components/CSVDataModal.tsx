'use client'

import { useState, useEffect } from 'react'
import { Download, Eye, FileJson } from 'lucide-react'
import Modal from './Modal'

interface CSVDataModalProps {
  token: string
  title: string
  isOpen: boolean
  onClose: () => void
}

export default function CSVDataModal({ token, title, isOpen, onClose }: CSVDataModalProps) {
  const [csvData, setCSVData] = useState<string>('')
  const [jsonData, setJsonData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'table' | 'raw'>('table')

  useEffect(() => {
    if (isOpen && token) {
      fetchCSVData()
    }
  }, [isOpen, token])

  const fetchCSVData = async () => {
    setLoading(true)
    setError(null)
    try {
      // Add 30 second timeout
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000)
      
      try {
        const response = await fetch(`/api/analytics?token=${token}&force=true`, {
          signal: controller.signal
        })
        
        if (!response.ok) {
          throw new Error(`API error: ${response.status} ${response.statusText}`)
        }
        
        const result = await response.json()
        
        // Extract CSV data
        if (result.csv_data) {
          setCSVData(result.csv_data)
          // Parse CSV to JSON for table view
          parseCSVToJSON(result.csv_data)
        } else {
          setError('No CSV data found for this project. Try running the project first.')
        }
      } finally {
        clearTimeout(timeoutId)
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        setError('Request timed out (took longer than 30 seconds). The server might be busy.')
      } else {
        setError(err instanceof Error ? err.message : 'Unknown error occurred')
      }
    } finally {
      setLoading(false)
    }
  }

  const parseCSVToJSON = (csv: string) => {
    const lines = csv.trim().split('\n')
    if (lines.length < 2) {
      setJsonData([])
      return
    }

    const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''))
    const data = lines.slice(1).map(line => {
      const values = line.split(',').map(v => v.trim().replace(/^"|"$/g, ''))
      const obj: any = {}
      headers.forEach((header, index) => {
        obj[header] = values[index] || ''
      })
      return obj
    })
    setJsonData(data)
  }

  const downloadCSV = () => {
    if (!csvData) return
    const element = document.createElement('a')
    element.setAttribute('href', 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvData))
    element.setAttribute('download', `${token}-data.csv`)
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  const downloadJSON = () => {
    if (jsonData.length === 0) return
    const dataStr = JSON.stringify(jsonData, null, 2)
    const element = document.createElement('a')
    element.setAttribute('href', 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr))
    element.setAttribute('download', `${token}-data.json`)
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  if (!isOpen) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`CSV Data - ${title}`} size="xlarge">
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      ) : error ? (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          Error: {error}
        </div>
      ) : csvData ? (
        <div className="space-y-4">
          {/* Header with download buttons */}
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex gap-2">
              <button
                onClick={() => setViewMode('table')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
                  viewMode === 'table'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                <Eye className="w-4 h-4" />
                Table
              </button>
              <button
                onClick={() => setViewMode('raw')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
                  viewMode === 'raw'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                <FileJson className="w-4 h-4" />
                Raw
              </button>
            </div>
            <div className="flex gap-2">
              <button
                onClick={downloadCSV}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition"
              >
                <Download className="w-4 h-4" />
                Download CSV
              </button>
              <button
                onClick={downloadJSON}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition"
              >
                <Download className="w-4 h-4" />
                Download JSON
              </button>
            </div>
          </div>

          {/* Content */}
          {viewMode === 'table' ? (
            // Table view
            <div className="overflow-x-auto border border-gray-300 rounded-lg">
              {jsonData.length > 0 ? (
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-gray-100 border-b border-gray-300">
                      {Object.keys(jsonData[0]).map((key) => (
                        <th
                          key={key}
                          className="px-4 py-2 text-left text-sm font-semibold text-gray-800 border-r border-gray-300 last:border-r-0"
                        >
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {jsonData.map((row, idx) => (
                      <tr key={idx} className="border-b border-gray-200 hover:bg-blue-50 transition">
                        {Object.values(row).map((value: any, cellIdx) => (
                          <td
                            key={cellIdx}
                            className="px-4 py-2 text-sm text-gray-700 border-r border-gray-200 last:border-r-0 break-words"
                          >
                            {typeof value === 'string' ? (
                              value.length > 100 ? `${value.substring(0, 100)}...` : value
                            ) : (
                              String(value)
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="text-center py-8 text-gray-500">No data rows found</div>
              )}
            </div>
          ) : (
            // Raw CSV view
            <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
              <pre className="text-xs font-mono overflow-auto max-h-96 text-gray-800 whitespace-pre-wrap break-words">
                {csvData}
              </pre>
            </div>
          )}

          {/* Stats */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-gray-700">
            <p>
              <strong>Total Records:</strong> {jsonData.length}
            </p>
            {jsonData.length > 0 && (
              <p>
                <strong>Columns:</strong> {Object.keys(jsonData[0]).length}
              </p>
            )}
          </div>
        </div>
      ) : null}
    </Modal>
  )
}
