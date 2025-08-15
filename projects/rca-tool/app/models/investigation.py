from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model - you might already have this"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    investigations = db.relationship('Investigation', backref='creator', lazy=True)

class Investigation(db.Model):
    """Core investigation model"""
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(20), unique=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    incident_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100))
    severity = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='s0')
    
    # S0: Containment
    containment_actions = db.Column(db.Text)
    containment_completed_at = db.Column(db.DateTime)
    
    # S1: Problem Definition (5W1H)
    what_happened = db.Column(db.Text)
    when_occurred = db.Column(db.DateTime)
    where_occurred = db.Column(db.String(200))
    who_involved = db.Column(db.Text)
    how_discovered = db.Column(db.Text)
    why_important = db.Column(db.Text)
    
    # Metadata
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    facts = db.relationship('InvestigationFact', backref='investigation', lazy=True, cascade='all, delete-orphan')
    timeline_events = db.relationship('TimelineEvent', backref='investigation', lazy=True, cascade='all, delete-orphan')
    why_nodes = db.relationship('WhyTreeNode', backref='investigation', lazy=True, cascade='all, delete-orphan')
    files = db.relationship('InvestigationFile', backref='investigation', lazy=True, cascade='all, delete-orphan')
    action_items = db.relationship('ActionItem', backref='investigation', lazy=True, cascade='all, delete-orphan')
    
    def generate_reference_number(self):
        """Auto-generate reference number"""
        year = datetime.now().year
        count = Investigation.query.filter(
            db.extract('year', Investigation.created_at) == year
        ).count() + 1
        self.reference_number = f"RCA-{year}-{count:03d}"
    
    @property
    def progress(self):
        """Calculate progress percentage"""
        progress_map = {
            's0': 20,
            's1': 40,
            's2': 60,
            'why_tree': 80,
            'draft_report': 90,
            'completed': 100
        }
        return progress_map.get(self.status, 0)
    
    @property
    def days_since_incident(self):
        """Calculate days since incident"""
        if self.incident_date:
            delta = datetime.utcnow() - self.incident_date
            return delta.days
        return None

class InvestigationFact(db.Model):
    """Facts collected during investigation (4 P's)"""
    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigation.id'), nullable=False)
    category = db.Column(db.String(20), nullable=False)  # people, position, paper, parts
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(200))
    confidence_level = db.Column(db.Integer, default=3)  # 1-5 scale
    collected_at = db.Column(db.DateTime, default=datetime.utcnow)
    collected_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # 4 P's categories
    CATEGORIES = [
        ('people', 'People'),
        ('position', 'Position/Environment'),
        ('paper', 'Paper/Procedures'),
        ('parts', 'Parts/Equipment')
    ]

class TimelineEvent(db.Model):
    """Timeline of events"""
    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigation.id'), nullable=False)
    event_time = db.Column(db.DateTime, nullable=False)
    event_type = db.Column(db.String(20), default='normal')
    event_description = db.Column(db.Text, nullable=False)
    is_critical = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    EVENT_TYPES = [
        ('normal', 'Normal Operation'),
        ('deviation', 'Deviation'),
        ('alarm', 'Alarm/Alert'),
        ('intervention', 'Human Intervention'),
        ('incident', 'Incident Occurred'),
        ('discovery', 'Problem Discovered'),
        ('response', 'Response Action')
    ]

class WhyTreeNode(db.Model):
    """Why Tree analysis nodes"""
    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigation.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('why_tree_node.id'), nullable=True)
    
    question = db.Column(db.String(200), default="Why?")
    answer = db.Column(db.Text, nullable=False)
    cause_type = db.Column(db.String(20))  # physical, human, system, procedure, environmental
    
    level = db.Column(db.Integer, default=1)
    sequence = db.Column(db.Integer, default=1)
    is_root_cause = db.Column(db.Boolean, default=False)
    requires_action = db.Column(db.Boolean, default=False)
    evidence_description = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Self-referential relationship for tree structure
    children = db.relationship('WhyTreeNode', backref=db.backref('parent', remote_side=[id]))
    
    def calculate_level(self):
        """Calculate node level in tree"""
        if not self.parent_id:
            self.level = 1
        else:
            self.level = self.parent.level + 1
            # Auto-mark as root cause if deep enough
            if self.level >= 3:
                self.is_root_cause = True

class InvestigationFile(db.Model):
    """File attachments"""
    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigation.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    category = db.Column(db.String(20), default='other')
    description = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class ActionItem(db.Model):
    """Action items from root causes"""
    id = db.Column(db.Integer, primary_key=True)
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigation.id'), nullable=False)
    why_node_id = db.Column(db.Integer, db.ForeignKey('why_tree_node.id'))
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    due_date = db.Column(db.Date)
    completed_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    @property
    def is_overdue(self):
        if self.status != 'completed' and self.due_date:
            return datetime.utcnow().date() > self.due_date
        return False