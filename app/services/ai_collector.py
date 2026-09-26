import os
import json
from datetime import datetime
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Tu es un assistant qui recherche des opportunités (bourses, stages, hackathons, concours, emplois, formations) destinées aux étudiants et jeunes professionnels africains.

Réponds UNIQUEMENT avec un tableau JSON valide, sans texte avant/après, sans balises markdown. Chaque élément doit avoir exactement ces champs:
- title (string)
- description (string, 2-3 phrases)
- organizer (string ou null)
- link (string, URL complète et réelle)
- country_scope (string: nom de pays, "Afrique", ou "International")
- deadline (string au format YYYY-MM-DD, ou null si inconnue)
- category (string: une de "Hackathon", "Concours", "Formation", "Bourse", "Stage", "Emploi", "Conférence", "Volontariat")

Ne retourne que des opportunités réelles trouvées via la recherche web, avec un lien précis. Maximum 8 résultats."""


def collect_opportunities(search_query):
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[
            {"role": "user", "content": f"Trouve des opportunités récentes sur: {search_query}"}
        ]
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    full_text = "".join(text_parts).strip()
    full_text = full_text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(full_text)
    except json.JSONDecodeError:
        print("Réponse IA non parsable:", full_text[:500])
        return []


def save_opportunities(opportunities):
    from app import db
    from app.models import Opportunity, Category

    saved_count = 0
    for item in opportunities:
        link = item.get('link')
        if not link or Opportunity.query.filter_by(link=link).first():
            continue  # doublon ou lien manquant

        cat_name = item.get('category', 'Autre')
        category = Category.query.filter_by(name=cat_name).first()
        if not category:
            category = Category(name=cat_name)
            db.session.add(category)
            db.session.flush()

        deadline = None
        if item.get('deadline'):
            try:
                deadline = datetime.strptime(item['deadline'], '%Y-%m-%d')
            except ValueError:
                pass

        opp = Opportunity(
            title=item.get('title', 'Sans titre')[:200],
            description=item.get('description', ''),
            organizer=item.get('organizer'),
            link=link,
            country_scope=item.get('country_scope'),
            deadline=deadline,
            status='pending',
            source='ai',
            category_id=category.id
        )
        db.session.add(opp)
        saved_count += 1

    db.session.commit()
    return saved_count