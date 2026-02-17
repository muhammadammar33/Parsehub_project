"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  TrendingUp,
  Zap,
  Download,
  AlertCircle,
  BarChart3,
  Play,
} from "lucide-react";
import ProjectsList from "@/components/ProjectsList";
import StatsCard from "@/components/StatsCard";
import Header from "@/components/Header";
import AllProjectsAnalyticsModal from "@/components/AllProjectsAnalyticsModal";
import RunDialog from "@/components/RunDialog";
import { useRealTimeMonitoring } from "@/lib/useRealTimeMonitoring";

interface Project {
  token: string;
  title: string;
  owner_email: string;
  projecturl?: string;
  main_site?: string;
  last_run: {
    status: string;
    pages: number;
    start_time: string;
    run_token: string;
  } | null;
}

interface Stats {
  total: number;
  running: number;
  completed: number;
  queued: number;
}

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<Stats>({
    total: 0,
    running: 0,
    completed: 0,
    queued: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [runDialogOpen, setRunDialogOpen] = useState(false);
  const [projectToRun, setProjectToRun] = useState<Project | null>(null);

  // Real-time monitoring hook
  const monitoring = useRealTimeMonitoring();

  useEffect(() => {
    fetchProjects();
    const interval = setInterval(fetchProjects, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchProjects = async () => {
    try {
      setError(null);
      const response = await fetch("/api/projects");
      if (!response.ok) throw new Error("Failed to fetch projects");

      const data = await response.json();
      setProjects(data.projects || []);
      setLastUpdate(new Date());

      // Calculate stats
      const running =
        data.projects?.filter((p: Project) => p.last_run?.status === "running")
          .length || 0;
      const completed =
        data.projects?.filter((p: Project) => p.last_run?.status === "complete")
          .length || 0;
      const queued =
        data.projects?.filter((p: Project) => p.last_run?.status === "queued")
          .length || 0;

      setStats({
        total: data.projects?.length || 0,
        running,
        completed,
        queued,
      });

      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch projects");
      setLoading(false);
    }
  };

  const handleRunAll = async () => {
    try {
      setError(null);
      const response = await fetch("/api/projects/run-all", { method: "POST" });
      if (!response.ok) throw new Error("Failed to run projects");

      setTimeout(fetchProjects, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run projects");
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <Header />

      {/* Error Alert */}
      {error && (
        <div className="container mx-auto px-6 py-4 mt-6">
          <div className="bg-red-900/30 backdrop-blur-sm border border-red-700/50 rounded-xl p-4 flex items-start gap-3 shadow-lg shadow-red-900/20">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-red-300">Error</p>
              <p className="text-red-400 text-sm mt-0.5">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Stats Section */}
      <section className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5 mb-8">
          <StatsCard
            title="Total Projects"
            value={stats.total}
            icon={<TrendingUp className="w-6 h-6" />}
            color="bg-blue-500"
          />
          <StatsCard
            title="Running"
            value={stats.running}
            icon={<Activity className="w-6 h-6" />}
            color="bg-green-500"
          />
          <StatsCard
            title="Queued"
            value={stats.queued}
            icon={<Zap className="w-6 h-6" />}
            color="bg-yellow-500"
          />
          <StatsCard
            title="Completed"
            value={stats.completed}
            icon={<Download className="w-6 h-6" />}
            color="bg-purple-500"
          />
        </div>

        {/* Action Buttons */}
        <div className="mb-8 flex gap-4 flex-wrap items-center">
          <button
            onClick={handleRunAll}
            disabled={loading}
            className="inline-flex items-center gap-2 px-6 py-3.5 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-slate-700 disabled:to-slate-700 rounded-xl font-semibold transition-all duration-200 shadow-lg hover:shadow-blue-500/25 disabled:shadow-none transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed"
          >
            <Play className="w-5 h-5" />
            Run All Projects
          </button>
          <button
            onClick={() => setAnalyticsOpen(true)}
            className="inline-flex items-center gap-2 px-6 py-3.5 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 rounded-xl font-semibold transition-all duration-200 shadow-lg hover:shadow-purple-500/25 transform hover:scale-105"
          >
            <BarChart3 className="w-5 h-5" />
            Analytics
          </button>
          <button
            onClick={fetchProjects}
            disabled={loading}
            className="inline-flex items-center gap-2 px-6 py-3.5 bg-slate-800 hover:bg-slate-700 disabled:bg-slate-800/50 border border-slate-700 hover:border-slate-600 rounded-xl font-semibold transition-all duration-200 disabled:cursor-not-allowed"
          >
            <Activity className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          {lastUpdate && (
            <div className="ml-auto flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
              <span className="text-slate-400 text-sm font-medium">
                Updated {lastUpdate.toLocaleTimeString()}
              </span>
            </div>
          )}
        </div>

        {/* Projects List */}
        {loading ? (
          <div className="text-center py-20">
            <div className="inline-flex flex-col items-center gap-6">
              <div className="relative">
                <div className="animate-spin rounded-full h-16 w-16 border-4 border-slate-700 border-t-blue-500"></div>
                <div className="absolute inset-0 rounded-full bg-blue-500/20 animate-pulse"></div>
              </div>
              <div>
                <p className="text-slate-300 text-lg font-semibold">
                  Loading projects...
                </p>
                <p className="text-slate-500 text-sm mt-1">
                  Please wait while we fetch your data
                </p>
              </div>
            </div>
          </div>
        ) : (
          <ProjectsList
            projects={projects}
            onRunProject={async (token: string) => {
              const project = projects.find((p) => p.token === token);
              if (project) {
                setProjectToRun(project);
                setRunDialogOpen(true);
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
          projectURL={projectToRun.projecturl || projectToRun.main_site || ""}
          onRunStart={async (runToken: string, pages: number) => {
            // Start real-time monitoring
            try {
              await monitoring.startMonitoring(
                projectToRun.token,
                runToken,
                pages,
              );
            } catch (err) {
              console.error("Failed to start monitoring:", err);
            }

            await fetchProjects();
            // Show analytics modal for all projects
            setAnalyticsOpen(true);
          }}
        />
      )}

      {/* Analytics Modal */}
      <AllProjectsAnalyticsModal
        isOpen={analyticsOpen}
        onClose={() => {
          setAnalyticsOpen(false);
        }}
        projects={projects}
      />
    </main>
  );
}
