import { NextRequest, NextResponse } from 'next/server'
import axios from 'axios'
import * as path from 'path'
import * as fs from 'fs'

const API_KEY = process.env.PARSEHUB_API_KEY || ''
const BASE_URL = process.env.PARSEHUB_BASE_URL || 'https://www.parsehub.com/api/v2'

function saveRunToken(token: string, runToken: string) {
  try {
    const filePath = path.join(process.cwd(), '..', 'active_runs.json')
    let data: any = {
      timestamp: new Date().toISOString(),
      runs: []
    }
    
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf-8')
      data = JSON.parse(content)
    }
    
    if (!Array.isArray(data.runs)) {
      data.runs = []
    }
    
    // Add or update the run token
    const existingIndex = data.runs.findIndex((r: any) => r.token === token)
    if (existingIndex >= 0) {
      data.runs[existingIndex].run_token = runToken
      data.runs[existingIndex].status = 'started'
    } else {
      data.runs.push({
        token,
        run_token: runToken,
        status: 'started',
        project: token,
      })
    }
    
    data.timestamp = new Date().toISOString()
    
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8')
    console.log(`Saved run token for project ${token}: ${runToken}`)
    return true
  } catch (error) {
    console.error('Error saving run token:', error)
    return false
  }
}

export async function POST(request: NextRequest) {
  try {
    const { token, pages } = await request.json()

    if (!token) {
      return NextResponse.json(
        { error: 'Project token is required' },
        { status: 400 }
      )
    }

    const response = await axios.post(
      `${BASE_URL}/projects/${token}/run`,
      {},
      { params: { api_key: API_KEY } }
    )

    if (response.data && response.data.run_token) {
      saveRunToken(token, response.data.run_token)
      
      // Save pages info to active_runs.json if pages specified
      if (pages && pages > 0) {
        try {
          const filePath = path.join(process.cwd(), '..', 'active_runs.json')
          let data: any = { timestamp: new Date().toISOString(), runs: [] }
          
          if (fs.existsSync(filePath)) {
            const content = fs.readFileSync(filePath, 'utf-8')
            data = JSON.parse(content)
          }
          
          if (!Array.isArray(data.runs)) {
            data.runs = []
          }
          
          const runIndex = data.runs.findIndex((r: any) => r.token === token && r.run_token === response.data.run_token)
          if (runIndex >= 0) {
            data.runs[runIndex].target_pages = pages
          }
          
          data.timestamp = new Date().toISOString()
          fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8')
        } catch (err) {
          console.log('Warning: Could not save pages info:', err)
        }
      }
    }

    return NextResponse.json({
      success: true,
      run_token: response.data.run_token,
      status: 'started',
      pages: pages || 1,
    })
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { error: 'Failed to run project' },
      { status: 500 }
    )
  }
}
