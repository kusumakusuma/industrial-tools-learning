"""
Day 5: Flask Web Application
Goal: Create a dynamic web server for the reliability dashboard
New concepts: Flask, routes, templates, JSON APIs
"""

from flask import Flask, render_template, request, jsonify
import csv
import os
from datetime import datetime
from typing import Dict, List

# Initialize Flask app
app = Flask(__name__)

# LESSON 1: Flask basics - Creating routes
@app.route('/')
def home():
    """Home page - redirect to dashboard"""
    return render_template('dashboard.html')

# LESSON 2: Working with data
def load_equipment_data() -> List[Dict]:
    """Load equipment data from CSV file"""
    equipment_list = []
    csv_path = '../fleet_data.csv'  # From Day 2
    
    # Check if file exists
    if not os.path.exists(csv_path):
        # Return sample data if no CSV
        return [
            {
                'name': 'Pump-101',
                'total_hours': 720,
                'uptime_hours': 695.5,
                'failures': 3,
                'availability': 96.53,
                'mtbf': 231.83,
                'mttr': 8.17,
                'status': 'GOOD'
            },
            {
                'name': 'Compressor-A',
                'total_hours': 720,
                'uptime_hours': 635,
                'failures': 5,
                'availability': 88.19,
                'mtbf': 127.0,
                'mttr': 17.0,
                'status': 'FAIR'
            }
        ]
    
    try:
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Calculate status based on availability
                availability = float(row.get('availability', 0))
                if availability >= 95:
                    status = 'GOOD'
                elif availability >= 90:
                    status = 'FAIR'
                else:
                    status = 'POOR'
                
                equipment_list.append({
                    'name': row['name'],
                    'total_hours': float(row['total_hours']),
                    'uptime_hours': float(row['uptime_hours']),
                    'failures': int(row['failures']),
                    'availability': availability,
                    'mtbf': float(row['mtbf']) if row['mtbf'] != 'inf' else 999999,
                    'mttr': float(row.get('mttr', 0)),
                    'status': status
                })
    except Exception as e:
        print(f"Error loading CSV: {e}")
    
    return equipment_list

def save_equipment_data(equipment_list: List[Dict]):
    """Save equipment data to CSV"""
    csv_path = '../fleet_data.csv'
    
    try:
        with open(csv_path, 'w', newline='') as file:
            if equipment_list:
                fieldnames = ['name', 'total_hours', 'uptime_hours', 'failures', 
                            'availability', 'mtbf', 'mttr', 'date_added']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for eq in equipment_list:
                    writer.writerow({
                        'name': eq['name'],
                        'total_hours': eq['total_hours'],
                        'uptime_hours': eq['uptime_hours'],
                        'failures': eq['failures'],
                        'availability': f"{eq['availability']:.2f}",
                        'mtbf': f"{eq['mtbf']:.2f}" if eq['mtbf'] < 999999 else 'inf',
                        'mttr': f"{eq['mttr']:.2f}",
                        'date_added': eq.get('date_added', datetime.now().strftime('%Y-%m-%d %H:%M'))
                    })
    except Exception as e:
        print(f"Error saving CSV: {e}")

# LESSON 3: API endpoints for dynamic data
@app.route('/api/equipment')
def get_equipment():
    """API endpoint to get all equipment data"""
    equipment = load_equipment_data()
    
    # Calculate fleet statistics
    if equipment:
        total_availability = sum(eq['availability'] for eq in equipment)
        avg_availability = total_availability / len(equipment)
        
        total_mtbf = sum(eq['mtbf'] for eq in equipment if eq['mtbf'] < 999999)
        equipment_with_failures = sum(1 for eq in equipment if eq['failures'] > 0)
        avg_mtbf = total_mtbf / equipment_with_failures if equipment_with_failures > 0 else 0
        
        critical_count = sum(1 for eq in equipment if eq['status'] == 'POOR')
    else:
        avg_availability = 0
        avg_mtbf = 0
        critical_count = 0
    
    return jsonify({
        'equipment': equipment,
        'statistics': {
            'fleet_availability': round(avg_availability, 2),
            'total_equipment': len(equipment),
            'critical_alerts': critical_count,
            'avg_mtbf': round(avg_mtbf, 2)
        }
    })

