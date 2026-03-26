from datetime import datetime, timedelta, date
import json
import os
import random
from flask import request
from werkzeug.security import generate_password_hash
from pywebpush import webpush, WebPushException
from .db import db_session
from .models import (
    User,
    StatBlock,
    Quest,
    QuestEvent,
    Buff,
    Title,
    UserTitle,
    PushSubscription,
    RewardDrop,
    Boss,
    Skill,
    UserSkill,
    Party,
    PartyMember,
    Contract,
    QuestTemplate,
    ReminderPreference,
)
from .schemas import QuestCreateSchema
from .game import level_for_xp, streak_multiplier


VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY')
VAPID_CLAIMS = {"sub": os.getenv('VAPID_SUB', 'mailto:you@example.com')}


def register_routes(app):
    @app.get('/me')
    def me():
        user = _ensure_demo_user()
        _ensure_title_unlocks(user)
        _ensure_default_skills()
        return {'user': _user_payload(user)}

    @app.get('/quests')
    def list_quests():
        user = _ensure_demo_user()
        quests = db_session.query(Quest).filter_by(user_id=user.id).order_by(Quest.created_at.desc()).all()
        return {'quests': [_quest_payload(q) for q in quests]}

    @app.post('/quests')
    def create_quest():
        user = _ensure_demo_user()
        body = request.get_json() or {}
        data = QuestCreateSchema(**body)
        quest = Quest(
            user_id=user.id,
            type=data.type,
            title=data.title,
            description=data.description,
            xp_reward=data.xp_reward,
            stat_targets=data.stat_targets,
            due_date=datetime.fromisoformat(data.due_date) if data.due_date else None,
            is_active=data.is_active,
        )
        db_session.add(quest)
        db_session.commit()
        return {'quest': _quest_payload(quest)}, 201

    @app.patch('/quests/<int:quest_id>')
    def update_quest(quest_id):
        user = _ensure_demo_user()
        quest = db_session.query(Quest).filter_by(id=quest_id, user_id=user.id).first()
        if not quest:
            return {'message': 'quest not found'}, 404
        body = request.get_json() or {}
        for field in ['title', 'description', 'type', 'xp_reward', 'is_active']:
            if field in body:
                setattr(quest, field, body[field])
        if 'due_date' in body:
            quest.due_date = datetime.fromisoformat(body['due_date']) if body['due_date'] else None
        db_session.commit()
        return {'quest': _quest_payload(quest)}

    @app.delete('/quests/<int:quest_id>')
    def delete_quest(quest_id):
        user = _ensure_demo_user()
        quest = db_session.query(Quest).filter_by(id=quest_id, user_id=user.id).first()
        if not quest:
            return {'message': 'quest not found'}, 404
        db_session.delete(quest)
        db_session.commit()
        return {'message': 'deleted'}

    @app.post('/quests/<int:quest_id>/complete')
    def complete_quest(quest_id):
        user = _ensure_demo_user()
        quest = db_session.query(Quest).filter_by(id=quest_id, user_id=user.id).first()
        if not quest:
            return {'message': 'quest not found'}, 404

        # streak multiplier per quest
        current_streak = len(quest.events)
        streak_mult = streak_multiplier(current_streak + 1)

        # bonus multipliers
        bonus, details = _compute_bonus(user, quest)
        mult = streak_mult * (1 + bonus)
        earned = int(quest.xp_reward * mult)

        user.xp_total += earned
        user.level = level_for_xp(user.xp_total)
        user.streak_days = current_streak + 1
        coin_rate = user.coin_rate or 0.02
        coins_earned = max(1, int(round(earned * coin_rate)))
        user.coins += coins_earned

        evt = QuestEvent(quest_id=quest.id, xp_earned=earned, coins_earned=coins_earned, streak_multiplier=mult)
        db_session.add(evt)

        boss = _get_or_create_boss(user)
        boss_damage = int(earned * (1 + _get_skill_effect(user).get('boss_damage_bonus', 0)))
        boss.hp_current = max(0, boss.hp_current - boss_damage)

        loot = _maybe_drop_loot(user, quest)
        _ensure_title_unlocks(user)
        _ensure_buffs(user)
        db_session.commit()

        return {
            'earned': earned,
            'multiplier': mult,
            'details': details,
            'coins_earned': coins_earned,
            'coins_balance': user.coins,
            'boss': _boss_payload(boss),
            'loot': _reward_payload(loot) if loot else None,
            'user': _user_payload(user),
            'quest': _quest_payload(quest)
        }

    @app.get('/buffs')
    def list_buffs():
        user = _ensure_demo_user()
        buffs = db_session.query(Buff).filter_by(user_id=user.id).all()
        return {'buffs': [_buff_payload(b) for b in buffs]}

    @app.get('/titles')
    def list_titles():
        user = _ensure_demo_user()
        _ensure_title_unlocks(user)
        return {'titles': _titles_payload(user)}

    @app.post('/titles/<int:title_id>/equip')
    def equip_title(title_id):
        user = _ensure_demo_user()
        title = db_session.query(Title).get(title_id)
        if not title:
            return {'message': 'title not found'}, 404
        if user.level < title.min_level:
            return {'message': 'level too low'}, 400
        record = db_session.query(UserTitle).filter_by(user_id=user.id, title_id=title.id).first()
        if not record:
            record = UserTitle(user_id=user.id, title_id=title.id, is_active=True)
            db_session.add(record)
        for ut in user.titles:
            ut.is_active = (ut.title_id == title.id)
        db_session.commit()
        return {'titles': _titles_payload(user)}

    @app.get('/rewards')
    def list_rewards():
        user = _ensure_demo_user()
        rewards = db_session.query(RewardDrop).filter_by(user_id=user.id).order_by(RewardDrop.created_at.desc()).limit(10).all()
        return {'rewards': [_reward_payload(r) for r in rewards]}

    @app.get('/boss')
    def get_boss():
        user = _ensure_demo_user()
        boss = _get_or_create_boss(user)
        return {'boss': _boss_payload(boss)}

    @app.get('/recap/weekly')
    def weekly_recap():
        user = _ensure_demo_user()
        return {'recap': _weekly_recap(user)}

    @app.get('/skills')
    def list_skills():
        user = _ensure_demo_user()
        _ensure_default_skills()
        return {'skills': _skills_payload(user)}

    @app.post('/skills/<int:skill_id>/unlock')
    def unlock_skill(skill_id):
        user = _ensure_demo_user()
        skill = db_session.query(Skill).get(skill_id)
        if not skill:
            return {'message': 'skill not found'}, 404
        if any(us.skill_id == skill.id for us in user.skills):
            return {'message': 'already unlocked'}, 400
        if user.xp_total < skill.cost_xp:
            return {'message': 'not enough xp'}, 400
        user.xp_total -= skill.cost_xp
        db_session.add(UserSkill(user_id=user.id, skill_id=skill.id))
        db_session.commit()
        return {'skills': _skills_payload(user), 'user': _user_payload(user)}

    @app.post('/streak/recover')
    def streak_recover():
        user = _ensure_demo_user()
        if user.resilience_tokens <= 0:
            return {'message': 'no tokens'}, 400
        user.resilience_tokens -= 1
        user.streak_days = max(1, user.streak_days)
        db_session.commit()
        return {'user': _user_payload(user)}

    @app.get('/party')
    def get_party():
        user = _ensure_demo_user()
        member = db_session.query(PartyMember).filter_by(user_id=user.id).first()
        if not member:
            return {'party': None}
        return {'party': _party_payload(member.party)}

    @app.post('/party/create')
    def create_party():
        user = _ensure_demo_user()
        if db_session.query(PartyMember).filter_by(user_id=user.id).first():
            return {'message': 'already in party'}, 400
        body = request.get_json() or {}
        name = body.get('name') or 'My Party'
        code = _make_code()
        party = Party(name=name, code=code)
        db_session.add(party)
        db_session.flush()
        db_session.add(PartyMember(party_id=party.id, user_id=user.id, role='leader'))
        db_session.commit()
        return {'party': _party_payload(party)}

    @app.post('/party/join')
    def join_party():
        user = _ensure_demo_user()
        if db_session.query(PartyMember).filter_by(user_id=user.id).first():
            return {'message': 'already in party'}, 400
        body = request.get_json() or {}
        code = (body.get('code') or '').strip().upper()
        party = db_session.query(Party).filter_by(code=code).first()
        if not party:
            return {'message': 'party not found'}, 404
        db_session.add(PartyMember(party_id=party.id, user_id=user.id, role='member'))
        db_session.commit()
        return {'party': _party_payload(party)}

    @app.post('/party/leave')
    def leave_party():
        user = _ensure_demo_user()
        member = db_session.query(PartyMember).filter_by(user_id=user.id).first()
        if not member:
            return {'message': 'not in party'}, 400
        db_session.delete(member)
        db_session.commit()
        return {'party': None}

    @app.get('/party/leaderboard')
    def party_leaderboard():
        user = _ensure_demo_user()
        member = db_session.query(PartyMember).filter_by(user_id=user.id).first()
        if not member:
            return {'members': []}
        members = (
            db_session.query(PartyMember)
            .filter_by(party_id=member.party_id)
            .all()
        )
        leaderboard = []
        for m in members:
            if not m.user:
                continue
            leaderboard.append({
                'id': m.user.id,
                'display_name': m.user.display_name,
                'coins': m.user.coins,
                'xp_total': m.user.xp_total,
                'streak_days': m.user.streak_days,
            })
        leaderboard.sort(key=lambda item: (-item['coins'], -item['xp_total']))
        return {'members': leaderboard}

    @app.get('/contract')
    def get_contract():
        user = _ensure_demo_user()
        contract = db_session.query(Contract).filter_by(user_id=user.id).first()
        return {'contract': _contract_payload(contract) if contract else None}

    @app.post('/contract')
    def upsert_contract():
        user = _ensure_demo_user()
        body = request.get_json() or {}
        contract = db_session.query(Contract).filter_by(user_id=user.id).first()
        if not contract:
            contract = Contract(user_id=user.id)
            db_session.add(contract)
        contract.target_streak = int(body.get('target_streak', contract.target_streak))
        contract.pledge = body.get('pledge', contract.pledge)
        contract.reward = body.get('reward', contract.reward)
        contract.active = bool(body.get('active', True))
        contract.updated_at = datetime.utcnow()
        db_session.commit()
        return {'contract': _contract_payload(contract)}

    @app.get('/templates')
    def list_templates():
        user = _ensure_demo_user()
        templates = db_session.query(QuestTemplate).filter_by(user_id=user.id).all()
        return {'templates': [_template_payload(t) for t in templates]}

    @app.post('/templates')
    def create_template():
        user = _ensure_demo_user()
        body = request.get_json() or {}
        template = QuestTemplate(
            user_id=user.id,
            type=body.get('type', 'daily'),
            title=body.get('title', 'New Template'),
            description=body.get('description', ''),
            xp_reward=int(body.get('xp_reward', 10)),
        )
        db_session.add(template)
        db_session.commit()
        return {'template': _template_payload(template)}, 201

    @app.post('/templates/<int:template_id>/use')
    def use_template(template_id):
        user = _ensure_demo_user()
        template = db_session.query(QuestTemplate).filter_by(id=template_id, user_id=user.id).first()
        if not template:
            return {'message': 'template not found'}, 404
        quest = Quest(
            user_id=user.id,
            type=template.type,
            title=template.title,
            description=template.description,
            xp_reward=template.xp_reward,
            stat_targets={},
            is_active=True,
        )
        db_session.add(quest)
        db_session.commit()
        return {'quest': _quest_payload(quest)}

    @app.get('/reminders')
    def get_reminders():
        user = _ensure_demo_user()
        reminder = db_session.query(ReminderPreference).filter_by(user_id=user.id).first()
        return {'reminder': _reminder_payload(reminder) if reminder else None}

    @app.post('/coins/spend')
    def spend_coins():
        user = _ensure_demo_user()
        body = request.get_json() or {}
        amount = int(body.get('amount', 0))
        if amount <= 0:
            return {'message': 'invalid amount'}, 400
        if user.coins < amount:
            return {'message': 'not enough coins'}, 400
        user.coins -= amount
        db_session.commit()
        return {'coins': user.coins}

    @app.post('/coins/settings')
    def update_coin_settings():
        user = _ensure_demo_user()
        body = request.get_json() or {}
        rate = None
        if 'coin_rate' in body:
            try:
                rate = float(body.get('coin_rate'))
            except (TypeError, ValueError):
                rate = None
        if rate is None and 'xp_per_coin' in body:
            try:
                xp_per_coin = float(body.get('xp_per_coin'))
                if xp_per_coin > 0:
                    rate = 1.0 / xp_per_coin
            except (TypeError, ValueError):
                rate = None
        if rate is None:
            return {'message': 'invalid coin settings'}, 400
        rate = max(0.005, min(rate, 0.2))
        user.coin_rate = rate
        db_session.commit()
        return {'user': _user_payload(user)}

    @app.post('/reminders')
    def save_reminders():
        user = _ensure_demo_user()
        body = request.get_json() or {}
        reminder = db_session.query(ReminderPreference).filter_by(user_id=user.id).first()
        if not reminder:
            reminder = ReminderPreference(user_id=user.id)
            db_session.add(reminder)
        reminder.time = body.get('time', reminder.time)
        reminder.timezone = body.get('timezone', reminder.timezone)
        reminder.enabled = bool(body.get('enabled', reminder.enabled))
        db_session.commit()
        return {'reminder': _reminder_payload(reminder)}

    @app.post('/push/subscribe')
    def push_subscribe():
        user = _ensure_demo_user()
        body = request.get_json() or {}
        endpoint = body.get('endpoint')
        keys = body.get('keys', {})
        if not endpoint or 'p256dh' not in keys or 'auth' not in keys:
            return {'message': 'invalid subscription'}, 400
        sub = db_session.query(PushSubscription).filter_by(endpoint=endpoint).first()
        if not sub:
            sub = PushSubscription(user_id=user.id, endpoint=endpoint, p256dh=keys['p256dh'], auth=keys['auth'])
            db_session.add(sub)
        else:
            sub.p256dh = keys['p256dh']
            sub.auth = keys['auth']
            sub.user_id = user.id
        db_session.commit()
        return {'message': 'saved'}

    @app.post('/push/send_test')
    def push_send_test():
        if not VAPID_PUBLIC_KEY or not VAPID_PRIVATE_KEY:
            return {'message': 'VAPID keys not configured'}, 400
        user = _ensure_demo_user()
        subs = db_session.query(PushSubscription).filter_by(user_id=user.id).all()
        payload = {'title': 'myLife', 'body': 'Streak reminder: keep the chain alive today!'}
        sent = 0
        for sub in subs:
            try:
                webpush(
                    subscription_info={
                        'endpoint': sub.endpoint,
                        'keys': {'p256dh': sub.p256dh, 'auth': sub.auth}
                    },
                    data=json.dumps(payload),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS,
                    vapid_public_key=VAPID_PUBLIC_KEY,
                )
                sent += 1
            except WebPushException:
                continue
        return {'sent': sent}

    @app.get('/')
    def root():
        return {'status': 'ok', 'service': 'myLife API'}

    @app.get('/health')
    def health():
        return {'status': 'ok'}


