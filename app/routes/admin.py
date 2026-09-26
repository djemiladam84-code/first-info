from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app import db
from app.models import Opportunity, Category

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    pending = Opportunity.query.filter_by(status='pending').order_by(Opportunity.created_at.desc()).all()
    approved_count = Opportunity.query.filter_by(status='approved').count()
    return render_template('admin/dashboard.html', pending=pending, approved_count=approved_count)


@admin_bp.route('/opportunites/nouvelle', methods=['GET', 'POST'])
@login_required
@admin_required
def new_opportunity():
    categories = Category.query.all()

    if request.method == 'POST':
        opp = Opportunity(
            title=request.form['title'],
            description=request.form['description'],
            organizer=request.form.get('organizer'),
            link=request.form['link'],
            country_scope=request.form.get('country_scope'),
            category_id=request.form.get('category_id', type=int),
            status='approved',
            source='manual'
        )
        db.session.add(opp)
        db.session.commit()
        flash('Opportunité ajoutée.', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/new_opportunity.html', categories=categories)


@admin_bp.route('/opportunites/<int:opp_id>/valider', methods=['POST'])
@login_required
@admin_required
def approve_opportunity(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)
    opp.status = 'approved'
    db.session.commit()
    flash('Opportunité validée.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/opportunites/<int:opp_id>/rejeter', methods=['POST'])
@login_required
@admin_required
def reject_opportunity(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)
    opp.status = 'rejected'
    db.session.commit()
    flash('Opportunité rejetée.', 'info')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/opportunites/<int:opp_id>/supprimer', methods=['POST'])
@login_required
@admin_required
def delete_opportunity(opp_id):
    opp = Opportunity.query.get_or_404(opp_id)
    db.session.delete(opp)
    db.session.commit()
    flash('Opportunité supprimée.', 'info')
    return redirect(url_for('admin.dashboard'))
@admin_bp.route('/collecte-ia', methods=['GET', 'POST'])
@login_required
@admin_required
def ai_collection():
    if request.method == 'POST':
        from app.services.ai_collector import collect_opportunities, save_opportunities

        query = request.form.get('query', 'bourses et stages pour étudiants africains 2026')
        opportunities = collect_opportunities(query)
        count = save_opportunities(opportunities)
        flash(f'{count} nouvelle(s) opportunité(s) trouvée(s), en attente de validation.', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/ai_collection.html')