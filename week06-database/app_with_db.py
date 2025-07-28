"""
Day 6: Flask with SQLite Database
Goal: Upgrade from CSV to a real database
New concepts: SQL, SQLAlchemy ORM, database relationships
"""

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from typing import Dict, List
import os

# Initialize Flask app
app = Flask(__name__)

# LESSON 1: Database Configuration
# SQLite database will be created in the same directory
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reliability.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# LESSON 2: Database Models (like SharePoint Lists!)
class Equipment(db.Model):
    """Equipment table - main entity"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    equipment_type = db.Column(db.String(50))
    location = db.Column(db.String(100))
    install_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to readings (one equipment has many readings)
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
                'status': 'NO DATA'
            }

class PerformanceReading(db.Model):
    """Performance readings table - like SharePoint list items"""
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
        
        # Determine status
        if self.availability >= 95:
            self.status = 'GOOD'
        elif self.availability >= 90:
            self.status = 'FAIR'
        else:
            self.status = 'POOR'

# LESSON 3: Database initialization
def init_database():
    """Create tables and add sample data if empty"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we have any equipment
        if Equipment.query.count() == 0:
            print("Initializing database with sample data...")
            
            # Add sample equipment
            equipment_list = [
                Equipment(name='Pump-101', equipment_type='Centrifugal Pump', location='Building A'),
                Equipment(name='Compressor-A', equipment_type='Air Compressor', location='Building B'),
                Equipment(name='Motor-15', equipment_type='Electric Motor', location='Building A'),
                Equipment(name='Generator-01', equipment_type='Backup Generator', location='Power House')
            ]
            
            for eq in equipment_list:
                db.session.add(eq)
            
            db.session.commit()
            
            # Add sample readings
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

# Routes remain similar but now use database
@app.route('/')
def home():
    """Home page - dashboard"""
    return render_template('dashboard.html')

# LESSON 4: Database queries
@app.route('/api/equipment')
def get_equipment():
    """Get all equipment with latest readings"""
    equipment_list = Equipment.query.all()
    equipment_data = [eq.to_dict() for eq in equipment_list]
    
    # Calculate fleet statistics using SQL aggregation
    total_equipment = len(equipment_data)
    
    # Get latest readings for statistics
    latest_readings = db.session.query(PerformanceReading)\
        .distinct(PerformanceReading.equipment_id)\
        .order_by(PerformanceReading.equipment_id, PerformanceReading.reading_date.desc()).all()
    
    if latest_readings:
        avg_availability = sum(r.availability for r in latest_readings) / len(latest_readings)
        critical_count = sum(1 for r in latest_readings if r.status == 'POOR')
        readings_with_failures = [r for r in latest_readings if r.failures > 0]
        avg_mtbf = sum(r.mtbf for r in readings_with_failures) / len(readings_with_failures) if readings_with_failures else 0
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

# LESSON 5: Adding data with relationships
@app.route('/api/equipment/add', methods=['POST'])
def add_equipment():
    """Add new equipment with initial reading"""
    try:
        data = request.get_json()
        
        # Create new equipment
        new_equipment = Equipment(
            name=data['name'],
            equipment_type=data.get('type', 'Unknown'),
            location=data.get('location', 'Not specified')
        )
        
        # Check if equipment already exists
        if Equipment.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Equipment already exists'}), 400
        
        db.session.add(new_equipment)
        db.session.flush()  # Get the ID without committing
        
        # Add initial performance reading
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

# LESSON 6: Complex queries
@app.route('/api/equipment/<int:equipment_id>')
def get_equipment_details(equipment_id):
    """Get equipment details with performance history"""
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Get all readings for this equipment
    readings = PerformanceReading.query.filter_by(equipment_id=equipment_id)\
              .order_by(PerformanceReading.reading_date.desc()).limit(10).all()
    
    # Calculate trends
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

# LESSON 7: Adding performance readings
@app.route('/api/equipment/<int:equipment_id>/reading', methods=['POST'])
def add_reading(equipment_id):
    """Add new performance reading for equipment"""
    equipment = Equipment.query.get_or_404(equipment_id)
    
    try:
        data = request.get_json()
        
        reading = PerformanceReading(
            equipment_id=equipment_id,
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
            'message': f'Reading added for {equipment.name}',
            'reading': {
                'date': reading.reading_date.strftime('%Y-%m-%d %H:%M'),
                'availability': reading.availability,
                'status': reading.status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# LESSON 8: Database transactions
@app.route('/api/equipment/<int:equipment_id>', methods=['DELETE'])
def delete_equipment(equipment_id):
    """Delete equipment and all its readings (CASCADE)"""
    equipment = Equipment.query.get_or_404(equipment_id)
    
    try:
        equipment_name = equipment.name
        db.session.delete(equipment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Equipment {equipment_name} and all readings deleted'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# LESSON 9: Advanced queries
@app.route('/api/reports/worst-performers')
def worst_performers():
    """Get equipment with availability below 90% in last reading"""
    # SQL: SELECT * FROM equipment JOIN performance_reading WHERE availability < 90
    worst = db.session.query(Equipment, PerformanceReading)\
            .join(PerformanceReading)\
            .filter(PerformanceReading.availability < 90)\
            .order_by(PerformanceReading.availability.asc())\
            .limit(5).all()
    
    return jsonify([{
        'name': eq.name,
        'location': eq.location,
        'availability': reading.availability,
        'status': reading.status,
        'last_updated': reading.reading_date.strftime('%Y-%m-%d')
    } for eq, reading in worst])

@app.route('/api/health')
def health_check():
    """Health check with database status"""
    try:
        # Check database connection
        equipment_count = Equipment.query.count()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'equipment_count': equipment_count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'error',
            'error': str(e)
        }), 500

# Run the application
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Flask Reliability Dashboard with SQLite")
    print("=" * 50)
    
    # Initialize database
    init_database()
    
    print("\nDatabase Features:")
    print("✓ Persistent storage (reliability.db)")
    print("✓ Relationships (Equipment → Readings)")
    print("✓ Performance history tracking")
    print("✓ Complex queries and reports")
    print("-" * 50)
    print("Server starting at: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)