# Helpers

def _ensure_title_unlocks(user: User):
    _ensure_default_titles()
    titles = db_session.query(Title).all()
    for t in titles:
        if user.level >= t.min_level and not any(ut.title_id == t.id for ut in user.titles):
            db_session.add(UserTitle(user_id=user.id, title_id=t.id, is_active=False))
    db_session.commit()


def _ensure_default_titles():
    defaults = [
        {'name': 'Apprentice', 'detail': '+5 Discipline, +2% XP', 'min_level': 5, 'buff': {'discipline': 5, 'xp_bonus': 0.02}},
        {'name': 'Disciplined', 'detail': '+5 Order, +5% Daily XP', 'min_level': 10, 'buff': {'order': 5, 'quest_type_bonus': {'daily': 0.05}}},
        {'name': 'Master', 'detail': '+10 Mind, +10% Main XP', 'min_level': 20, 'buff': {'mind': 10, 'quest_type_bonus': {'main': 0.10}}},
    ]
    for d in defaults:
        exists = db_session.query(Title).filter_by(name=d['name']).first()
        if not exists:
            db_session.add(Title(**d))
    db_session.commit()


def _ensure_default_skills():
    defaults = [
        {'name': 'Early Bird', 'detail': '+10% XP before 9am', 'cost_xp': 150, 'effect': {'time_bonus': {'start': '05:00', 'end': '09:00', 'bonus': 0.10}}, 'category': 'mind'},
        {'name': 'Daily Discipline', 'detail': '+10% Daily XP', 'cost_xp': 200, 'effect': {'quest_type_bonus': {'daily': 0.10}}, 'category': 'order'},
        {'name': 'Side Hustle', 'detail': '+10% Side XP', 'cost_xp': 200, 'effect': {'quest_type_bonus': {'side': 0.10}}, 'category': 'wealth'},
        {'name': 'Boss Slayer', 'detail': '+20% Boss damage', 'cost_xp': 250, 'effect': {'boss_damage_bonus': 0.20}, 'category': 'body'},
    ]
    for d in defaults:
        exists = db_session.query(Skill).filter_by(name=d['name']).first()
        if not exists:
            db_session.add(Skill(**d))
    db_session.commit()


