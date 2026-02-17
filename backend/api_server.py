"""
Flask API Server for ParseHub Real-Time Monitoring
Exposes REST endpoints for the Next.js frontend to control and monitor real-time data collection
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging
from typing import Optional, Dict, List
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Import local services
from database import ParseHubDatabase
from monitoring_service import MonitoringService
from analytics_service import AnalyticsService

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
db = ParseHubDatabase()
monitoring_service = MonitoringService()
analytics_service = AnalyticsService()

# API Key validation
BACKEND_API_KEY = os.getenv('BACKEND_API_KEY', 't_hmXetfMCq3')

def validate_api_key(request_obj):
    """Validate API key from Authorization header"""
    auth_header = request_obj.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    
    token = auth_header.replace('Bearer ', '')
    return token == BACKEND_API_KEY

# ========== MONITORING ENDPOINTS ==========

@app.route('/api/monitor/start', methods=['POST'])
def start_monitoring():
    """
    Start real-time monitoring of a ParseHub run
    
    Request body:
    {
        "run_token": "...",
        "pages": 1,
        "project_id": 1 (optional)
    }
    """
    if not validate_api_key(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        run_token = data.get('run_token')
        pages = data.get('pages', 1)
        project_id = data.get('project_id')
        
        if not run_token:
            return jsonify({'error': 'Missing required field: run_token'}), 400
        
        # If project_id not provided, infer from run token in active runs
        if not project_id:
            try:
                with open('../active_runs.json', 'r') as f:
                    active_runs = json.load(f)
                    for project in active_runs.get('projects', []):
                        for run in project.get('runs', []):
                            if run.get('run_token') == run_token:
                                project_id = project.get('id')
                                break
            except:
                pass
        
        if not project_id:
            return jsonify({'error': 'Could not determine project_id'}), 400
        
        # Create monitoring session in database
        session_id = db.create_monitoring_session(project_id, run_token, pages)
        
        if not session_id:
            return jsonify({'error': 'Failed to create monitoring session'}), 500
        
        # Start real-time monitoring in background
        # This will run the monitoring loop in the monitoring service
        try:
            monitoring_service.monitor_run_realtime(project_id, run_token, pages)
        except Exception as e:
            logger.error(f'Error starting real-time monitoring: {e}')
            # Still return success since session was created, monitoring will retry
        
        return jsonify({
            'session_id': session_id,
            'run_token': run_token,
            'project_id': project_id,
            'target_pages': pages,
            'status': 'monitoring_started'
        }), 200
    
    except Exception as e:
        logger.error(f'Error in /api/monitor/start: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/monitor/status', methods=['GET'])
def get_monitor_status():
    """
    Get current monitoring status
    
    Query parameters:
    - session_id: Monitoring session ID (optional)
    - project_id: Project ID (optional)
    """
    if not validate_api_key(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        session_id = request.args.get('session_id', type=int)
        project_id = request.args.get('project_id', type=int)
        
        if not session_id and not project_id:
            return jsonify({'error': 'Missing required parameter: session_id or project_id'}), 400
        
        # Get session summary
        if session_id:
            summary = db.get_session_summary(session_id)
        else:  # project_id provided
            summary = db.get_monitoring_status_for_project(project_id)
        
        if not summary:
            return jsonify({'error': 'Monitoring session not found'}), 404
        
        return jsonify({
            'success': True,
            'status': summary['status'],
            'session_id': summary.get('session_id'),
            'project_id': summary.get('project_id'),
            'run_token': summary.get('run_token'),
            'target_pages': summary.get('target_pages'),
            'total_pages': summary.get('total_pages'),
            'total_records': summary.get('total_records'),
            'progress_percentage': summary.get('progress_percentage'),
            'current_url': summary.get('current_url'),
            'error_message': summary.get('error_message'),
            'start_time': summary.get('start_time'),
            'end_time': summary.get('end_time'),
        }), 200
    
    except Exception as e:
        logger.error(f'Error in /api/monitor/status: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/monitor/data', methods=['GET'])
def get_monitor_data():
    """
    Get scraped data from a monitoring session
    
    Query parameters:
    - session_id: Monitoring session ID (required)
    - limit: Number of records to fetch (default: 100)
    - offset: Number of records to skip (default: 0)
    """
    if not validate_api_key(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        session_id = request.args.get('session_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if not session_id:
            return jsonify({'error': 'Missing required parameter: session_id'}), 400
        
        # Validate limit and offset
        limit = min(max(limit, 1), 1000)  # Clamp between 1 and 1000
        offset = max(offset, 0)
        
        # Get records from database
        records = db.get_session_records(session_id, limit, offset)
        total = db.get_session_records_count(session_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'records': records,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total,
        }), 200
    
    except Exception as e:
        logger.error(f'Error in /api/monitor/data: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/monitor/data/csv', methods=['GET'])
def get_monitor_data_csv():
    """
    Export monitoring session data as CSV
    
    Query parameters:
    - session_id: Monitoring session ID (required)
    """
    if not validate_api_key(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        session_id = request.args.get('session_id', type=int)
        
        if not session_id:
            return jsonify({'error': 'Missing required parameter: session_id'}), 400
        
        # Get CSV data
        csv_data = db.get_data_as_csv(session_id)
        
        if not csv_data:
            return jsonify({'error': 'No records found for session'}), 404
        
        return csv_data, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename="session_{session_id}_data.csv"'
        }
    
    except Exception as e:
        logger.error(f'Error in /api/monitor/data/csv: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/monitor/stop', methods=['POST'])
def stop_monitoring():
    """
    Stop real-time monitoring of a run
    
    Request body:
    {
        "session_id": 1 (optional),
        "run_token": "..." (optional)
    }
    """
    if not validate_api_key(request):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        run_token = data.get('run_token')
        
        if not session_id and not run_token:
            return jsonify({'error': 'Missing required field: session_id or run_token'}), 400
        
        # Update session status to cancelled
        if session_id:
            db.update_monitoring_session(session_id, status='cancelled')
            summary = db.get_session_summary(session_id)
        else:
            # Find session by run_token (get most recent)
            # This would need a database method to find by run_token
            return jsonify({'error': 'Session ID required for stopping'}), 400
        
        return jsonify({
            'success': True,
            'status': 'cancelled',
            'session_id': session_id,
            'total_records': summary.get('total_records') if summary else 0,
        }), 200
    
    except Exception as e:
        logger.error(f'Error in /api/monitor/stop: {e}')
        return jsonify({'error': str(e)}), 500


# ========== HEALTH CHECK ==========

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200


# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Internal server error: {error}')
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    from datetime import datetime
    
    port = os.getenv('BACKEND_PORT', 5000)
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f'Starting ParseHub API Server on port {port}')
    app.run(host='0.0.0.0', port=int(port), debug=debug)
