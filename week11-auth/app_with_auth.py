"""
Flask Backend with Authentication System
Building towards a production-ready reliability management system
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from sqlalchemy import func
import secrets

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Generate a secure secret key
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "reliability_auth.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app, origins=['http://localhost:3000'], supports_credentials=True)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Model
class User(UserMixin, db.Model):
    """User account model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relationships
    equipment = db.relationship('Equipment', backref='owner', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.strftime('%Y-%m-%d')
        }

# Updated Equipment Model with ownership
class Equipment(db.Model):
    """Equipment table with user ownership"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    equipment_type = db.Column(db.String(50))
    location = db.Column(db.String(100))
    install_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Unique constraint: same user cannot have duplicate equipment names
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='_user_equipment_uc'),)
    
    readings = db.relationship('PerformanceReading', backref='equipment', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
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

# Performance Reading Model (unchanged)
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        # Check if user exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email']
        )
        user.set_password(data['password'])
        
        # First user becomes admin
        if User.query.count() == 0:
            user.is_admin = True
        
        db.session.add(user)
        db.session.commit()
        
        # Log the user in
        login_user(user)
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password required'}), 400
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == data['username']) | 
            (User.email == data['username'])
        ).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        login_user(user, remember=True)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    logout_user()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })

@app.route('/api/user')
@login_required
def get_current_user():
    """Get current user info"""
    return jsonify({
        'user': current_user.to_dict()
    })

# Protected Equipment Routes (now user-specific)
@app.route('/api/equipment')
@login_required
def get_equipment():
    """Get all equipment for current user"""
    try:
        # Get only equipment owned by current user
        equipment_list = Equipment.query.filter_by(user_id=current_user.id).all()
        equipment_data = [eq.to_dict() for eq in equipment_list]
        
        # Calculate statistics for user's equipment only
        total_equipment = len(equipment_data)
        
        if total_equipment > 0:
            # Get latest readings for user's equipment
            user_equipment_ids = [eq.id for eq in equipment_list]
            
            subquery = db.session.query(
                PerformanceReading.equipment_id,
                func.max(PerformanceReading.reading_date).label('max_date')
            ).filter(
                PerformanceReading.equipment_id.in_(user_equipment_ids)
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
@login_required
def add_equipment():
    """Add new equipment for current user"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'total_hours', 'uptime_hours', 'failures']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user already has equipment with this name
        if Equipment.query.filter_by(user_id=current_user.id, name=data['name'].strip()).first():
            return jsonify({'error': 'You already have equipment with this name'}), 400
        
        new_equipment = Equipment(
            name=data['name'].strip(),
            equipment_type=data.get('type', 'Unknown'),
            location=data.get('location', 'Not specified'),
            user_id=current_user.id  # Associate with current user
        )
        
        if float(data['uptime_hours']) > float(data['total_hours']):
            return jsonify({'error': 'Uptime cannot exceed total hours'}), 400
        
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

@app.route('/api/equipment/<int:equipment_id>', methods=['DELETE'])
@login_required
def delete_equipment(equipment_id):
    """Delete equipment (only if owned by current user)"""
    equipment = Equipment.query.filter_by(id=equipment_id, user_id=current_user.id).first()
    
    if not equipment:
        return jsonify({'error': 'Equipment not found or access denied'}), 404
    
    try:
        equipment_name = equipment.name
        db.session.delete(equipment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Equipment {equipment_name} deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Admin Routes
@app.route('/api/admin/users')
@login_required
def get_all_users():
    """Get all users (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    users = User.query.all()
    return jsonify({
        'users': [user.to_dict() for user in users]
    })

@app.route('/api/health')
def health_check():
    """Health check (public)"""
    try:
        return jsonify({
            'status': 'healthy',
            'authenticated': current_user.is_authenticated,
            'timestamp': datetime.now().isoformat()
        })
    except:
        return jsonify({
            'status': 'healthy',
            'authenticated': False,
            'timestamp': datetime.now().isoformat()
        })
# PAGE ROUTES (Add these!)
@app.route('/')
def index():
    """Redirect to login or dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    """Serve the login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Serve the dashboard page"""
    # For now, just show the existing dashboard
    return render_template('dashboard.html')

# Keep the existing init_database() and if __name__ == '__main__': below

def init_database():
    """Initialize database with demo data"""
    with app.app_context():
        db.create_all()
        
        # Create demo user if no users exist
        if User.query.count() == 0:
            print("Creating demo user...")
            demo_user = User(
                username='demo',
                email='demo@example.com',
                is_admin=True
            )
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            db.session.commit()
            
            print("Demo user created:")
            print("  Username: demo")
            print("  Password: demo123")
            print("  Email: demo@example.com")

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Flask Reliability Dashboard with Authentication")
    print("=" * 50)
    
    init_database()
    
    print("\nAPI Endpoints:")
    print("  POST /api/register - Create new account")
    print("  POST /api/login - Login")
    print("  POST /api/logout - Logout")
    print("  GET  /api/user - Get current user")
    print("  GET  /api/equipment - Get user's equipment (protected)")
    print("  POST /api/equipment/add - Add equipment (protected)")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)