def _ensure_buffs(user: User):
    def upsert(label, detail, effect=None):
        buff = db_session.query(Buff).filter_by(user_id=user.id, label=label).first()
        if not buff:
            buff = Buff(user_id=user.id, label=label, detail=detail, effect=effect or {})
            db_session.add(buff)
        else:
            buff.detail = detail
            buff.effect = effect or {}
        return buff

    if user.streak_days >= 3:
        upsert('On a Roll', '+10% XP today', {'xp_bonus': 0.1})
    if user.streak_days >= 7:
        upsert('Momentum', 'x1.5 streak multiplier', {'streak_mult': 1.5})
    active_title = next((ut for ut in user.titles if ut.is_active), None)
    if active_title and active_title.title and active_title.title.buff:
        upsert(f"Title: {active_title.title.name}", active_title.title.detail, active_title.title.buff)


def _compute_bonus(user: User, quest: Quest):
    bonus = 0.0
    details = []
    now = datetime.now()

    # time of day bonus
    if now.hour >= 5 and now.hour < 9:
        bonus += 0.10
        details.append('Early Bird +10%')

    # title and skill bonuses
    effects = _get_skill_effect(user)
    active_title = next((ut for ut in user.titles if ut.is_active), None)
    if active_title and active_title.title and active_title.title.buff:
        effects = _merge_effects(effects, active_title.title.buff)

    if 'xp_bonus' in effects:
        bonus += float(effects.get('xp_bonus', 0))
        details.append(f"XP Bonus +{int(effects.get('xp_bonus', 0) * 100)}%")

    qtype_bonus = effects.get('quest_type_bonus', {})
    if quest.type in qtype_bonus:
        bonus += float(qtype_bonus[quest.type])
        details.append(f"{quest.type.title()} Bonus +{int(qtype_bonus[quest.type] * 100)}%")

    # perfect day bonus and token
    today = date.today()
    total_dailies = db_session.query(Quest).filter_by(user_id=user.id, type='daily', is_active=True).count()
    if total_dailies > 0:
        completed_today = 0
        daily_quests = db_session.query(Quest).filter_by(user_id=user.id, type='daily', is_active=True).all()
        for q in daily_quests:
            if any(e.completed_at.date() == today for e in q.events) or q.id == quest.id:
                completed_today += 1
        if completed_today >= total_dailies and (not user.last_perfect_day or user.last_perfect_day.date() != today):
            bonus += 0.20
            details.append('Perfect Day +20%')
            user.last_perfect_day = datetime.utcnow()
            user.resilience_tokens = min(user.resilience_tokens + 1, 3)

    return bonus, details


