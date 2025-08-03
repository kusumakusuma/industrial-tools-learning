"""
Flask Backend with SQLite Database and CORS enabled
Complete working version for React frontend
"""

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from typing import Dict, List
import os
from sqlalchemy import func

# Initialize Flask app
app = Flask(__name__)

# CRITICAL: Enable CORS for React frontend
CORS(app, origins=['http://localhost:3000'])

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "reliability.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Database Models
class Equipment(db.Model):
    """Equipment table"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    equipment_type = db.Column(db.String(50))
    location = db.Column(db.String(100))
    install_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    readings = db.relationship('PerformanceReading', backref='equipment', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary for JSON"""
        latest_reading = PerformanceReading.query.filter_by(equipment_id=self.id)\
                        .order_by(PerformanceReading.reading_date.desc()).first()
        
        if latest_reading:
            return {
                'id': self.id,
                'name': self.name,
                'type': self.equipment_type,
                'location': self.location,
                'install_date': self.install_date.strftime('%Y-%m-%d'),
                'total_hours': latest_reading.total_hours,
                'uptime_hours': latest_reading.uptime_hours,
                'failures': latest_reading.failures,
                'availability': latest_reading.availability,
                'mtbf': latest_reading.mtbf,
                'mttr': latest_reading.mttr,
                'status': latest_reading.status,
                'last_updated': latest_reading.reading_date.strftime('%Y-%m-%d %H:%M')
            }
        else:
            return {
                'id': self.id,
                'name': self.name,
                'type': self.equipment_type,
                'location': self.location,
                'install_date': self.install_date.strftime('%Y-%m-%d'),
                'status': 'NO DATA',
                'availability': 0,
                'mtbf': 0,
                'failures': 0
            }

class PerformanceReading(db.Model):
    """Performance readings table"""
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    reading_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_hours = db.Column(db.Float, nullable=False)
    uptime_hours = db.Column(db.Float, nullable=False)
    failures = db.Column(db.Integer, nullable=False)
    availability = db.Column(db.Float)
    mtbf = db.Column(db.Float)
    mttr = db.Column(db.Float)
    status = db.Column(db.String(20))
    notes = db.Column(db.Text)
    
    def calculate_metrics(self):
        """Calculate all metrics from raw data"""
        downtime = self.total_hours - self.uptime_hours
        self.availability = (self.uptime_hours / self.total_hours * 100) if self.total_hours > 0 else 0
        self.mtbf = self.uptime_hours / self.failures if self.failures > 0 else 999999
        self.mttr = downtime / self.failures if self.failures > 0 else 0
        
        if self.availability >= 95:
            self.status = 'GOOD'
        elif self.availability >= 90:
            self.status = 'FAIR'
        else:
            self.status = 'POOR'

def init_database():
    """Create tables and add sample data if empty"""
    with app.app_context():
        db.create_all()
        
        if Equipment.query.count() == 0:
            print("Initializing database with sample data...")
            
            equipment_list = [
                Equipment(name='Pump-101', equipment_type='Centrifugal Pump', location='Building A'),
                Equipment(name='Compressor-A', equipment_type='Air Compressor', location='Building B'),
                Equipment(name='Motor-15', equipment_type='Electric Motor', location='Building A'),
                Equipment(name='Generator-01', equipment_type='Backup Generator', location='Power House')
            ]
            
            for eq in equipment_list:
                db.session.add(eq)
            
            db.session.commit()
            
            readings = [
                {'equipment_name': 'Pump-101', 'total': 720, 'uptime': 695.5, 'failures': 3},
                {'equipment_name': 'Compressor-A', 'total': 720, 'uptime': 635, 'failures': 5},
                {'equipment_name': 'Motor-15', 'total': 720, 'uptime': 550, 'failures': 8},
                {'equipment_name': 'Generator-01', 'total': 720, 'uptime': 718, 'failures': 1}
            ]
            
            for reading_data in readings:
                eq = Equipment.query.filter_by(name=reading_data['equipment_name']).first()
                if eq:
                    reading = PerformanceReading(
                        equipment_id=eq.id,
                        total_hours=reading_data['total'],
                        uptime_hours=reading_data['uptime'],
                        failures=reading_data['failures']
                    )
                    reading.calculate_metrics()
                    db.session.add(reading)
            
            db.session.commit()
            print("Sample data added successfully!")

# Routes
@app.route('/')
def home():
    """Home page"""
    return render_template('dashboard.html')

@app.route('/api/test')
def test():
    """Simple test endpoint"""
    return jsonify({"message": "Flask API is working!", "timestamp": datetime.now().isoformat()})

