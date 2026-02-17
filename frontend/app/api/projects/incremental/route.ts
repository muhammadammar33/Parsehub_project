import { NextRequest, NextResponse } from 'next/server'
import * as path from 'path'
import * as fs from 'fs'
import { execSync } from 'child_process'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const projectToken = body.project_token || body.projectToken
    const projectName = body.project_name || body.projectName
    let originalUrl = body.original_url || body.originalUrl
    const totalPages = parseInt(body.total_pages || body.totalPages || '10')
    const pagesPerIteration = parseInt(body.pages_per_iteration || body.pagesPerIteration || '5')

    // Validation (originalUrl is optional - will be fetched from ParseHub if not provided)
    if (!projectToken || !projectName || totalPages <= 0) {
      console.error('[API] Validation failed:', {
        projectToken: !!projectToken,
        projectName: !!projectName,
        originalUrl: !!originalUrl,
        totalPages
      })
      return NextResponse.json(
        {
          error: 'Missing or invalid required fields',
          required: ['project_token', 'project_name', 'total_pages']
        },
        { status: 400 }
      )
    }

    console.log(`\n[API] Incremental scraping request:`)
    console.log(`  Project: ${projectName}`)
    console.log(`  Token: ${projectToken}`)
    console.log(`  Target pages: ${totalPages}`)
    if (!originalUrl) {
      console.log(`  URL: Will fetch from ParseHub project details`)
    } else {
      console.log(`  URL: ${originalUrl}`)
    }

    // Execute Python backend script to handle incremental scraping
    const projectRoot = path.resolve(process.cwd(), '..')
    const backendDir = path.join(projectRoot, 'backend')
    const pythonExe = path.join(projectRoot, '.venv', 'Scripts', 'python.exe')
    const scriptPath = path.join(backendDir, 'start_incremental_scraping.py')

    console.log(`[API] Using Python: ${pythonExe}`)
    console.log(`[API] Backend dir: ${backendDir}`)
    console.log(`[API] Script path: ${scriptPath}`)

    if (!fs.existsSync(pythonExe)) {
      console.error('[API] Python executable not found:', pythonExe)
      return NextResponse.json(
        { error: 'Python environment not found' },
        { status: 500 }
      )
    }

    if (!fs.existsSync(scriptPath)) {
      console.error('[API] Script not found:', scriptPath)
      return NextResponse.json(
        { error: 'Incremental scraping script not found' },
        { status: 500 }
      )
    }

    try {
      const args = {
        project_token: projectToken,
        project_name: projectName,
        original_url: originalUrl,
        total_pages: totalPages,
        pages_per_iteration: pagesPerIteration
      }

      const output = execSync(
        `"${pythonExe}" "${scriptPath}"`,
        {
          cwd: backendDir,
          encoding: 'utf-8',
          maxBuffer: 10 * 1024 * 1024,
          timeout: 30000,
          input: JSON.stringify(args)
        }
      )

      console.log(`[API] Python output: ${output}`)
      const result = JSON.parse(output)

      if (result.success) {
        return NextResponse.json({
          success: true,
          session_id: result.session_id,
          message: result.message,
          status: 'running'
        })
      } else {
        console.error('[API] Python returned error:', result.error)
        return NextResponse.json(
          { error: result.error || 'Failed to start incremental scraping' },
          { status: 500 }
        )
      }
    } catch (execError: any) {
      console.error(`[API] Execution error:`, execError.message)
      console.error(`[API] Stderr:`, execError.stderr?.toString())
      console.error(`[API] Stdout:`, execError.stdout?.toString())
      return NextResponse.json(
        { error: 'Failed to start incremental scraping', details: execError.message },
        { status: 500 }
      )
    }
  } catch (error) {
    console.error(`[API] Error:`, error)
    return NextResponse.json(
      { error: String(error) },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const sessionId = searchParams.get('session_id')

    if (!sessionId) {
      return NextResponse.json(
        { error: 'session_id is required' },
        { status: 400 }
      )
    }

    // Execute Python backend script to get session status
    const projectRoot = path.resolve(process.cwd(), '..')
    const backendDir = path.join(projectRoot, 'backend')
    const pythonExe = path.join(projectRoot, '.venv', 'Scripts', 'python.exe')

    if (!fs.existsSync(pythonExe)) {
      return NextResponse.json(
        { error: 'Python environment not found' },
        { status: 500 }
      )
    }

    const pythonScript = `
import sys
import json
sys.path.insert(0, '.')
from scraping_session_service import ScrapingSessionService

try:
    session_service = ScrapingSessionService()
    
    # Get session details
    session_res = session_service.get_session(${sessionId})
    if not session_res['success']:
        print(json.dumps({'success': False, 'error': 'Session not found'}))
        sys.exit(1)
    
    session = session_res['session']
    
    # Get iteration runs
    runs_res = session_service.get_session_runs(${sessionId})
    runs = runs_res.get('runs', []) if runs_res['success'] else []
    
    # Get combined data status
    combined_res = session_service.get_combined_data(${sessionId})
    has_combined_data = combined_res['success']
    
    print(json.dumps({
        'success': True,
        'session': session,
        'iterations': runs,
        'has_combined_data': has_combined_data,
        'progress': {
            'pages_completed': session['pages_completed'],
            'pages_target': session['total_pages_target'],
            'percentage': round((session['pages_completed'] / session['total_pages_target'] * 100) if session['total_pages_target'] > 0 else 0, 1),
            'status': session['status']
        }
    }))
except Exception as e:
    import traceback
    print(json.dumps({'success': False, 'error': str(e)}))
`

    try {
      const output = execSync(
        `"${pythonExe}" -c "${pythonScript.replace(/"/g, '\\"')}"`,
        {
          cwd: backendDir,
          encoding: 'utf-8',
          maxBuffer: 10 * 1024 * 1024,
          timeout: 15000
        }
      )

      const result = JSON.parse(output)
      return NextResponse.json(result)
    } catch (execError: any) {
      console.error('[API] GET execution error:', execError.message)
      return NextResponse.json(
        { error: 'Failed to fetch session status', details: execError.message },
        { status: 500 }
      )
    }
  } catch (error) {
    console.error(`[API] GET Error: ${error}`)
    return NextResponse.json(
      { error: String(error) },
      { status: 500 }
    )
  }
}

