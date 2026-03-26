import axios from 'axios'
import type {
  Quest,
  User,
  Title,
  Buff,
  RewardDrop,
  Boss,
  WeeklyRecap,
  Skill,
  Party,
  Contract,
  QuestTemplate,
  ReminderPreference,
} from '../types'

function resolveApiBase(): string {
  const envUrl = (import.meta.env.VITE_API_URL || '').trim()
  if (envUrl) {
    try {
      return new URL(envUrl).toString()
    } catch (e) {
      console.warn('Invalid VITE_API_URL, falling back to origin:5000', envUrl, e)
    }
  }
  if (typeof window !== 'undefined') {
    // swap current port with 5000 for API default
    const url = new URL(window.location.href)
    url.port = '5000'
    url.pathname = ''
    url.search = ''
    return url.toString().replace(/\/$/, '')
  }
  return 'http://localhost:5000'
}

const API_URL = resolveApiBase()

const api = axios.create({
  baseURL: API_URL,
  withCredentials: false,
})

const authHeaders = (token?: string) =>
  token
    ? {
        headers: { Authorization: `Bearer ${token}` },
      }
    : {}

export async function getMe(token: string) {
  const res = await api.get('/me', authHeaders(token))
  return res.data as { user: User }
}

export async function getQuests(token: string) {
  const res = await api.get('/quests', authHeaders(token))
  return res.data as { quests: Quest[] }
}

export async function createQuest(
  token: string,
  quest: { type: string; title: string; description?: string; xp_reward?: number }
) {
  const res = await api.post('/quests', quest, authHeaders(token))
  return res.data as { quest: Quest }
}

export async function updateQuest(
  token: string,
  id: number,
  quest: Partial<{ type: string; title: string; description: string; xp_reward: number; is_active: boolean; due_date: string | null }>
) {
  const res = await api.patch(`/quests/${id}`, quest, authHeaders(token))
  return res.data as { quest: Quest }
}

export async function deleteQuest(token: string, id: number) {
  const res = await api.delete(`/quests/${id}`, authHeaders(token))
  return res.data as { message: string }
}

export async function getTitles(token: string) {
  const res = await api.get('/titles', authHeaders(token))
  return res.data as { titles: Title[] }
}

export async function equipTitle(token: string, id: number) {
  const res = await api.post(`/titles/${id}/equip`, {}, authHeaders(token))
  return res.data as { titles: Title[] }
}

export async function listBuffs(token: string) {
  const res = await api.get('/buffs', authHeaders(token))
  return res.data as { buffs: Buff[] }
}

export async function savePushSubscription(token: string, subscription: PushSubscriptionJSON) {
  const res = await api.post('/push/subscribe', subscription, authHeaders(token))
  return res.data
}

export async function completeQuest(id: number, token: string) {
  const res = await api.post(`/quests/${id}/complete`, {}, authHeaders(token))
  return res.data as {
    earned: number
    multiplier: number
    coins_earned?: number
    coins_balance?: number
    user: User
    quest: Quest
    details?: string[]
    boss?: Boss
    loot?: RewardDrop | null
  }
}

export async function getRewards(token: string) {
  const res = await api.get('/rewards', authHeaders(token))
  return res.data as { rewards: RewardDrop[] }
}

export async function getBoss(token: string) {
  const res = await api.get('/boss', authHeaders(token))
  return res.data as { boss: Boss }
}

export async function getWeeklyRecap(token: string) {
  const res = await api.get('/recap/weekly', authHeaders(token))
  return res.data as { recap: WeeklyRecap }
}

export async function getSkills(token: string) {
  const res = await api.get('/skills', authHeaders(token))
  return res.data as { skills: Skill[] }
}

export async function unlockSkill(token: string, id: number) {
  const res = await api.post(`/skills/${id}/unlock`, {}, authHeaders(token))
  return res.data as { skills: Skill[]; user: User }
}

export async function recoverStreak(token: string) {
  const res = await api.post('/streak/recover', {}, authHeaders(token))
  return res.data as { user: User }
}

export async function getParty(token: string) {
  const res = await api.get('/party', authHeaders(token))
  return res.data as { party: Party | null }
}

export async function getPartyLeaderboard(token: string) {
  const res = await api.get('/party/leaderboard', authHeaders(token))
  return res.data as { members: { id: number; display_name: string; coins: number; xp_total: number; streak_days: number }[] }
}

export async function createParty(token: string, name: string) {
  const res = await api.post('/party/create', { name }, authHeaders(token))
  return res.data as { party: Party }
}

export async function joinParty(token: string, code: string) {
  const res = await api.post('/party/join', { code }, authHeaders(token))
  return res.data as { party: Party }
}

export async function leaveParty(token: string) {
  const res = await api.post('/party/leave', {}, authHeaders(token))
  return res.data as { party: Party | null }
}

export async function getContract(token: string) {
  const res = await api.get('/contract', authHeaders(token))
  return res.data as { contract: Contract | null }
}

export async function saveContract(token: string, payload: Partial<Contract>) {
  const res = await api.post('/contract', payload, authHeaders(token))
  return res.data as { contract: Contract }
}

export async function getTemplates(token: string) {
  const res = await api.get('/templates', authHeaders(token))
  return res.data as { templates: QuestTemplate[] }
}

export async function createTemplate(token: string, payload: Partial<QuestTemplate>) {
  const res = await api.post('/templates', payload, authHeaders(token))
  return res.data as { template: QuestTemplate }
}

export async function useTemplate(token: string, id: number) {
  const res = await api.post(`/templates/${id}/use`, {}, authHeaders(token))
  return res.data as { quest: Quest }
}

export async function getReminders(token: string) {
  const res = await api.get('/reminders', authHeaders(token))
  return res.data as { reminder: ReminderPreference | null }
}

export async function saveReminders(token: string, payload: Partial<ReminderPreference>) {
  const res = await api.post('/reminders', payload, authHeaders(token))
  return res.data as { reminder: ReminderPreference }
}

export async function spendCoins(token: string, amount: number) {
  const res = await api.post('/coins/spend', { amount }, authHeaders(token))
  return res.data as { coins: number }
}

export async function updateCoinSettings(token: string, payload: { coin_rate?: number; xp_per_coin?: number }) {
  const res = await api.post('/coins/settings', payload, authHeaders(token))
  return res.data as { user: User }
}