def _get_skill_effect(user: User):
    effect = {}
    for us in user.skills:
        effect = _merge_effects(effect, us.skill.effect or {})
    return effect


def _merge_effects(base, extra):
    if not extra:
        return base
    merged = dict(base)
    if 'xp_bonus' in extra:
        merged['xp_bonus'] = merged.get('xp_bonus', 0) + float(extra.get('xp_bonus', 0))
    if 'boss_damage_bonus' in extra:
        merged['boss_damage_bonus'] = merged.get('boss_damage_bonus', 0) + float(extra.get('boss_damage_bonus', 0))
    if 'quest_type_bonus' in extra:
        merged.setdefault('quest_type_bonus', {})
        for k, v in extra['quest_type_bonus'].items():
            merged['quest_type_bonus'][k] = merged['quest_type_bonus'].get(k, 0) + float(v)
    return merged


def _maybe_drop_loot(user: User, quest: Quest):
    roll = random.random()
    if roll > 0.25:
        return None
    pool = [
        ('Quick Stretch', 'Take 3 minutes to stretch', 'common'),
        ('Victory Walk', '5-minute walk outside', 'common'),
        ('Snack Boost', 'Healthy snack reward', 'uncommon'),
        ('Focus Token', '25-minute deep focus block', 'uncommon'),
        ('Epic Reset', 'Half-day off your biggest stressor', 'rare'),
    ]
    label, detail, rarity = random.choice(pool)
    drop = RewardDrop(user_id=user.id, quest_id=quest.id, label=label, detail=detail, rarity=rarity)
    db_session.add(drop)
    return drop


