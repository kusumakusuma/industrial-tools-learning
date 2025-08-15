from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.investigation import db, Investigation, InvestigationFact, TimelineEvent
from datetime import datetime

investigations_bp = Blueprint('investigations', __name__)

@investigations_bp.route('/')
@login_required
def dashboard():
    """Main dashboard showing all investigations"""
    investigations = Investigation.query.filter_by(
        created_by_id=current_user.id
    ).order_by(Investigation.created_at.desc()).all()
    
    # Calculate statistics
    stats = {
        'total': len(investigations),
        'in_progress': sum(1 for i in investigations if i.status != 'completed'),
        'completed': sum(1 for i in investigations if i.status == 'completed'),
        'overdue': sum(1 for i in investigations if i.days_since_incident and i.days_since_incident > 30)
    }
    
    return render_template('investigations/dashboard.html', 
                         investigations=investigations,
                         stats=stats)

@investigations_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_investigation():
    """Create new investigation"""
    if request.method == 'POST':
        investigation = Investigation(
            title=request.form['title'],
            description=request.form.get('description'),
            incident_date=datetime.strptime(request.form['incident_date'], '%Y-%m-%dT%H:%M'),
            location=request.form['location'],
            severity=request.form['severity'],
            created_by_id=current_user.id
        )
        investigation.generate_reference_number()
        
        db.session.add(investigation)
        db.session.commit()
        
        flash(f'Investigation {investigation.reference_number} created successfully!', 'success')
        return redirect(url_for('investigations.view_investigation', id=investigation.id))
    
    return render_template('investigations/create.html')

@investigations_bp.route('/<int:id>')
@login_required
def view_investigation(id):
    """View investigation details"""
    investigation = Investigation.query.get_or_404(id)
    
    # Organize facts by category
    facts_by_category = {}
    for category, label in InvestigationFact.CATEGORIES:
        facts_by_category[category] = {
            'label': label,
            'facts': [f for f in investigation.facts if f.category == category]
        }
    
    return render_template('investigations/detail.html',
                         investigation=investigation,
                         facts_by_category=facts_by_category)

@investigations_bp.route('/<int:id>/add-fact', methods=['POST'])
@login_required
def add_fact(id):
    """Add fact to investigation (AJAX endpoint)"""
    investigation = Investigation.query.get_or_404(id)
    
    fact = InvestigationFact(
        investigation_id=id,
        category=request.form['category'],
        title=request.form['title'],
        description=request.form['description'],
        source=request.form.get('source'),
        confidence_level=int(request.form.get('confidence_level', 3)),
        collected_by_id=current_user.id
    )
    
    db.session.add(fact)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'fact': {
            'id': fact.id,
            'title': fact.title,
            'category': fact.category
        }
    })