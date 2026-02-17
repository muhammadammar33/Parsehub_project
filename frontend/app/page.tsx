'use client'

import { useEffect, useState } from 'react'
import { Activity, TrendingUp, Zap, Download, AlertCircle, BarChart3 } from 'lucide-react'
import ProjectsList from '@/components/ProjectsList'
import StatsCard from '@/components/StatsCard'
import Header from '@/components/Header'
import AllProjectsAnalyticsModal from '@/components/AllProjectsAnalyticsModal'
import RunDialog from '@/components/RunDialog'
import { useRealTimeMonitoring } from '@/lib/useRealTimeMonitoring'

interface Project {
  token: string
  title: string
  owner_email: string
  projecturl?: string
  main_site?: string
  last_run: {
    status: string
    pages: number
    start_time: string
    run_token: string
  } | null
}

interface Stats {
  total: number
  running: number
  completed: number
  queued: number
}

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([])
  const [stats, setStats] = useState<Stats>({
    total: 0,
    running: 0,
    completed: 0,
    queued: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [analyticsOpen, setAnalyticsOpen] = useState(false)
  const [runDialogOpen, setRunDialogOpen] = useState(false)
  const [projectToRun, setProjectToRun] = useState<Project | null>(null)
  
  // Real-time monitoring hook
  const monitoring = useRealTimeMonitoring()

  useEffect(() => {
    fetchProjects()
    const interval = setInterval(fetchProjects, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const fetchProjects = async () => {
    try {
      setError(null)
      const response = await fetch('/api/projects')
      if (!response.ok) throw new Error('Failed to fetch projects')
      
      const data = await response.json()
      setProjects(data.projects || [])
      setLastUpdate(new Date())

      // Calculate stats
      const running = data.projects?.filter(
        (p: Project) => p.last_run?.status === 'running'
      ).length || 0
      const completed = data.projects?.filter(
        (p: Project) => p.last_run?.status === 'complete'
      ).length || 0
      const queued = data.projects?.filter(
        (p: Project) => p.last_run?.status === 'queued'
      ).length || 0

      setStats({
        total: data.projects?.length || 0,
        running,
        completed,
        queued,
      })

      setLoading(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch projects')
      setLoading(false)
    }
  }

  const handleRunAll = async () => {
    try {
      setError(null)
      const response = await fetch('/api/projects/run-all', { method: 'POST' })
      if (!response.ok) throw new Error('Failed to run projects')
      
      setTimeout(fetchProjects, 1000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run projects')
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <Header />

      {/* Error Alert */}
      {error && (
        <div className="container mx-auto px-4 py-4 mt-4">
          <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-400">Error</p>
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Stats Section */}
      <section className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <StatsCard
            title="Total Projects"
            value={stats.total}
            icon={<TrendingUp className="w-5 h-5" />}
            color="bg-blue-500"
          />
          <StatsCard
            title="Running"
            value={stats.running}
            icon={<Activity className="w-5 h-5" />}
            color="bg-green-500"
          />
          <StatsCard
            title="Queued"
            value={stats.queued}
            icon={<Zap className="w-5 h-5" />}
            color="bg-yellow-500"
          />
          <StatsCard
            title="Completed"
            value={stats.completed}
            icon={<Download className="w-5 h-5" />}
            color="bg-purple-500"
          />
        </div>

        {/* Action Buttons */}
        <div className="mb-8 flex gap-4 flex-wrap">
          <button
            onClick={handleRunAll}
            disabled={loading}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:from-slate-600 disabled:to-slate-700 rounded-lg font-semibold transition-all shadow-lg"
          >
            🚀 Run All Projects
          </button>
          <button
            onClick={() => setAnalyticsOpen(true)}
            className="px-6 py-3 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 rounded-lg font-semibold transition-all shadow-lg flex items-center gap-2"
          >
            <BarChart3 className="w-5 h-5" />
            📊 Analyze
          </button>
          <button
            onClick={fetchProjects}
            disabled={loading}
            className="px-6 py-3 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 rounded-lg font-semibold transition-all"
          >
            🔄 Refresh
          </button>
          {lastUpdate && (
            <div className="text-slate-400 text-sm flex items-center">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
          )}
        </div>

        {/* Projects List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-400"></div>
            </div>
            <p className="text-slate-400 mt-4">Loading projects...</p>
          </div>
        ) : (
          <ProjectsList 
            projects={projects} 
            onRunProject={async (token: string) => {
              const project = projects.find(p => p.token === token)
              if (project) {
                setProjectToRun(project)
                setRunDialogOpen(true)
              }
            }}
          />
        )}
      </section>

      {/* Run Dialog */}
      {projectToRun && (
        <RunDialog
          isOpen={runDialogOpen}
          onClose={() => setRunDialogOpen(false)}
          projectToken={projectToRun.token}
          projectTitle={projectToRun.title}
          projectURL={projectToRun.projecturl || projectToRun.main_site || ''}
          onRunStart={async (runToken: string, pages: number) => {
            // Start real-time monitoring
            try {
              await monitoring.startMonitoring(projectToRun.token, runToken, pages)
            } catch (err) {
              console.error('Failed to start monitoring:', err)
            }
            
            await fetchProjects()
            // Show analytics modal for all projects
            setAnalyticsOpen(true)
          }}
        />
      )}

      {/* Analytics Modal */}
      <AllProjectsAnalyticsModal
        isOpen={analyticsOpen}
        onClose={() => {
          setAnalyticsOpen(false)
        }}
        projects={projects}
      />
    </main>
  )
}
