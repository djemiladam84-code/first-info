from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Opportunity, Category

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    opportunities = Opportunity.query.filter_by(status='approved') \
        .order_by(Opportunity.created_at.desc()).limit(10).all()
    return render_template('index.html', opportunities=opportunities)


@main_bp.route('/opportunites')
def opportunity_list():
    query = Opportunity.query.filter_by(status='approved')

    category_id = request.args.get('categorie', type=int)
    country = request.args.get('pays', '').strip()
    search = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    if category_id:
        query = query.filter_by(category_id=category_id)
    if country:
        query = query.filter_by(country_scope=country)
    if search:
        pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                Opportunity.title.ilike(pattern),
                Opportunity.description.ilike(pattern),
                Opportunity.organizer.ilike(pattern)
            )
        )

    pagination = query.order_by(Opportunity.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    categories = Category.query.order_by(Category.name).all()
    countries = (
        db.session.query(Opportunity.country_scope)
        .filter(
            Opportunity.status == 'approved',
            Opportunity.country_scope.isnot(None),
            Opportunity.country_scope != ''
        )
        .distinct()
        .order_by(Opportunity.country_scope)
        .all()
    )

    return render_template(
        'opportunities/list.html',
        opportunities=pagination.items,
        pagination=pagination,
        categories=categories,
        countries=[country[0] for country in countries],
        selected_category=category_id,
        selected_country=country,
        search=search
    )


@main_bp.route('/opportunites/<int:opp_id>')
def opportunity_detail(opp_id):
    opportunity = Opportunity.query.get_or_404(opp_id)
    return render_template('opportunities/detail.html', opportunity=opportunity)


@main_bp.route('/opportunites/<int:opp_id>/favori', methods=['POST'])
@login_required
def toggle_favorite(opp_id):
    opportunity = Opportunity.query.get_or_404(opp_id)

    if opportunity in current_user.favorite_opportunities:
        current_user.favorite_opportunities.remove(opportunity)
        db.session.commit()
    else:
        current_user.favorite_opportunities.append(opportunity)
        db.session.commit()

    return redirect(request.referrer or url_for('main.index'))


@main_bp.route('/mes-favoris')
@login_required
def my_favorites():
    opportunities = current_user.favorite_opportunities.filter_by(status='approved').all()
    return render_template('opportunities/favorites.html', opportunities=opportunities)