@app.route('/api/equipment')
def get_equipment():
    """Get all equipment with latest readings"""
    try:
        equipment_list = Equipment.query.all()
        equipment_data = [eq.to_dict() for eq in equipment_list]
        
        total_equipment = len(equipment_data)
        
        if total_equipment > 0:
            subquery = db.session.query(
                PerformanceReading.equipment_id,
                func.max(PerformanceReading.reading_date).label('max_date')
            ).group_by(PerformanceReading.equipment_id).subquery()

            latest_readings = db.session.query(PerformanceReading).join(
                subquery,
                (PerformanceReading.equipment_id == subquery.c.equipment_id) &
                (PerformanceReading.reading_date == subquery.c.max_date)
            ).all()
            
            if latest_readings:
                valid_readings = [r for r in latest_readings if r.availability is not None]
                avg_availability = sum(r.availability for r in valid_readings) / len(valid_readings) if valid_readings else 0
                critical_count = sum(1 for r in latest_readings if r.status == 'POOR')
                readings_with_failures = [r for r in latest_readings if r.failures > 0 and r.mtbf < 999999]
                avg_mtbf = sum(r.mtbf for r in readings_with_failures) / len(readings_with_failures) if readings_with_failures else 0
            else:
                avg_availability = 0
                critical_count = 0
                avg_mtbf = 0
        else:
            avg_availability = 0
            critical_count = 0
            avg_mtbf = 0
        
        return jsonify({
            'equipment': equipment_data,
            'statistics': {
                'fleet_availability': round(avg_availability, 2),
                'total_equipment': total_equipment,
                'critical_alerts': critical_count,
                'avg_mtbf': round(avg_mtbf, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/equipment/add', methods=['POST'])
def add_equipment():
    """Add new equipment with initial reading"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'total_hours', 'uptime_hours', 'failures']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        new_equipment = Equipment(
            name=data['name'].strip(),
            equipment_type=data.get('type', 'Unknown'),
            location=data.get('location', 'Not specified')
        )
        
        if Equipment.query.filter_by(name=data['name'].strip()).first():
            return jsonify({'error': 'Equipment already exists'}), 400
        
        if float(data['uptime_hours']) > float(data['total_hours']):
            return jsonify({'error': 'Uptime cannot exceed total hours'}), 400
        if int(data['failures']) < 0:
            return jsonify({'error': 'Failures cannot be negative'}), 400
        
        db.session.add(new_equipment)
        db.session.flush()
        
        reading = PerformanceReading(
            equipment_id=new_equipment.id,
            total_hours=float(data['total_hours']),
            uptime_hours=float(data['uptime_hours']),
            failures=int(data['failures']),
            notes=data.get('notes', '')
        )
        reading.calculate_metrics()
        
        db.session.add(reading)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Equipment {new_equipment.name} added successfully',
            'equipment': new_equipment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/equipment/<int:equipment_id>')
def get_equipment_details(equipment_id):
    """Get equipment details with performance history"""
    equipment = Equipment.query.get_or_404(equipment_id)
    
    readings = PerformanceReading.query.filter_by(equipment_id=equipment_id)\
              .order_by(PerformanceReading.reading_date.desc()).limit(10).all()
    
    if len(readings) >= 2:
        availability_trend = readings[0].availability - readings[-1].availability
        trend = 'improving' if availability_trend > 0 else 'declining' if availability_trend < 0 else 'stable'
    else:
        trend = 'insufficient data'
    
    return jsonify({
        'equipment': equipment.to_dict(),
        'history': [{
            'date': r.reading_date.strftime('%Y-%m-%d'),
            'availability': r.availability,
            'mtbf': r.mtbf,
            'failures': r.failures
        } for r in readings],
        'trend': trend,
        'total_readings': len(readings)
    })

@app.route('/api/equipment/<int:equipment_id>', methods=['DELETE'])
def delete_equipment(equipment_id):
    """Delete equipment and all its readings"""
    equipment = Equipment.query.get_or_404(equipment_id)
    
    try:
        equipment_name = equipment.name
        db.session.delete(equipment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Equipment {equipment_name} and all readings deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check with database status"""
    try:
        equipment_count = Equipment.query.count()
        db_location = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'database_location': db_location,
            'equipment_count': equipment_count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Flask Reliability Dashboard with SQLite")
    print("=" * 50)
    print(f"Database location: {os.path.join(basedir, 'reliability.db')}")
    print("CORS enabled for React frontend at http://localhost:3000")
    
    init_database()
    
    print("\nAPI Endpoints:")
    print("  GET  http://localhost:5000/api/test")
    print("  GET  http://localhost:5000/api/health")
    print("  GET  http://localhost:5000/api/equipment")
    print("  POST http://localhost:5000/api/equipment/add")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)