def _get_or_create_boss(user: User):
    week_start = datetime.combine(date.today() - timedelta(days=date.today().weekday()), datetime.min.time())
    boss = db_session.query(Boss).filter_by(user_id=user.id).order_by(Boss.week_start.desc()).first()
    if not boss or boss.week_start.date() != week_start.date():
        hp_total = 800 + user.level * 40
        boss = Boss(user_id=user.id, week_start=week_start, hp_total=hp_total, hp_current=hp_total)
        db_session.add(boss)
        db_session.commit()
    return boss


def _weekly_recap(user: User):
    week_start = datetime.combine(date.today() - timedelta(days=date.today().weekday()), datetime.min.time())
    events = (
        db_session.query(QuestEvent, Quest)
        .join(Quest, QuestEvent.quest_id == Quest.id)
        .filter(Quest.user_id == user.id)
        .filter(QuestEvent.completed_at >= week_start)
        .all()
    )
    total_xp = sum(e.xp_earned for e, _ in events)
    quest_count = len(events)
    type_counts = {}
    for _, q in events:
        type_counts[q.type] = type_counts.get(q.type, 0) + 1
    top_type = max(type_counts, key=type_counts.get) if type_counts else None
    return {
        'week_start': week_start.date().isoformat(),
        'total_xp': total_xp,
        'quests_completed': quest_count,
        'top_type': top_type,
        'current_streak': user.streak_days,
    }