# LESSON 4: Handling form submissions
@app.route('/api/equipment/add', methods=['POST'])
def add_equipment():
    """API endpoint to add new equipment"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'total_hours', 'uptime_hours', 'failures']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Convert to proper types
        name = str(data['name']).strip()
        total_hours = float(data['total_hours'])
        uptime_hours = float(data['uptime_hours'])
        failures = int(data['failures'])
        
        # Validate data
        if not name:
            return jsonify({'error': 'Equipment name cannot be empty'}), 400
        if uptime_hours > total_hours:
            return jsonify({'error': 'Uptime cannot exceed total hours'}), 400
        if failures < 0:
            return jsonify({'error': 'Failures cannot be negative'}), 400
        
        # Calculate metrics
        downtime = total_hours - uptime_hours
        availability = (uptime_hours / total_hours * 100) if total_hours > 0 else 0
        mtbf = uptime_hours / failures if failures > 0 else 999999
        mttr = downtime / failures if failures > 0 else 0
        
        # Determine status
        if availability >= 95:
            status = 'GOOD'
        elif availability >= 90:
            status = 'FAIR'
        else:
            status = 'POOR'
        
        # Create equipment record
        new_equipment = {
            'name': name,
            'total_hours': total_hours,
            'uptime_hours': uptime_hours,
            'failures': failures,
            'availability': availability,
            'mtbf': mtbf,
            'mttr': mttr,
            'status': status,
            'date_added': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        # Load existing equipment and add new one
        equipment_list = load_equipment_data()
        equipment_list.append(new_equipment)
        
        # Save to CSV
        save_equipment_data(equipment_list)
        
        return jsonify({
            'success': True,
            'message': f'Equipment {name} added successfully',
            'equipment': new_equipment
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# LESSON 5: Equipment details endpoint
@app.route('/api/equipment/<equipment_name>')
def get_equipment_details(equipment_name):
    """Get details for specific equipment"""
    equipment_list = load_equipment_data()
    
    # Find the equipment
    equipment = next((eq for eq in equipment_list if eq['name'] == equipment_name), None)
    
    if not equipment:
        return jsonify({'error': 'Equipment not found'}), 404
    
    # Add some calculated details
    equipment['performance_score'] = min(100, equipment['availability'] + (equipment['mtbf'] / 10))
    equipment['maintenance_priority'] = 'HIGH' if equipment['status'] == 'POOR' else 'MEDIUM' if equipment['status'] == 'FAIR' else 'LOW'
    
    return jsonify(equipment)

# LESSON 6: Delete equipment endpoint
@app.route('/api/equipment/<equipment_name>', methods=['DELETE'])
def delete_equipment(equipment_name):
    """Delete equipment from the system"""
    equipment_list = load_equipment_data()
    
    # Filter out the equipment to delete
    updated_list = [eq for eq in equipment_list if eq['name'] != equipment_name]
    
    if len(updated_list) == len(equipment_list):
        return jsonify({'error': 'Equipment not found'}), 404
    
    # Save updated list
    save_equipment_data(updated_list)
    
    return jsonify({
        'success': True,
        'message': f'Equipment {equipment_name} deleted successfully'
    })

# LESSON 7: Health check endpoint
@app.route('/api/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Add a new API endpoint to get equipment by status:
@app.route('/api/equipment/status/<status>')
def get_equipment_by_status(status):
    """Get all equipment with specific status (GOOD/FAIR/POOR)"""
    equipment_list = load_equipment_data()
    filtered = [eq for eq in equipment_list if eq['status'] == status.upper()]
    return jsonify({
        'status': status.upper(),
        'count': len(filtered),
        'equipment': filtered
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Run the application
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Flask Reliability Dashboard")
    print("=" * 50)
    print("Server starting at: http://localhost:5000")
    print("API endpoints:")
    print("  GET  /api/equipment - List all equipment")
    print("  POST /api/equipment/add - Add new equipment")
    print("  GET  /api/equipment/<name> - Get equipment details")
    print("  DELETE /api/equipment/<name> - Delete equipment")
    print("-" * 50)
    
    # Run in debug mode for development
    app.run(debug=True, host='0.0.0.0', port=5000)