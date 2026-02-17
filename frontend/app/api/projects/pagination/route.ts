import { NextRequest, NextResponse } from 'next/server'
import * as path from 'path'
import { execSync } from 'child_process'

export async function POST(request: NextRequest) {
  try {
    const { token, targetPages } = await request.json()

    if (!token) {
      return NextResponse.json(
        { error: 'Project token is required' },
        { status: 400 }
      )
    }

    // Call Python backend to check pagination status
    const backendPath = path.resolve(process.cwd(), '..', 'backend')
    
    const command = `cd "${backendPath}" && python -c "
import sys
sys.path.insert(0, '.')
from database import ParseHubDatabase
from pagination_service import PaginationService
db = ParseHubDatabase()
db.connect()
import sqlite3
db.connection.row_factory = sqlite3.Row
cursor = db.connection.cursor()
cursor.execute('SELECT id FROM projects WHERE token = ?', ('${token}',))
result = cursor.fetchone()
db.disconnect()

if result:
    project_id = result['id']
    service = PaginationService()
    check_result = service.check_pagination_needed(project_id, ${targetPages || 1})
    import json
    print(json.dumps(check_result))
else:
    print('{}')
"`

    try {
      const result = execSync(command).toString().trim()
      const paginationStatus = result ? JSON.parse(result) : {}

      return NextResponse.json({
        success: true,
        paginationStatus,
        needsRecovery: paginationStatus.needs_recovery || false,
        timestamp: new Date().toISOString(),
      })
    } catch (error) {
      console.error('Error executing command:', error)
      return NextResponse.json(
        { error: 'Failed to check pagination status' },
        { status: 500 }
      )
    }
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { error: 'Failed to check pagination' },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const token = searchParams.get('token')
    const targetPages = searchParams.get('targetPages')

    if (!token) {
      return NextResponse.json(
        { error: 'Project token is required' },
        { status: 400 }
      )
    }

    // Call Python backend
    const backendPath = path.resolve(process.cwd(), '..', 'backend')
    
    const command = `cd "${backendPath}" && python -c "
import sys
sys.path.insert(0, '.')
from database import ParseHubDatabase
from pagination_service import PaginationService
db = ParseHubDatabase()
db.connect()
import sqlite3
db.connection.row_factory = sqlite3.Row
cursor = db.connection.cursor()
cursor.execute('SELECT id FROM projects WHERE token = ?', ('${token}',))
result = cursor.fetchone()
db.disconnect()

if result:
    project_id = result['id']
    service = PaginationService()
    check_result = service.check_pagination_needed(project_id, ${targetPages || 1})
    import json
    print(json.dumps(check_result))
else:
    print('{}')
"`

    try {
      const result = execSync(command).toString().trim()
      const paginationStatus = result ? JSON.parse(result) : {}

      return NextResponse.json({
        success: true,
        paginationStatus,
        needsRecovery: paginationStatus.needs_recovery || false,
        timestamp: new Date().toISOString(),
      })
    } catch (error) {
      console.error('Error executing command:', error)
      return NextResponse.json(
        { error: 'Failed to check pagination status' },
        { status: 500 }
      )
    }
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { error: 'Failed to check pagination' },
      { status: 500 }
    )
  }
}