def _user_payload(user: User):
    return {
        'id': user.id,
        'email': user.email,
        'display_name': user.display_name,
        'level': user.level,
        'xp_total': user.xp_total,
        'coins': user.coins,
        'coin_rate': user.coin_rate,
        'streak_days': user.streak_days,
        'resilience_tokens': user.resilience_tokens,
        'stats': _stats_payload(user.stats) if user.stats else None,
        'buffs': [_buff_payload(b) for b in user.buffs],
    }


def _stats_payload(stats: StatBlock):
    return {
        'mind': stats.mind,
        'body': stats.body,
        'wealth': stats.wealth,
        'order': stats.order,
        'discipline': stats.discipline,
    }


def _quest_payload(quest: Quest):
    return {
        'id': quest.id,
        'type': quest.type,
        'title': quest.title,
        'description': quest.description,
        'xp_reward': quest.xp_reward,
        'stat_targets': quest.stat_targets,
        'due_date': quest.due_date.isoformat() if quest.due_date else None,
        'is_active': quest.is_active,
        'created_at': quest.created_at.isoformat(),
        'events': [
            {
                'id': e.id,
                'completed_at': e.completed_at.isoformat(),
                'xp_earned': e.xp_earned,
                'coins_earned': e.coins_earned,
                'streak_multiplier': e.streak_multiplier,
            }
            for e in quest.events
        ],
    }


