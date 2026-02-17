'use client'

import { useState, useEffect } from 'react'
import BrandCollapsible from './BrandCollapsible'

interface Project {
  token: string
  name?: string
  title?: string
}

interface ProjectsListProps {
  projects: Project[]
  onRunProject: (token: string) => Promise<void>
}

export default function ProjectsList({
  projects,
  onRunProject,
}: ProjectsListProps) {
  const [groupedByBrand, setGroupedByBrand] = useState<
    Map<string, Project[]>
  >(new Map())

  useEffect(() => {
    // Group projects by brand/category
    const groups = new Map<string, Project[]>()

    projects.forEach((project) => {
      const projectName = project.name || project.title || 'Unknown'
      // Extract brand from project name (split by underscore or space)
      const brand = projectName.split(/[_\s]+/)[0] || 'Other'
      if (!groups.has(brand)) {
        groups.set(brand, [])
      }
      groups.get(brand)!.push({
        token: project.token,
        name: projectName,
      })
    })

    setGroupedByBrand(groups)
  }, [projects])

  const handleRunAll = async (brand: string) => {
    const brandProjects = groupedByBrand.get(brand)
    if (!brandProjects) return

    for (const project of brandProjects) {
      try {
        await onRunProject(project.token)
        await new Promise((resolve) => setTimeout(resolve, 1000)) // 1 second delay between runs
      } catch (error) {
        console.error(`Failed to run ${project.name}:`, error)
      }
    }
  }

  if (groupedByBrand.size === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-lg">No projects found</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Projects by Brand</h2>

      {Array.from(groupedByBrand.entries())
        .sort(([brandA], [brandB]) => brandA.localeCompare(brandB))
        .map(([brand, brandProjects]) => (
          <BrandCollapsible
            key={brand}
            brand={brand}
            projects={brandProjects}
            onRunAll={handleRunAll}
            onRunProject={onRunProject}
          />
        ))}
    </div>
  )
}
