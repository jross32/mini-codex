export type Buff = { label: string; detail: string }
export type Title = {
  id: number
  name: string
  detail: string
  min_level: number
  buff: Record<string, unknown>
  earned: boolean
  active: boolean
}

export type User = {
  id: number
  email: string
  display_name: string
  level: number
  xp_total: number
  coins: number
  coin_rate?: number
  streak_days: number
  resilience_tokens?: number
  stats: Record<string, number>
  buffs?: Buff[]
}

export type QuestEvent = {
  id: number
  completed_at: string
  xp_earned: number
  coins_earned?: number
  streak_multiplier: number
}

export type Quest = {
  id: number
  type: 'daily' | 'side' | 'main'
  title: string
  description: string
  xp_reward: number
  stat_targets: Record<string, unknown>
  due_date: string | null
  is_active: boolean
  created_at: string
  events: QuestEvent[]
}

export type RewardDrop = {
  id: number
  label: string
  detail: string
  rarity: string
  created_at: string
}

export type Boss = {
  id: number
  name: string
  week_start: string
  hp_total: number
  hp_current: number
}

export type WeeklyRecap = {
  week_start: string
  total_xp: number
  quests_completed: number
  top_type: string | null
  current_streak: number
}

export type Skill = {
  id: number
  name: string
  detail: string
  cost_xp: number
  effect: Record<string, unknown>
  category: string
  unlocked: boolean
}

export type Party = {
  id: number
  name: string
  code: string
  members: number
}

export type Contract = {
  id: number
  target_streak: number
  pledge: string
  reward: string
  active: boolean
}

export type QuestTemplate = {
  id: number
  type: 'daily' | 'side' | 'main'
  title: string
  description: string
  xp_reward: number
}

export type ReminderPreference = {
  id: number
  time: string
  timezone: string
  enabled: boolean
}
