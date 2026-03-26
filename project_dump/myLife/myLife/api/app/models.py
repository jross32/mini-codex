from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from .db import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=False)
    level = Column(Integer, default=1)
    xp_total = Column(Integer, default=0)
    coins = Column(Integer, default=0)
    coin_rate = Column(Float, default=0.02)
    streak_days = Column(Integer, default=0)
    resilience_tokens = Column(Integer, default=1)
    last_perfect_day = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    stats = relationship('StatBlock', uselist=False, back_populates='user', cascade='all, delete-orphan')
    quests = relationship('Quest', back_populates='user', cascade='all, delete-orphan')
    buffs = relationship('Buff', back_populates='user', cascade='all, delete-orphan')
    titles = relationship('UserTitle', back_populates='user', cascade='all, delete-orphan')
    push_subscriptions = relationship('PushSubscription', back_populates='user', cascade='all, delete-orphan')
    rewards = relationship('RewardDrop', back_populates='user', cascade='all, delete-orphan')
    skills = relationship('UserSkill', back_populates='user', cascade='all, delete-orphan')
    parties = relationship('PartyMember', back_populates='user', cascade='all, delete-orphan')
    contracts = relationship('Contract', back_populates='user', cascade='all, delete-orphan')
    templates = relationship('QuestTemplate', back_populates='user', cascade='all, delete-orphan')
    reminders = relationship('ReminderPreference', back_populates='user', cascade='all, delete-orphan')

class StatBlock(Base):
    __tablename__ = 'stats'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    mind = Column(Integer, default=10)
    body = Column(Integer, default=10)
    wealth = Column(Integer, default=10)
    order = Column(Integer, default=10)
    discipline = Column(Integer, default=10)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='stats')

class Quest(Base):
    __tablename__ = 'quests'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(String(10), nullable=False)  # daily, side, main
    title = Column(String(120), nullable=False)
    description = Column(Text, default='')
    xp_reward = Column(Integer, default=10)
    stat_targets = Column(JSON, default={})
    due_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='quests')
    events = relationship('QuestEvent', back_populates='quest', cascade='all, delete-orphan')

class QuestEvent(Base):
    __tablename__ = 'quest_events'
    id = Column(Integer, primary_key=True)
    quest_id = Column(Integer, ForeignKey('quests.id'), nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
    xp_earned = Column(Integer, default=0)
    coins_earned = Column(Integer, default=0)
    streak_multiplier = Column(Float, default=1.0)

    quest = relationship('Quest', back_populates='events')


class Buff(Base):
    __tablename__ = 'buffs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    label = Column(String(120), nullable=False)
    detail = Column(Text, default='')
    effect = Column(JSON, default={})
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='buffs')


class Title(Base):
    __tablename__ = 'titles'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)
    detail = Column(Text, default='')
    min_level = Column(Integer, default=1)
    buff = Column(JSON, default={})

    users = relationship('UserTitle', back_populates='title', cascade='all, delete-orphan')


class UserTitle(Base):
    __tablename__ = 'user_titles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title_id = Column(Integer, ForeignKey('titles.id'), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=False)

    user = relationship('User', back_populates='titles')
    title = relationship('Title', back_populates='users')


class PushSubscription(Base):
    __tablename__ = 'push_subscriptions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    endpoint = Column(Text, unique=True, nullable=False)
    p256dh = Column(String(300), nullable=False)
    auth = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='push_subscriptions')


class RewardDrop(Base):
    __tablename__ = 'reward_drops'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    quest_id = Column(Integer, ForeignKey('quests.id'), nullable=True)
    label = Column(String(120), nullable=False)
    detail = Column(Text, default='')
    rarity = Column(String(20), default='common')
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='rewards')


class Boss(Base):
    __tablename__ = 'bosses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    week_start = Column(DateTime, nullable=False)
    name = Column(String(120), default='The Week Tyrant')
    hp_total = Column(Integer, default=1000)
    hp_current = Column(Integer, default=1000)
    created_at = Column(DateTime, default=datetime.utcnow)


class Skill(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)
    detail = Column(Text, default='')
    cost_xp = Column(Integer, default=100)
    effect = Column(JSON, default={})
    category = Column(String(50), default='general')

    users = relationship('UserSkill', back_populates='skill', cascade='all, delete-orphan')


class UserSkill(Base):
    __tablename__ = 'user_skills'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills.id'), nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='skills')
    skill = relationship('Skill', back_populates='users')


class Party(Base):
    __tablename__ = 'parties'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    code = Column(String(12), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship('PartyMember', back_populates='party', cascade='all, delete-orphan')


class PartyMember(Base):
    __tablename__ = 'party_members'
    id = Column(Integer, primary_key=True)
    party_id = Column(Integer, ForeignKey('parties.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String(20), default='member')
    joined_at = Column(DateTime, default=datetime.utcnow)

    party = relationship('Party', back_populates='members')
    user = relationship('User', back_populates='parties')


class Contract(Base):
    __tablename__ = 'contracts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    target_streak = Column(Integer, default=7)
    pledge = Column(String(120), default='No sugar for a week')
    reward = Column(String(120), default='New book')
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='contracts')


class QuestTemplate(Base):
    __tablename__ = 'quest_templates'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(String(10), nullable=False)
    title = Column(String(120), nullable=False)
    description = Column(Text, default='')
    xp_reward = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='templates')


class ReminderPreference(Base):
    __tablename__ = 'reminder_preferences'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    time = Column(String(10), default='09:00')
    timezone = Column(String(50), default='local')
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='reminders')