def _buff_payload(buff: Buff):
    return {
        'id': buff.id,
        'label': buff.label,
        'detail': buff.detail,
        'effect': buff.effect,
        'expires_at': buff.expires_at.isoformat() if buff.expires_at else None,
    }


def _titles_payload(user: User):
    titles = db_session.query(Title).all()
    return [
        {
            'id': t.id,
            'name': t.name,
            'detail': t.detail,
            'min_level': t.min_level,
            'buff': t.buff,
            'earned': any(ut.title_id == t.id for ut in user.titles),
            'active': any(ut.title_id == t.id and ut.is_active for ut in user.titles),
        }
        for t in titles
    ]


def _skills_payload(user: User):
    skills = db_session.query(Skill).all()
    unlocked = {us.skill_id for us in user.skills}
    return [
        {
            'id': s.id,
            'name': s.name,
            'detail': s.detail,
            'cost_xp': s.cost_xp,
            'effect': s.effect,
            'category': s.category,
            'unlocked': s.id in unlocked,
        }
        for s in skills
    ]


def _reward_payload(reward: RewardDrop):
    return {
        'id': reward.id,
        'label': reward.label,
        'detail': reward.detail,
        'rarity': reward.rarity,
        'created_at': reward.created_at.isoformat(),
    }


def _boss_payload(boss: Boss):
    return {
        'id': boss.id,
        'name': boss.name,
        'week_start': boss.week_start.date().isoformat(),
        'hp_total': boss.hp_total,
        'hp_current': boss.hp_current,
    }


def _party_payload(party: Party):
    return {
        'id': party.id,
        'name': party.name,
        'code': party.code,
        'members': len(party.members),
    }


def _contract_payload(contract: Contract):
    return {
        'id': contract.id,
        'target_streak': contract.target_streak,
        'pledge': contract.pledge,
        'reward': contract.reward,
        'active': contract.active,
    }


def _template_payload(template: QuestTemplate):
    return {
        'id': template.id,
        'type': template.type,
        'title': template.title,
        'description': template.description,
        'xp_reward': template.xp_reward,
    }


def _reminder_payload(reminder: ReminderPreference):
    return {
        'id': reminder.id,
        'time': reminder.time,
        'timezone': reminder.timezone,
        'enabled': reminder.enabled,
    }


def _ensure_demo_user():
    user = db_session.query(User).first()
    if not user:
        user = User(email='demo@mylife.local', display_name='Player', password_hash=generate_password_hash('demo'), coins=50, coin_rate=0.02)
        stat = StatBlock(user=user)
        db_session.add_all([user, stat])
        db_session.commit()
    if user.coin_rate is None:
        user.coin_rate = 0.02
        db_session.commit()
    return user


def _make_code():
    return ''.join(random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
