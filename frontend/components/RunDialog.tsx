'use client'

import React, { useState } from 'react'
import Modal from './Modal'
import ProgressModal from './ProgressModal'
import { Play, AlertCircle, Zap } from 'lucide-react'

interface RunDialogProps {
  isOpen: boolean
  onClose: () => void
  projectToken: string
  projectTitle: string
  projectURL?: string
  onRunStart: (runToken: string, pages: number) => void
  isLoading?: boolean
}

export default function RunDialog({
  isOpen,
  onClose,
  projectToken,
  projectTitle,
  projectURL = '',
  onRunStart,
  isLoading = false,
}: RunDialogProps) {
  const [pages, setPages] = useState<number>(1)
  const [useIncremental, setUseIncremental] = useState(false)
  const [totalPages, setTotalPages] = useState<number>(10)
  const [error, setError] = useState<string>('')
  const [isRunning, setIsRunning] = useState(false)
  const [sessionId, setSessionId] = useState<number | null>(null)
  const [showProgress, setShowProgress] = useState(false)

  const handleRun = async () => {
    if (pages < 1) {
      setError('Pages must be at least 1')
      return
    }

    if (pages > 1000) {
      setError('Pages cannot exceed 1000')
      return
    }

    if (useIncremental && totalPages < pages) {
      setError('Total pages must be greater than or equal to pages per iteration')
      return
    }

    setError('')
    setIsRunning(true)

    try {
      if (useIncremental) {
        // Fetch project details from ParseHub to get the URL if not provided
        let urlToUse = projectURL
        if (!urlToUse) {
          try {
            const projectDetailsRes = await fetch(`/api/projects/${projectToken}`)
            if (projectDetailsRes.ok) {
              const projectData = await projectDetailsRes.json()
              urlToUse = projectData.project?.url || projectData.project?.main_site || ''
            }
          } catch (err) {
            console.error('Failed to fetch project URL:', err)
            // Continue with empty URL, let backend handle the error
          }
        }

        // Start incremental scraping
        const response = await fetch('/api/projects/incremental', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            project_token: projectToken,
            project_name: projectTitle,
            original_url: urlToUse,
            total_pages: totalPages,
            pages_per_iteration: pages,
          }),
        })

        if (!response.ok) {
          throw new Error('Failed to start incremental scraping')
        }

        const data = await response.json()

        if (data.success) {
          setPages(1)
          setTotalPages(10)
          setUseIncremental(false)
          setSessionId(data.session_id)
          setShowProgress(true)
          onClose()
        } else {
          setError(data.error || 'Failed to start incremental scraping')
        }
      } else {
        // Regular run
        const response = await fetch('/api/projects/run', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            token: projectToken,
            pages: pages,
          }),
        })

        if (!response.ok) {
          throw new Error('Failed to start run')
        }

        const data = await response.json()

        if (data.success && data.run_token) {
          onRunStart(data.run_token, pages)
          setPages(1)
          onClose()
        } else {
          setError(data.error || 'Failed to start run')
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsRunning(false)
    }
  }

  const handlePagesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value) || 0
    setPages(Math.max(1, Math.min(1000, value)))
    setError('')
  }

  const handleTotalPagesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value) || 0
    setTotalPages(Math.max(1, Math.min(10000, value)))
    setError('')
  }

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} title={`Run: ${projectTitle}`}>
        <div className="space-y-4">
        {/* Incremental Scraping Toggle */}
        <div className="border-b border-gray-200 pb-4">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="incremental-toggle"
              checked={useIncremental}
              onChange={(e) => {
                setUseIncremental(e.target.checked)
                setError('')
              }}
              disabled={isRunning || isLoading}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2"
            />
            <label htmlFor="incremental-toggle" className="flex items-center gap-2 cursor-pointer">
              <Zap className="w-4 h-4 text-orange-600" />
              <span className="font-medium text-gray-700">Enable Incremental Scraping</span>
            </label>
          </div>
          <p className="text-xs text-gray-500 mt-2 ml-7">
            Automatically creates and runs multiple jobs to scrape all pages, combining results
          </p>
        </div>

        {/* Regular Pages Input */}
        {!useIncremental && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Number of Pages to Scrape
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="1"
                max="1000"
                value={pages}
                onChange={handlePagesChange}
                disabled={isRunning || isLoading}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                placeholder="Enter number of pages"
              />
              <span className="text-sm text-gray-500">pages</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Specify how many pages to scrape in a single run.
            </p>
          </div>
        )}

        {/* Incremental Scraping Inputs */}
        {useIncremental && (
          <div className="space-y-4 bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Pages per Iteration
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="1"
                  max="500"
                  value={pages}
                  onChange={handlePagesChange}
                  disabled={isRunning || isLoading}
                  className="flex-1 px-3 py-2 border border-orange-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 disabled:bg-gray-100 text-gray-900 font-semibold"
                  placeholder="e.g., 5"
                />
                <span className="text-sm text-gray-600">pages/run</span>
              </div>
              <p className="text-xs text-gray-600 mt-1">
                How many pages to scrape per ParseHub project iteration
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Total Pages Target
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="1"
                  max="10000"
                  value={totalPages}
                  onChange={handleTotalPagesChange}
                  disabled={isRunning || isLoading}
                  className="flex-1 px-3 py-2 border border-orange-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 disabled:bg-gray-100 text-gray-900 font-semibold"
                  placeholder="e.g., 50"
                />
                <span className="text-sm text-gray-600">pages total</span>
              </div>
              <p className="text-xs text-gray-600 mt-1">
                Total pages you want to scrape (system will create {Math.ceil(totalPages / pages)} iterations)
              </p>
            </div>

            <div className="bg-white border border-orange-200 rounded p-2">
              <p className="text-sm font-medium text-gray-700">Scraping Plan:</p>
              <p className="text-sm text-gray-600 mt-1">
                Will create <strong>{Math.ceil(totalPages / pages)}</strong> automatic runs of{' '}
                <strong>{pages} pages each</strong> to reach <strong>{totalPages} pages</strong>
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
            <span className="text-sm text-red-700">{error}</span>
          </div>
        )}

        {!useIncremental && (
          <div className="bg-blue-50 border border-blue-200 rounded p-3">
            <p className="text-sm text-blue-800">
              <strong>Auto-Recovery Enabled:</strong> If the scraping stops before reaching all{' '}
              {pages} pages, you can resume without losing progress.
            </p>
          </div>
        )}

        {useIncremental && (
          <div className="bg-orange-50 border border-orange-200 rounded p-3">
            <p className="text-sm text-orange-800">
              <strong>Automated Pagination:</strong> URL pattern will be detected automatically. New projects
              will be created for each iteration and combined results will be saved.
            </p>
          </div>
        )}

        <div className="flex gap-2 justify-end pt-2">
          <button
            onClick={onClose}
            disabled={isRunning || isLoading}
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleRun}
            disabled={isRunning || isLoading}
            className={`px-4 py-2 text-white rounded-md flex items-center gap-2 disabled:cursor-not-allowed ${
              useIncremental
                ? 'bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400'
                : 'bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400'
            }`}
          >
            <Play className="w-4 h-4" />
            {isRunning || isLoading ? 'Starting...' : useIncremental ? 'Start Incremental Scrape' : 'Start Run'}
          </button>
        </div>
      </div>
    </Modal>

    <ProgressModal
      isOpen={showProgress}
      onClose={() => setShowProgress(false)}
      sessionId={sessionId || 0}
      projectName={projectTitle}
    />
  </>
  )
}

