import { useEffect, useMemo, useRef, useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  completeQuest,
  createQuest,
  deleteQuest,
  equipTitle,
  getMe,
  getQuests,
  getTitles,
  listBuffs,
  savePushSubscription,
  updateQuest,
  getRewards,
  getBoss,
  getWeeklyRecap,
  getSkills,
  unlockSkill,
  recoverStreak,
  getParty,
  getPartyLeaderboard,
  createParty,
  joinParty,
  leaveParty,
  getContract,
  saveContract,
  getTemplates,
  createTemplate,
  useTemplate,
  getReminders,
  saveReminders,
  spendCoins,
  updateCoinSettings,
} from "./lib/api"
import type { Quest, QuestTemplate } from "./types"

const TOKEN = "" // auth removed; using demo user on API

function formatStatKey(key: string) {
  return key.charAt(0).toUpperCase() + key.slice(1)
}

function getErrorMessage(err: any, fallback = "Something went wrong.") {
  return err?.response?.data?.message || err?.message || fallback
}

const STAT_STYLES: Record<string, { border: string; dot: string; text: string }> = {
  mind: { border: "border-sky-400/70", dot: "bg-sky-400", text: "text-sky-100" },
  body: { border: "border-rose-400/70", dot: "bg-rose-400", text: "text-rose-100" },
  wealth: { border: "border-emerald-400/70", dot: "bg-emerald-400", text: "text-emerald-100" },
  discipline: { border: "border-amber-300/70", dot: "bg-amber-300", text: "text-amber-100" },
  order: { border: "border-violet-400/70", dot: "bg-violet-400", text: "text-violet-100" },
}

function getStatStyle(key: string) {
  return STAT_STYLES[key] || { border: "border-slate-400/40", dot: "bg-slate-400", text: "text-slate-200" }
}

type NavView = "dashboard" | "quests" | "stats" | "buffs" | "progress" | "journal" | "shop" | "settings"

type PriorityWeights = {
  main: number
  daily: number
  side: number
  xpWeight: number
  dueOverdue: number
  dueSoon: number
  dueToday: number
  dueUpcoming: number
  completedPenalty: number
  newQuestBonus: number
}

const DEFAULT_PRIORITY_WEIGHTS: PriorityWeights = {
  main: 60,
  daily: 35,
  side: 20,
  xpWeight: 0.25,
  dueOverdue: 45,
  dueSoon: 30,
  dueToday: 20,
  dueUpcoming: 10,
  completedPenalty: 25,
  newQuestBonus: 8,
}

const VIEW_PATHS: Record<NavView, string> = {
  dashboard: "/",
  quests: "/quests",
  stats: "/stats",
  buffs: "/buffs",
  progress: "/progress",
  journal: "/journal",
  shop: "/shop",
  settings: "/settings",
}

function isSameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
}

function completedToday(quest: Quest, now = new Date()) {
  return quest.events.some((event) => isSameDay(new Date(event.completed_at), now))
}

type XpSeries = {
  labels: string[]
  values: number[]
  max: number
}

type CalendarCell = {
  key: string
  date: Date
  xp: number
} | null

type JournalEntry = {
  id: string
  date: string
  mood: number
  gratitude: string
  win: string
  challenge: string
  notes: string
}

type JournalForm = {
  date: string
  mood: number
  gratitude: string
  win: string
  challenge: string
  notes: string
}

const JOURNAL_STORAGE_KEY = "mylife.journalEntries"
const DEFAULT_COIN_RATE = 0.02

type ShopCategory = "buff" | "theme" | "perk"

type ShopItem = {
  id: string
  name: string
  description: string
  effect: string
  costCoins: number
  category: ShopCategory
}

type ShopState = {
  owned: string[]
  spent: number
}

const SHOP_STORAGE_KEY = "mylife.shopState"

const SHOP_CATEGORIES: { key: ShopCategory; label: string; subtitle: string }[] = [
  { key: "buff", label: "Buffs", subtitle: "Momentum boosters and streak aids." },
  { key: "theme", label: "Themes", subtitle: "Cosmetic palettes for the HQ." },
  { key: "perk", label: "Perks", subtitle: "System upgrades for faster progress." },
]

const SHOP_ITEMS: ShopItem[] = [
  {
    id: "buff-momentum-anchor",
    name: "Momentum Anchor",
    description: "Protects your streak from one slip-up.",
    effect: "+1 resilience token (cosmetic for now).",
    costCoins: 120,
    category: "buff",
  },
  {
    id: "buff-xp-surge",
    name: "XP Surge",
    description: "Feels like a double XP day.",
    effect: "Next 5 quest completions feel legendary.",
    costCoins: 160,
    category: "buff",
  },
  {
    id: "theme-aurora",
    name: "Aurora Drift",
    description: "A cool, neon palette for night mode.",
    effect: "Unlocks a new UI theme.",
    costCoins: 90,
    category: "theme",
  },
  {
    id: "theme-ember",
    name: "Ember Focus",
    description: "Warm gradients for high-intensity days.",
    effect: "Unlocks a second UI theme.",
    costCoins: 90,
    category: "theme",
  },
  {
    id: "perk-auto-planner",
    name: "Auto Planner+",
    description: "Boost your daily plan suggestions.",
    effect: "Priority engine gets smarter.",
    costCoins: 200,
    category: "perk",
  },
  {
    id: "perk-fast-recap",
    name: "Fast Recap",
    description: "One-tap recap builder for the journal.",
    effect: "Adds summary templates to logs.",
    costCoins: 140,
    category: "perk",
  },
]

function dateKey(date: Date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, "0")
  const d = String(date.getDate()).padStart(2, "0")
  return `${y}-${m}-${d}`
}

function formatShort(date: Date) {
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}

function buildXpSeries(quests: Quest[], days = 14): XpSeries {
  const now = new Date()
  const start = new Date(now)
  start.setHours(0, 0, 0, 0)
  start.setDate(start.getDate() - (days - 1))
  const map: Record<string, number> = {}
  const labels: string[] = []

  for (let i = 0; i < days; i += 1) {
    const day = new Date(start)
    day.setDate(start.getDate() + i)
    const key = dateKey(day)
    map[key] = 0
    labels.push(formatShort(day))
  }

  quests.forEach((quest) => {
    quest.events.forEach((event) => {
      const eventDate = new Date(event.completed_at)
      if (eventDate < start) return
      const key = dateKey(eventDate)
      if (key in map) {
        map[key] += event.xp_earned
      }
    })
  })

  const values = labels.map((_, idx) => {
    const day = new Date(start)
    day.setDate(start.getDate() + idx)
    return map[dateKey(day)] || 0
  })
  const max = Math.max(10, ...values)
  return { labels, values, max }
}

function buildCoinSeries(quests: Quest[], rate: number, days = 14): XpSeries {
  const now = new Date()
  const start = new Date(now)
  start.setHours(0, 0, 0, 0)
  start.setDate(start.getDate() - (days - 1))
  const map: Record<string, number> = {}
  const labels: string[] = []

  for (let i = 0; i < days; i += 1) {
    const day = new Date(start)
    day.setDate(start.getDate() + i)
    const key = dateKey(day)
    map[key] = 0
    labels.push(formatShort(day))
  }

  quests.forEach((quest) => {
    quest.events.forEach((event) => {
      const eventDate = new Date(event.completed_at)
      if (eventDate < start) return
      const key = dateKey(eventDate)
      if (key in map) {
        const earnedCoins = event.coins_earned && event.coins_earned > 0 ? event.coins_earned : coinsFromXp(event.xp_earned, rate)
        map[key] += earnedCoins
      }
    })
  })

  const values = labels.map((_, idx) => {
    const day = new Date(start)
    day.setDate(start.getDate() + idx)
    return map[dateKey(day)] || 0
  })
  const max = Math.max(5, ...values)
  return { labels, values, max }
}

function buildCalendar(quests: Quest[], days = 21): CalendarCell[] {
  const now = new Date()
  const start = new Date(now)
  start.setHours(0, 0, 0, 0)
  start.setDate(start.getDate() - (days - 1))
  const xpMap: Record<string, number> = {}

  quests.forEach((quest) => {
    quest.events.forEach((event) => {
      const eventDate = new Date(event.completed_at)
      if (eventDate < start) return
      const key = dateKey(eventDate)
      xpMap[key] = (xpMap[key] || 0) + event.xp_earned
    })
  })

  const cells: CalendarCell[] = []
  const pad = start.getDay()
  for (let i = 0; i < pad; i += 1) cells.push(null)

  for (let i = 0; i < days; i += 1) {
    const day = new Date(start)
    day.setDate(start.getDate() + i)
    const key = dateKey(day)
    cells.push({ key, date: day, xp: xpMap[key] || 0 })
  }
  return cells
}

function coinsFromXp(xp: number, rate = DEFAULT_COIN_RATE) {
  return Math.max(1, Math.round(xp * rate))
}

function loadJournalEntries() {
  if (typeof window === "undefined") return []
  try {
    const raw = window.localStorage.getItem(JOURNAL_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as JournalEntry[]
    return parsed.sort((a, b) => b.date.localeCompare(a.date))
  } catch {
    return []
  }
}

function loadShopState(): ShopState {
  if (typeof window === "undefined") return { owned: [], spent: 0 }
  try {
    const raw = window.localStorage.getItem(SHOP_STORAGE_KEY)
    if (!raw) return { owned: [], spent: 0 }
    const parsed = JSON.parse(raw) as ShopState
    const owned = Array.isArray(parsed.owned) ? parsed.owned : []
    const spent = typeof parsed.spent === "number" && parsed.spent > 0 ? parsed.spent : 0
    return { owned, spent }
  } catch {
    return { owned: [], spent: 0 }
  }
}

function buildJournalSummary(entry: JournalEntry) {
  const parts = []
  if (entry.win) parts.push(`Win: ${entry.win}`)
  if (entry.gratitude) parts.push(`Grateful for: ${entry.gratitude}`)
  if (entry.challenge) parts.push(`Challenge: ${entry.challenge}`)
  if (entry.notes) parts.push(entry.notes)
  return parts.join(" • ").slice(0, 180)
}

function calcJournalStreak(entries: JournalEntry[]) {
  if (entries.length === 0) return 0
  const set = new Set(entries.map((entry) => entry.date))
  let streak = 0
  const cursor = new Date()
  cursor.setHours(0, 0, 0, 0)
  while (set.has(dateKey(cursor))) {
    streak += 1
    cursor.setDate(cursor.getDate() - 1)
  }
  return streak
}

type DailyPlanItem = {
  quest: Quest
  block: { label: string; time: string }
  score: number
}

const TIME_BLOCKS = [
  { label: "Morning", time: "08:30" },
  { label: "Midday", time: "13:00" },
  { label: "Evening", time: "19:30" },
]

function scoreQuest(quest: Quest, now: Date, weights: PriorityWeights, seed: number) {
  let score = 0
  if (quest.type === "main") score += weights.main
  if (quest.type === "daily") score += weights.daily
  if (quest.type === "side") score += weights.side
  score += Math.min(quest.xp_reward, 200) * weights.xpWeight

  if (quest.due_date) {
    const due = new Date(quest.due_date)
    const diff = due.getTime() - now.getTime()
    if (diff <= 0) score += weights.dueOverdue
    else if (diff < 6 * 60 * 60 * 1000) score += weights.dueSoon
    else if (diff < 24 * 60 * 60 * 1000) score += weights.dueToday
    else if (diff < 3 * 24 * 60 * 60 * 1000) score += weights.dueUpcoming
  }

  if (completedToday(quest, now)) score -= weights.completedPenalty
  if (quest.events.length === 0) score += weights.newQuestBonus

  const jitter = (Math.sin((quest.id + seed) * 1.37) + 1) * 0.35
  return score + jitter
}

function urlBase64ToUint8Array(base64String: string) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/")
  const rawData = window.atob(base64)
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)))
}

const SkeletonCard = () => <div className="h-24 rounded-2xl panel-soft animate-pulse" />

const ProgressBar = ({ value, max }: { value: number; max: number }) => {
  const pct = max > 0 ? Math.max(0, Math.min(100, Math.round((value / max) * 100))) : 0
  return (
    <div className="h-3 rounded-full bg-white/10">
      <div
        className="h-full rounded-full bg-gradient-to-r from-rose-400 to-amber-300 transition-all duration-700 ease-out"
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

function StatCard({ label, value, tone }: { label: string; value: number; tone: { border: string; dot: string; text: string } }) {
  return (
    <div className={`panel-soft panel-hover panel-muted rounded-2xl border-l-4 p-4 ${tone.border}`}>
      <div className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${tone.dot}`} />
        <p className="text-sm text-slate-300">{label}</p>
      </div>
      <p className={`text-2xl font-semibold ${tone.text}`}>{value}</p>
    </div>
  )
}

function QuestCard({ quest, coinRate, onComplete, onEdit, onDelete }: { quest: Quest; coinRate: number; onComplete: (id: number) => void; onEdit: () => void; onDelete: () => void }) {
  const streak = quest.events.length
  const baseCoins = coinsFromXp(quest.xp_reward, coinRate)
  return (
    <div className="panel-soft panel-hover flex flex-col gap-2 rounded-2xl px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-white font-semibold">{quest.title}</p>
          <p className="text-sm text-slate-300">
            {quest.xp_reward} XP • Base {baseCoins} coins • Streak {streak}d
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={onEdit} className="rounded-lg border border-white/10 bg-white/10 px-3 py-2 text-xs font-semibold text-slate-100 hover:bg-white/20">
            Edit
          </button>
          <button onClick={onDelete} className="rounded-lg border border-rose-500/40 bg-rose-500/20 px-3 py-2 text-xs font-semibold text-rose-100 hover:brightness-110">
            Delete
          </button>
          <button onClick={() => onComplete(quest.id)} className="rounded-lg bg-emerald-400/90 px-3 py-2 text-xs font-semibold text-ink shadow-glow hover:scale-[1.02] transition">
            Complete
          </button>
        </div>
      </div>
      {quest.description && <p className="text-sm text-slate-200">{quest.description}</p>}
    </div>
  )
}

const BuffChip = ({ label, detail }: { label: string; detail: string }) => (
  <div className="animate-pop flex items-center gap-2 rounded-full border border-emerald-300/60 bg-emerald-300/15 px-3 py-1 text-sm text-emerald-100">
    <span className="h-2 w-2 rounded-full bg-emerald-300" />
    <span className="font-semibold">{label}</span>
    <span className="text-emerald-50/80">{detail}</span>
  </div>
)

function QuestForm({ initial, type, onCreate, onUpdate }: { initial?: Quest; type: Quest["type"]; onCreate?: (data: { type: Quest["type"]; title: string; description: string; xp_reward: number }) => void; onUpdate?: (id: number, data: Partial<Quest>) => void }) {
  const [title, setTitle] = useState(initial?.title ?? "")
  const [description, setDescription] = useState(initial?.description ?? "")
  const [xp, setXp] = useState(initial?.xp_reward ?? 20)

  const submit = () => {
    if (!title.trim()) return
    if (initial && onUpdate) {
      onUpdate(initial.id, { title: title.trim(), description, xp_reward: xp })
    } else if (onCreate) {
      onCreate({ type, title: title.trim(), description, xp_reward: xp })
      setTitle("")
      setDescription("")
      setXp(20)
    }
  }

  return (
    <div className="space-y-2 panel-soft rounded-2xl p-4">
      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Quest title" className="w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400" />
      <textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description (optional)" className="w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400" />
      <div className="flex items-center justify-between gap-3 text-sm text-slate-200">
        <label className="flex items-center gap-2">
          XP
          <input type="number" value={xp} min={5} max={500} onChange={(e) => setXp(Number(e.target.value))} className="w-24 rounded-lg border border-white/10 bg-white/10 px-2 py-1 text-white outline-none focus:border-sky-400" />
        </label>
        <button onClick={submit} className="rounded-xl bg-gradient-to-r from-emerald-400 to-sky-400 px-3 py-2 text-sm font-semibold text-ink shadow-glow hover:scale-[1.02] transition">
          {initial ? "Save" : "Add"}
        </button>
      </div>
    </div>
  )
}

export default function App() {
  const queryClient = useQueryClient()
  const location = useLocation()
  const navigate = useNavigate()
  const [showFormFor, setShowFormFor] = useState<Quest["type"] | null>(null)
  const [editing, setEditing] = useState<Quest | null>(null)
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null)
  const [navCollapsed, setNavCollapsed] = useState(false)
  const [timeLeft, setTimeLeft] = useState("...")
  const [xpPulse, setXpPulse] = useState(false)
  const [streakPulse, setStreakPulse] = useState(false)
  const [navOverlayOpen, setNavOverlayOpen] = useState(false)
  const [planSeed, setPlanSeed] = useState(0)
  const [focusMinutes, setFocusMinutes] = useState(25)
  const [focusQuestId, setFocusQuestId] = useState<number | null>(null)
  const [focusRemaining, setFocusRemaining] = useState(25 * 60)
  const [focusRunning, setFocusRunning] = useState(false)
  const [focusComplete, setFocusComplete] = useState(false)
  const prevXp = useRef<number | null>(null)
  const prevStreak = useRef<number | null>(null)
  const [journalEntries, setJournalEntries] = useState<JournalEntry[]>(() => loadJournalEntries())
  const [journalForm, setJournalForm] = useState<JournalForm>(() => ({
    date: dateKey(new Date()),
    mood: 3,
    gratitude: "",
    win: "",
    challenge: "",
    notes: "",
  }))
  const [priorityWeights, setPriorityWeights] = useState<PriorityWeights>(() => {
    if (typeof window === "undefined") return DEFAULT_PRIORITY_WEIGHTS
    try {
      const raw = window.localStorage.getItem("mylife.priorityWeights")
      if (!raw) return DEFAULT_PRIORITY_WEIGHTS
      return { ...DEFAULT_PRIORITY_WEIGHTS, ...JSON.parse(raw) }
    } catch {
      return DEFAULT_PRIORITY_WEIGHTS
    }
  })

  const [partyName, setPartyName] = useState("My Party")
  const [partyCode, setPartyCode] = useState("")
  const [contractForm, setContractForm] = useState({ target_streak: 7, pledge: "No sugar for a week", reward: "New book", active: true })
  const [templateForm, setTemplateForm] = useState<{ type: QuestTemplate["type"]; title: string; description: string; xp_reward: number }>({
    type: "daily",
    title: "",
    description: "",
    xp_reward: 10,
  })
  const [reminderForm, setReminderForm] = useState({ time: "09:00", timezone: "local", enabled: true })
  const [coinRateForm, setCoinRateForm] = useState(50)
  const [shopState, setShopState] = useState<ShopState>(() => loadShopState())

  const meQuery = useQuery({ queryKey: ["me"], queryFn: () => getMe(TOKEN) })
  const questsQuery = useQuery({ queryKey: ["quests"], queryFn: () => getQuests(TOKEN) })
  const titlesQuery = useQuery({ queryKey: ["titles"], queryFn: () => getTitles(TOKEN) })
  const buffsQuery = useQuery({ queryKey: ["buffs"], queryFn: () => listBuffs(TOKEN) })
  const rewardsQuery = useQuery({ queryKey: ["rewards"], queryFn: () => getRewards(TOKEN) })
  const bossQuery = useQuery({ queryKey: ["boss"], queryFn: () => getBoss(TOKEN) })
  const recapQuery = useQuery({ queryKey: ["recap"], queryFn: () => getWeeklyRecap(TOKEN) })
  const skillsQuery = useQuery({ queryKey: ["skills"], queryFn: () => getSkills(TOKEN) })
  const partyQuery = useQuery({ queryKey: ["party"], queryFn: () => getParty(TOKEN) })
  const partyLeaderboardQuery = useQuery({ queryKey: ["partyLeaderboard"], queryFn: () => getPartyLeaderboard(TOKEN) })
  const contractQuery = useQuery({ queryKey: ["contract"], queryFn: () => getContract(TOKEN) })
  const templatesQuery = useQuery({ queryKey: ["templates"], queryFn: () => getTemplates(TOKEN) })
  const remindersQuery = useQuery({ queryKey: ["reminders"], queryFn: () => getReminders(TOKEN) })
  const me = meQuery.data?.user
  const journalStreak = useMemo(() => calcJournalStreak(journalEntries), [journalEntries])
  const latestJournal = journalEntries[0]
  const journalSummary = latestJournal ? buildJournalSummary(latestJournal) : ""
  const ownedUpgrades = useMemo(() => new Set(shopState.owned), [shopState.owned])
  const coinRate = me?.coin_rate ?? DEFAULT_COIN_RATE
  const xpPerCoin = Math.max(1, Math.round(1 / coinRate))
  const availableCoins = Math.max(0, me?.coins ?? 0)

  useEffect(() => {
    if (contractQuery.data?.contract) {
      const c = contractQuery.data.contract
      setContractForm({ target_streak: c.target_streak, pledge: c.pledge, reward: c.reward, active: c.active })
    }
  }, [contractQuery.data])

  useEffect(() => {
    if (remindersQuery.data?.reminder) {
      const r = remindersQuery.data.reminder
      setReminderForm({ time: r.time, timezone: r.timezone, enabled: r.enabled })
    }
  }, [remindersQuery.data])

  useEffect(() => {
    if (me?.coin_rate) {
      setCoinRateForm(Math.max(1, Math.round(1 / me.coin_rate)))
    }
  }, [me?.coin_rate])

  useEffect(() => {
    if (typeof window === "undefined") return
    window.localStorage.setItem("mylife.priorityWeights", JSON.stringify(priorityWeights))
  }, [priorityWeights])

  useEffect(() => {
    if (typeof window === "undefined") return
    window.localStorage.setItem(JOURNAL_STORAGE_KEY, JSON.stringify(journalEntries))
  }, [journalEntries])

  useEffect(() => {
    if (typeof window === "undefined") return
    window.localStorage.setItem(SHOP_STORAGE_KEY, JSON.stringify(shopState))
  }, [shopState])

  useEffect(() => {
    const tick = () => {
      const now = new Date()
      const end = new Date()
      end.setHours(23, 59, 59, 999)
      const diff = end.getTime() - now.getTime()
      if (diff <= 0) {
        setTimeLeft("reset imminent")
        return
      }
      const hours = Math.floor(diff / (1000 * 60 * 60))
      const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
      setTimeLeft(`${hours}h ${mins}m`)
    }
    tick()
    const id = window.setInterval(tick, 60000)
    return () => window.clearInterval(id)
  }, [])

  useEffect(() => {
    if (me?.xp_total == null) return
    let timer: number | undefined
    if (prevXp.current != null && me.xp_total > prevXp.current) {
      setXpPulse(true)
      timer = window.setTimeout(() => setXpPulse(false), 900)
    }
    prevXp.current = me.xp_total
    return () => {
      if (timer) window.clearTimeout(timer)
    }
  }, [me?.xp_total])

  useEffect(() => {
    if (me?.streak_days == null) return
    let timer: number | undefined
    if (prevStreak.current != null && me.streak_days > prevStreak.current) {
      setStreakPulse(true)
      timer = window.setTimeout(() => setStreakPulse(false), 900)
    }
    prevStreak.current = me.streak_days
    return () => {
      if (timer) window.clearTimeout(timer)
    }
  }, [me?.streak_days])

  useEffect(() => {
    if (!focusRunning) return
    const id = window.setInterval(() => {
      setFocusRemaining((prev) => {
        if (prev <= 1) {
          setFocusRunning(false)
          setFocusComplete(true)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => window.clearInterval(id)
  }, [focusRunning])

  useEffect(() => {
    if (!focusRunning) {
      setFocusRemaining(focusMinutes * 60)
      setFocusComplete(false)
    }
  }, [focusMinutes, focusQuestId, focusRunning])

  const saveJournalEntry = () => {
    const trimmed = {
      date: journalForm.date,
      mood: journalForm.mood,
      gratitude: journalForm.gratitude.trim(),
      win: journalForm.win.trim(),
      challenge: journalForm.challenge.trim(),
      notes: journalForm.notes.trim(),
    }
    if (!trimmed.gratitude && !trimmed.win && !trimmed.challenge && !trimmed.notes) {
      setToast({ type: "error", message: "Add at least one note before saving." })
      return
    }
    const entry: JournalEntry = {
      id: `${trimmed.date}-${Math.random().toString(16).slice(2, 7)}`,
      ...trimmed,
    }
    setJournalEntries((prev) => {
      const withoutDate = prev.filter((item) => item.date !== trimmed.date)
      return [entry, ...withoutDate].sort((a, b) => b.date.localeCompare(a.date))
    })
    setToast({ type: "success", message: "Reflection saved." })
  }

  const clearJournalForm = () => {
    setJournalForm({
      date: dateKey(new Date()),
      mood: 3,
      gratitude: "",
      win: "",
      challenge: "",
      notes: "",
    })
  }

  const deleteJournalEntry = (entryId: string) => {
    setJournalEntries((prev) => prev.filter((entry) => entry.id !== entryId))
    setToast({ type: "success", message: "Entry removed." })
  }

  const purchaseUpgrade = (item: ShopItem) => {
    if (ownedUpgrades.has(item.id)) {
      setToast({ type: "error", message: "Already unlocked." })
      return
    }
    if (item.costCoins > availableCoins) {
      setToast({ type: "error", message: "Not enough coins." })
      return
    }
    spendCoinsMutation.mutate({ amount: item.costCoins, item })
  }


  const completeMutation = useMutation({
    mutationFn: (id: number) => completeQuest(id, TOKEN),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["me"] })
      queryClient.invalidateQueries({ queryKey: ["quests"] })
      queryClient.invalidateQueries({ queryKey: ["buffs"] })
      queryClient.invalidateQueries({ queryKey: ["boss"] })
      queryClient.invalidateQueries({ queryKey: ["rewards"] })
      queryClient.invalidateQueries({ queryKey: ["recap"] })
      const detail = data.details?.length ? ` (${data.details.join(", ")})` : ""
      const coinsNote = data.coins_earned ? ` +${data.coins_earned} coins` : ""
      setToast({ type: "success", message: `Quest completed! XP applied${detail}.${coinsNote}` })
    },
    onError: () => setToast({ type: "error", message: "Could not complete quest." }),
  })

  const createMutation = useMutation({
    mutationFn: (data: { type: Quest["type"]; title: string; description: string; xp_reward: number }) => createQuest(TOKEN, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["quests"] })
      setShowFormFor(null)
      setToast({ type: "success", message: "Quest created." })
    },
    onError: () => setToast({ type: "error", message: "Could not create quest." }),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Quest> }) => updateQuest(TOKEN, id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["quests"] })
      setEditing(null)
      setToast({ type: "success", message: "Quest updated." })
    },
    onError: () => setToast({ type: "error", message: "Could not update quest." }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteQuest(TOKEN, id),
    onMutate: async (id: number) => {
      await queryClient.cancelQueries({ queryKey: ["quests"] })
      const previous = queryClient.getQueryData<{ quests: Quest[] }>(["quests"])
      if (previous) {
        queryClient.setQueryData<{ quests: Quest[] }>(["quests"], {
          quests: previous.quests.filter((q) => q.id !== id),
        })
      }
      return { previous }
    },
    onError: (_err, _id, context) => {
      if (context?.previous) queryClient.setQueryData(["quests"], context.previous)
      setToast({ type: "error", message: "Could not delete quest." })
    },
    onSuccess: () => setToast({ type: "success", message: "Quest deleted." }),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ["quests"] }),
  })

  const equipMutation = useMutation({
    mutationFn: (id: number) => equipTitle(TOKEN, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["titles"] })
      queryClient.invalidateQueries({ queryKey: ["buffs"] })
      setToast({ type: "success", message: "Title equipped." })
    },
    onError: () => setToast({ type: "error", message: "Could not equip title." }),
  })

  const unlockMutation = useMutation({
    mutationFn: (id: number) => unlockSkill(TOKEN, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["skills"] })
      queryClient.invalidateQueries({ queryKey: ["me"] })
      setToast({ type: "success", message: "Skill unlocked." })
    },
    onError: (err) => setToast({ type: "error", message: getErrorMessage(err, "Could not unlock skill.") }),
  })

  const recoverMutation = useMutation({
    mutationFn: () => recoverStreak(TOKEN),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["me"] })
      setToast({ type: "success", message: "Resilience token used." })
    },
    onError: (err) => setToast({ type: "error", message: getErrorMessage(err, "No tokens available.") }),
  })

  const createPartyMutation = useMutation({
    mutationFn: () => createParty(TOKEN, partyName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["party"] })
      setToast({ type: "success", message: "Party created." })
    },
    onError: (err) => setToast({ type: "error", message: getErrorMessage(err, "Could not create party.") }),
  })

  const joinPartyMutation = useMutation({
    mutationFn: () => joinParty(TOKEN, partyCode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["party"] })
      setToast({ type: "success", message: "Joined party." })
    },
    onError: (err) => setToast({ type: "error", message: getErrorMessage(err, "Could not join party.") }),
  })

  const leavePartyMutation = useMutation({
    mutationFn: () => leaveParty(TOKEN),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["party"] })
      setToast({ type: "success", message: "Left party." })
    },
    onError: (err) => setToast({ type: "error", message: getErrorMessage(err, "Could not leave party.") }),
  })

  const contractMutation = useMutation({
    mutationFn: () => saveContract(TOKEN, contractForm),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contract"] })
      setToast({ type: "success", message: "Contract saved." })
    },
    onError: (err) => setToast({ type: "error", message: getErrorMessage(err, "Could not save contract.") }),
  })

  const templateMutation = useMutation({
    mutationFn: () => createTemplate(TOKEN, templateForm),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] })
      setTemplateForm({ type: "daily", title: "", description: "", xp_reward: 10 })
      setToast({ type: "success", message: "Template created." })
    },
    onError: (err) => setToast({ type: "error", message: getErrorMessage(err, "Could not create template.") }),
  })

  const useTemplateMutation = useMutation({
    mutationFn: (id: number) => useTemplate(TOKEN, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["quests"] })
      setToast({ type: "success", message: "Quest created from template." })
    },
  })

  const reminderMutation = useMutation({
    mutationFn: () => saveReminders(TOKEN, reminderForm),
    onSuccess: () => setToast({ type: "success", message: "Reminder saved." }),
    onError: (err) => setToast({ type: "error", message: getErrorMessage(err, "Could not save reminder.") }),
  })

  const pushMutation = useMutation({
    mutationFn: async () => {
      if (!("serviceWorker" in navigator) || !("PushManager" in window)) return
      const perm = await Notification.requestPermission()
      if (perm !== "granted") throw new Error("Notifications blocked")
      const reg = await navigator.serviceWorker.ready
      const vapid = import.meta.env.VITE_VAPID_PUBLIC_KEY
      if (!vapid) throw new Error("VAPID key not set")
      const sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(vapid) })
      return savePushSubscription(TOKEN, sub.toJSON())
    },
    onSuccess: () => setToast({ type: "success", message: "Reminders enabled." }),
    onError: (err) => setToast({ type: "error", message: getErrorMessage(err, "Could not enable reminders.") }),
  })

  const spendCoinsMutation = useMutation({
    mutationFn: ({ amount }: { amount: number; item: ShopItem }) => spendCoins(TOKEN, amount),
    onSuccess: (_data, payload) => {
      queryClient.invalidateQueries({ queryKey: ["me"] })
      setShopState((prev) => ({ owned: [...prev.owned, payload.item.id], spent: prev.spent + payload.amount }))
      setToast({ type: "success", message: `${payload.item.name} unlocked.` })
    },
    onError: (err) => setToast({ type: "error", message: getErrorMessage(err, "Not enough coins.") }),
  })

  const coinSettingsMutation = useMutation({
    mutationFn: ({ xpPerCoin }: { xpPerCoin: number }) => updateCoinSettings(TOKEN, { xp_per_coin: xpPerCoin }),
    onSuccess: (data) => {
      queryClient.setQueryData(["me"], data)
      queryClient.invalidateQueries({ queryKey: ["me"] })
      setToast({ type: "success", message: "Coin earning updated." })
    },
    onError: (err) => setToast({ type: "error", message: getErrorMessage(err, "Could not update coin settings.") }),
  })


  const quests = questsQuery.data?.quests ?? []
  const titles = titlesQuery.data?.titles ?? []
  const buffs = buffsQuery.data?.buffs ?? me?.buffs ?? []
  const rewards = rewardsQuery.data?.rewards ?? []
  const boss = bossQuery.data?.boss
  const recap = recapQuery.data?.recap
  const skills = skillsQuery.data?.skills ?? []
  const party = partyQuery.data?.party
  const partyLeaderboard = partyLeaderboardQuery.data?.members ?? []
  const contract = contractQuery.data?.contract
  const templates = templatesQuery.data?.templates ?? []
  const reminders = remindersQuery.data?.reminder

  const dailyQuests = useMemo(() => quests.filter((q) => q.type === "daily"), [quests])
  const sideQuests = useMemo(() => quests.filter((q) => q.type === "side"), [quests])
  const mainQuests = useMemo(() => quests.filter((q) => q.type === "main"), [quests])

  const statsEntries = useMemo(() => Object.entries(me?.stats || {}), [me])
  const activeTitle = useMemo(() => titles.find((t) => t.active), [titles])

  const xpInfo = useMemo(() => {
    const total = me?.xp_total ?? 0
    const level = me?.level ?? 1
    const threshold = (lvl: number) => Math.floor(100 * Math.pow(lvl, 1.5))
    const prev = level <= 1 ? 0 : threshold(level)
    const next = threshold(level + 1)
    const span = Math.max(1, next - prev)
    const progress = Math.max(0, total - prev)
    return { total, prev, next, span, progress }
  }, [me])

  const featuredQuest = useMemo(() => {
    const now = new Date()
    const scored = quests
      .filter((q) => q.is_active !== false)
      .map((quest) => ({ quest, score: scoreQuest(quest, now, priorityWeights, planSeed) }))
      .sort((a, b) => b.score - a.score)
    return scored[0]?.quest ?? null
  }, [priorityWeights, quests, planSeed])

  const featuredLabel = featuredQuest
    ? featuredQuest.type === "main"
      ? "Main Focus"
      : featuredQuest.type === "daily"
        ? "Daily Focus"
        : "Side Focus"
    : "Main Focus"

  const dailyPlan = useMemo<DailyPlanItem[]>(() => {
    const now = new Date()
    const scored = quests
      .filter((q) => q.is_active !== false)
      .map((quest) => ({ quest, score: scoreQuest(quest, now, priorityWeights, planSeed) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 3)
    return scored.map((item, index) => ({
      quest: item.quest,
      score: item.score,
      block: TIME_BLOCKS[index] ?? TIME_BLOCKS[TIME_BLOCKS.length - 1],
    }))
  }, [priorityWeights, quests, planSeed])

  const focusQuest = useMemo(() => quests.find((q) => q.id === focusQuestId) || dailyPlan[0]?.quest || null, [dailyPlan, focusQuestId, quests])

  const todayRecap = useMemo(() => {
    const now = new Date()
    let xp = 0
    let completed = 0
    let coins = 0
    let topQuest: { title: string; xp: number } | null = null
    quests.forEach((quest) => {
      let questXp = 0
      const hasToday = quest.events.some((event) => isSameDay(new Date(event.completed_at), now))
      if (hasToday) completed += 1
      quest.events.forEach((event) => {
        if (isSameDay(new Date(event.completed_at), now)) {
          xp += event.xp_earned
          questXp += event.xp_earned
          const earnedCoins = event.coins_earned && event.coins_earned > 0 ? event.coins_earned : coinsFromXp(event.xp_earned, coinRate)
          coins += earnedCoins
        }
      })
      if (questXp > 0 && (!topQuest || questXp > topQuest.xp)) {
        topQuest = { title: quest.title, xp: questXp }
      }
    })
    return { xp, completed, coins, topQuest }
  }, [coinRate, quests])

  const xpSeries = useMemo(() => buildXpSeries(quests, 14), [quests])
  const xpWeek = useMemo(() => buildXpSeries(quests, 7), [quests])
  const coinSeries = useMemo(() => buildCoinSeries(quests, coinRate, 14), [quests, coinRate])
  const coinWeek = useMemo(() => buildCoinSeries(quests, coinRate, 7), [quests, coinRate])
  const calendarCells = useMemo(() => buildCalendar(quests, 21), [quests])

  const xpWeekTotal = xpWeek.values.reduce((sum, v) => sum + v, 0)
  const xpWeekAvg = Math.round(xpWeekTotal / Math.max(1, xpWeek.values.length))
  const xpMax = xpSeries.max
  const coinWeekTotal = coinWeek.values.reduce((sum, v) => sum + v, 0)
  const coinWeekAvg = Math.round(coinWeekTotal / Math.max(1, coinWeek.values.length))
  const coinMax = coinSeries.max

  const xpPath = useMemo(() => {
    const points = xpSeries.values.map((value, index) => {
      const x = xpSeries.values.length === 1 ? 0 : (index / (xpSeries.values.length - 1)) * 100
      const y = 40 - (value / xpMax) * 30
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    return points.length ? `M ${points.join(" L ")}` : ""
  }, [xpSeries, xpMax])

  const xpArea = useMemo(() => {
    if (!xpPath) return ""
    return `${xpPath} L 100,40 L 0,40 Z`
  }, [xpPath])

  const coinPath = useMemo(() => {
    const points = coinSeries.values.map((value, index) => {
      const x = coinSeries.values.length === 1 ? 0 : (index / (coinSeries.values.length - 1)) * 100
      const y = 40 - (value / coinMax) * 30
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    return points.length ? `M ${points.join(" L ")}` : ""
  }, [coinSeries, coinMax])

  const coinArea = useMemo(() => {
    if (!coinPath) return ""
    return `${coinPath} L 100,40 L 0,40 Z`
  }, [coinPath])

  const coinHistory = useMemo(() => {
    const entries: { id: string; quest: string; date: string; coins: number; xp: number }[] = []
    quests.forEach((quest) => {
      quest.events.forEach((event) => {
        const earnedCoins = event.coins_earned && event.coins_earned > 0 ? event.coins_earned : coinsFromXp(event.xp_earned, coinRate)
        entries.push({
          id: `${quest.id}-${event.id}`,
          quest: quest.title,
          date: event.completed_at,
          coins: earnedCoins,
          xp: event.xp_earned,
        })
      })
    })
    return entries
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
      .slice(0, 12)
  }, [coinRate, quests])

  useEffect(() => {
    if (!focusQuestId && dailyPlan[0]?.quest) {
      setFocusQuestId(dailyPlan[0].quest.id)
    }
  }, [dailyPlan, focusQuestId])

  const normalizedPath = useMemo(() => location.pathname.replace(/\/+$/, "") || "/", [location.pathname])

  const activeView = useMemo<NavView>(() => {
    const match = (Object.entries(VIEW_PATHS) as [NavView, string][]).find(([, path]) => path === normalizedPath)
    return match?.[0] ?? "dashboard"
  }, [normalizedPath])

  useEffect(() => {
    const paths = new Set(Object.values(VIEW_PATHS))
    if (!paths.has(normalizedPath)) {
      navigate(VIEW_PATHS.dashboard, { replace: true })
    }
  }, [navigate, normalizedPath])

  const navSections: { label: string; icon: string; items: { label: string; view: NavView; path: string }[] }[] = [
    { label: "Dashboard", icon: "D", items: [{ label: "Home", view: "dashboard", path: VIEW_PATHS.dashboard }, { label: "Today's focus", view: "dashboard", path: VIEW_PATHS.dashboard }, { label: "Streak & XP", view: "dashboard", path: VIEW_PATHS.dashboard }] },
    { label: "Quests", icon: "Q", items: [{ label: "Daily quests", view: "quests", path: VIEW_PATHS.quests }, { label: "Side quests", view: "quests", path: VIEW_PATHS.quests }, { label: "Main quest", view: "quests", path: VIEW_PATHS.quests }, { label: "History", view: "quests", path: VIEW_PATHS.quests }] },
    { label: "Stats", icon: "S", items: [{ label: "Body", view: "stats", path: VIEW_PATHS.stats }, { label: "Mind", view: "stats", path: VIEW_PATHS.stats }, { label: "Wealth", view: "stats", path: VIEW_PATHS.stats }, { label: "Discipline", view: "stats", path: VIEW_PATHS.stats }, { label: "Order", view: "stats", path: VIEW_PATHS.stats }] },
    { label: "Buffs & Titles", icon: "B", items: [{ label: "Active buffs", view: "buffs", path: VIEW_PATHS.buffs }, { label: "Titles earned", view: "buffs", path: VIEW_PATHS.buffs }] },
    { label: "Progress", icon: "P", items: [{ label: "XP history", view: "progress", path: VIEW_PATHS.progress }, { label: "Streak calendar", view: "progress", path: VIEW_PATHS.progress }, { label: "Level timeline", view: "progress", path: VIEW_PATHS.progress }] },
    { label: "Logs / Journal", icon: "L", items: [{ label: "Notes", view: "journal", path: VIEW_PATHS.journal }, { label: "Reflections", view: "journal", path: VIEW_PATHS.journal }] },
    { label: "Shop / Upgrades", icon: "U", items: [{ label: "Buy buffs", view: "shop", path: VIEW_PATHS.shop }, { label: "Themes", view: "shop", path: VIEW_PATHS.shop }, { label: "Perks", view: "shop", path: VIEW_PATHS.shop }] },
    { label: "Settings", icon: "X", items: [{ label: "Reminders", view: "settings", path: VIEW_PATHS.settings }, { label: "Difficulty", view: "settings", path: VIEW_PATHS.settings }, { label: "Reset", view: "settings", path: VIEW_PATHS.settings }] },
  ]

  const viewMeta: Record<NavView, { eyebrow: string; title: string; subtitle: string }> = {
    dashboard: { eyebrow: "Dashboard", title: "Overview", subtitle: "Your command center for the day." },
    quests: { eyebrow: "Quests", title: "Mission Control", subtitle: "Track daily, side, and main quests." },
    stats: { eyebrow: "Stats", title: "Attribute Lab", subtitle: "See how your actions shape each stat." },
    buffs: { eyebrow: "Buffs & Titles", title: "Power Deck", subtitle: "Stack bonuses and equip titles." },
    progress: { eyebrow: "Progress", title: "Momentum Tracker", subtitle: "Review XP, streaks, and weekly progress." },
    journal: { eyebrow: "Journal", title: "Reflection Log", subtitle: "Capture insights and daily notes." },
    shop: { eyebrow: "Upgrades", title: "Reward Vault", subtitle: "Spend XP on perks and upgrades (soon)." },
    settings: { eyebrow: "Settings", title: "Control Room", subtitle: "Tune reminders and difficulty." },
  }

  const viewIcons: Record<NavView, string> = {
    dashboard: "D",
    quests: "Q",
    stats: "S",
    buffs: "B",
    progress: "P",
    journal: "L",
    shop: "U",
    settings: "X",
  }

  const quickNav = (Object.entries(viewMeta) as [NavView, { eyebrow: string; title: string; subtitle: string }][]).filter(([view]) => view !== "dashboard").map(([view, meta]) => ({
    view,
    title: meta.title,
    subtitle: meta.subtitle,
    path: VIEW_PATHS[view],
    icon: viewIcons[view],
  }))

  const isDashboard = activeView === "dashboard"
  const isQuestsView = activeView === "quests"
  const isStatsView = activeView === "stats"
  const isBuffsView = activeView === "buffs"
  const isProgressView = activeView === "progress"
  const isJournalView = activeView === "journal"
  const isShopView = activeView === "shop"
  const isSettingsView = activeView === "settings"
  const showSidebar = isStatsView || isBuffsView || isProgressView || isSettingsView

  const toggleForm = (type: Quest["type"]) => {
    setEditing(null)
    setShowFormFor((prev) => (prev === type ? null : type))
  }

  const updateWeight = (key: keyof PriorityWeights, value: number) => {
    setPriorityWeights((prev) => ({ ...prev, [key]: value }))
  }

  const resetWeights = () => setPriorityWeights(DEFAULT_PRIORITY_WEIGHTS)

  return (
    <div className="min-h-screen text-white">
      <div className="mx-auto flex max-w-7xl gap-6 px-6 py-8">
        <aside className={`panel sticky top-6 hidden h-[calc(100vh-3rem)] flex-col gap-4 rounded-3xl p-4 lg:flex ${navCollapsed ? "w-16" : "w-60"}`}>
          <div className="flex items-center justify-between">
            {!navCollapsed && <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Navigation</p>}
            <button
              onClick={() => setNavCollapsed((prev) => !prev)}
              className="rounded-lg border border-white/10 bg-white/10 px-2 py-1 text-xs text-slate-200 hover:bg-white/20"
            >
              {navCollapsed ? ">>" : "<<"}
            </button>
          </div>
          <div className="flex flex-col gap-4 overflow-y-auto pr-1">
            {navSections.map((section) => {
              const sectionActive = section.items.some((item) => item.view === activeView)
              const primaryPath = section.items[0]?.path
              return (
                <div key={section.label} className="space-y-2">
                  <button
                    onClick={() => primaryPath && navigate(primaryPath)}
                    className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-semibold ${sectionActive ? "bg-emerald-400/15 text-emerald-100 shadow-glow" : "text-slate-200 hover:bg-white/10"}`}
                  >
                    <span className={`flex h-8 w-8 items-center justify-center rounded-lg border ${sectionActive ? "border-emerald-300/40 bg-emerald-300/10 text-emerald-100" : "border-white/10 bg-white/5 text-slate-200"}`}>
                      {section.icon}
                    </span>
                    {!navCollapsed && <span>{section.label}</span>}
                  </button>
                  {!navCollapsed && (
                    <div className="space-y-1 pl-11 text-xs text-slate-400">
                      {section.items.map((item) => (
                        <button
                          key={`${section.label}-${item.label}`}
                          onClick={() => navigate(item.path)}
                          className={`block w-full text-left transition ${item.view === activeView ? "text-emerald-200" : "hover:text-slate-200"}`}
                        >
                          {item.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col gap-6">
          <header className="panel relative rounded-3xl p-6">
          <button
            onClick={() => setNavOverlayOpen(true)}
            className="absolute right-5 top-5 rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-slate-100 hover:bg-white/20"
            aria-label="Open navigation menu"
            title="Open menu"
          >
            ≡
          </button>
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div className="space-y-2">
              <p className="text-xs uppercase tracking-[0.35em] text-emerald-200/80">MYLIFE</p>
              <h1 className="text-3xl font-semibold text-white font-display">Turn life into the game</h1>
              <p className="text-slate-300">Earn XP for everything. Momentum replaces motivation.</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
              <p className="text-xs text-slate-400">Player</p>
              <p className="text-lg font-semibold text-white">{me?.display_name ?? "Loading..."}</p>
              <p className="text-xs text-slate-400">{me?.email ?? "demo@mylife.local"}</p>
              <div className="mt-2 flex items-center justify-between text-xs text-slate-300">
                <span>Coins</span>
                <span className="font-semibold text-amber-200">{me?.coins ?? 0}</span>
              </div>
            </div>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className={`panel-soft panel-hover rounded-2xl p-4 ${xpPulse ? "xp-pulse" : ""}`}>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Level</p>
              <p className="text-5xl font-semibold text-white tracking-tight">Lv {me?.level ?? 1}</p>
              <p className="text-sm text-slate-300">XP {xpInfo.total}</p>
              <div className="mt-3 space-y-1">
                <ProgressBar value={xpInfo.progress} max={xpInfo.span} />
                <p className="text-xs text-slate-400">{xpInfo.progress}/{xpInfo.span} to next level</p>
              </div>
            </div>
            <div className={`panel-soft panel-hover rounded-2xl p-4 ${streakPulse ? "streak-pulse" : ""}`}>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Momentum</p>
              <p className="text-2xl font-semibold text-white">{me?.streak_days ?? 0} day streak</p>
              <p className="text-sm text-slate-300">Resilience tokens: {me?.resilience_tokens ?? 0}</p>
              <button
                onClick={() => recoverMutation.mutate()}
                className="mt-3 w-full rounded-xl border border-emerald-300/40 bg-emerald-300/10 px-3 py-2 text-sm font-semibold text-emerald-100 hover:bg-emerald-300/20"
              >
                Use a token
              </button>
            </div>
            <div className="panel-soft panel-hover rounded-2xl p-4">
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Active Title</p>
              <p className="text-2xl font-semibold text-white">{activeTitle?.name || "None equipped"}</p>
              <p className="text-sm text-slate-300">{activeTitle?.detail || "Equip a title for passive buffs."}</p>
            </div>
          </div>
        </header>

        {isDashboard && (
          <section className="panel rounded-3xl p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-slate-400">Today Engine</p>
                <h2 className="text-2xl font-semibold text-white">Focus, finish, and recap</h2>
                <p className="text-sm text-slate-300">Day ends in {timeLeft}</p>
              </div>
              <button
                onClick={() => setPlanSeed((prev) => prev + 1)}
                className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-slate-100 hover:bg-white/20"
              >
                Refresh plan
              </button>
            </div>

            <div className="mt-6 grid gap-4 lg:grid-cols-[1.4fr_1fr_1fr]">
              <div className="panel-soft panel-hover rounded-2xl p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase text-slate-400">Daily plan</p>
                    <h3 className="text-lg font-semibold text-white">Top 3 quests</h3>
                  </div>
                  {featuredQuest && (
                    <span className="rounded-full border border-emerald-300/40 bg-emerald-300/10 px-3 py-1 text-xs text-emerald-100">
                      {featuredLabel}
                    </span>
                  )}
                </div>
                <div className="mt-4 space-y-3">
                  {dailyPlan.length === 0 && <p className="text-sm text-slate-300">Add quests to generate a plan.</p>}
                  {dailyPlan.map((item) => (
                    <div key={item.quest.id} className="rounded-2xl border border-white/10 bg-white/5 px-3 py-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-semibold text-white">{item.quest.title}</p>
                          <p className="text-xs text-slate-400">{item.quest.xp_reward} XP • {item.quest.type}</p>
                        </div>
                        <span className="text-xs text-emerald-200">{item.block.label} · {item.block.time}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="panel-soft panel-hover rounded-2xl p-4">
                <p className="text-xs uppercase text-slate-400">Focus timer</p>
                <h3 className="text-lg font-semibold text-white">Start a session</h3>
                <div className="mt-3 space-y-3">
                  <select
                    value={focusQuest?.id ?? ""}
                    onChange={(e) => setFocusQuestId(Number(e.target.value))}
                    className="w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-white outline-none focus:border-sky-400"
                  >
                    {dailyPlan.map((item) => (
                      <option key={`focus-${item.quest.id}`} value={item.quest.id}>
                        {item.quest.title}
                      </option>
                    ))}
                    {dailyPlan.length === 0 && (
                      <option value="">Add quests to focus</option>
                    )}
                  </select>
                  <div className="flex gap-2">
                    {[25, 50, 90].map((mins) => (
                      <button
                        key={`mins-${mins}`}
                        onClick={() => setFocusMinutes(mins)}
                        className={`flex-1 rounded-xl border px-3 py-2 text-xs ${focusMinutes === mins ? "border-emerald-300/40 bg-emerald-300/10 text-emerald-100" : "border-white/10 bg-white/10 text-slate-200"}`}
                      >
                        {mins}m
                      </button>
                    ))}
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-4 text-center">
                    <p className="text-xs text-slate-400">Remaining</p>
                    <p className="text-3xl font-semibold text-white">
                      {Math.floor(focusRemaining / 60).toString().padStart(2, "0")}:{(focusRemaining % 60).toString().padStart(2, "0")}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    {!focusRunning ? (
                      <button
                        onClick={() => setFocusRunning(true)}
                        className="flex-1 rounded-xl bg-gradient-to-r from-emerald-400 to-sky-400 px-3 py-2 text-sm font-semibold text-ink shadow-glow"
                      >
                        Start
                      </button>
                    ) : (
                      <button
                        onClick={() => setFocusRunning(false)}
                        className="flex-1 rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-slate-100 hover:bg-white/20"
                      >
                        Pause
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setFocusRunning(false)
                        setFocusRemaining(focusMinutes * 60)
                        setFocusComplete(false)
                      }}
                      className="flex-1 rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-slate-100 hover:bg-white/20"
                    >
                      Reset
                    </button>
                  </div>
                  {focusComplete && focusQuest && (
                    <button
                      onClick={() => completeMutation.mutate(focusQuest.id)}
                      className="w-full rounded-xl border border-emerald-300/40 bg-emerald-300/10 px-3 py-2 text-sm text-emerald-100 hover:bg-emerald-300/20"
                    >
                      Apply to quest
                    </button>
                  )}
                </div>
              </div>

              <div className="panel-soft panel-hover rounded-2xl p-4">
                <p className="text-xs uppercase text-slate-400">End of day</p>
                <h3 className="text-lg font-semibold text-white">Live recap</h3>
                <div className="mt-4 space-y-3">
                  <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                    <p className="text-xs text-slate-400">Quests completed today</p>
                    <p className="text-2xl font-semibold text-white">{todayRecap.completed}</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                    <p className="text-xs text-slate-400">XP earned today</p>
                    <p className="text-2xl font-semibold text-white">{todayRecap.xp}</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                    <p className="text-xs text-slate-400">Coins earned today</p>
                    <p className="text-2xl font-semibold text-white">{todayRecap.coins}</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                    <p className="text-xs text-slate-400">Current streak</p>
                    <p className="text-2xl font-semibold text-white">{me?.streak_days ?? 0} days</p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {!isDashboard && (
          <section className="panel rounded-3xl p-6">
            <p className="text-xs uppercase tracking-[0.35em] text-slate-400">{viewMeta[activeView].eyebrow}</p>
            <h2 className="text-2xl font-semibold text-white">{viewMeta[activeView].title}</h2>
            <p className="text-sm text-slate-300">{viewMeta[activeView].subtitle}</p>
          </section>
        )}

        {isDashboard && (
          <section className="panel rounded-3xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-slate-400">Navigate</p>
                <h2 className="text-2xl font-semibold text-white">Jump to a section</h2>
                <p className="text-sm text-slate-300">Quick access to deeper pages.</p>
              </div>
              <button
                onClick={() => setNavOverlayOpen(true)}
                className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-slate-100 hover:bg-white/20"
              >
                Open menu
              </button>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {quickNav.map((item) => (
                <button
                  key={item.view}
                  onClick={() => navigate(item.path)}
                  className="panel-soft panel-hover flex flex-col items-start gap-2 rounded-2xl px-4 py-3 text-left"
                >
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/10 text-sm font-semibold text-white">
                    {item.icon}
                  </span>
                  <div>
                    <p className="text-base font-semibold text-white">{item.title}</p>
                    <p className="text-xs text-slate-300">{item.subtitle}</p>
                  </div>
                </button>
              ))}
            </div>
          </section>
        )}

        <div className={`grid gap-6 ${showSidebar ? "lg:grid-cols-[2fr_1fr]" : ""}`}>
          <div className="space-y-6">
            {(isDashboard || isStatsView) && (
              <section className="panel rounded-3xl p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-white font-display">Core Stats</h2>
                    <p className="text-sm text-slate-300">Every action strengthens a stat. Train the full stack.</p>
                  </div>
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                  {statsEntries.length === 0 && <SkeletonCard />}
                  {statsEntries.map(([key, value]) => (
                    <StatCard key={key} label={formatStatKey(key)} value={value as number} tone={getStatStyle(key)} />
                  ))}
                </div>
              </section>
            )}

            {(isDashboard || isQuestsView) && (
              <section className="panel rounded-3xl p-6 ring-1 ring-emerald-400/25">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-semibold text-white font-display">Quests</h2>
                  <p className="text-sm text-slate-300">Daily rituals, optional side missions, and main story arcs.</p>
                </div>
                {editing && (
                  <button onClick={() => setEditing(null)} className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-slate-200 hover:bg-white/20">
                    Cancel edit
                  </button>
                )}
              </div>

              {editing && (
                <div className="mt-4 space-y-3">
                  <p className="text-sm text-slate-300">Editing: <span className="text-white font-semibold">{editing.title}</span></p>
                  <QuestForm key={editing.id} initial={editing} type={editing.type} onUpdate={(id, data) => updateMutation.mutate({ id, data })} />
                </div>
              )}

              <div className="mt-6 grid gap-4">
                <div className="space-y-3 panel-soft panel-hover rounded-2xl p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-lg font-semibold text-white">Daily Quests</p>
                      <p className="text-sm text-slate-300">Show up every day to stack streak multipliers.</p>
                    </div>
                    <button onClick={() => toggleForm("daily")} className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-slate-100 hover:bg-white/20">
                      {showFormFor === "daily" ? "Hide" : "Add daily"}
                    </button>
                  </div>
                  {showFormFor === "daily" && <QuestForm type="daily" onCreate={(data) => createMutation.mutate(data)} />}
                  {questsQuery.isLoading && <SkeletonCard />}
                  {!questsQuery.isLoading && dailyQuests.length === 0 && <p className="text-sm text-slate-400">No daily quests yet.</p>}
                  {dailyQuests.map((quest) => (
                    <QuestCard
                      key={quest.id}
                      quest={quest}
                      coinRate={coinRate}
                      onComplete={(id) => completeMutation.mutate(id)}
                      onEdit={() => setEditing(quest)}
                      onDelete={() => deleteMutation.mutate(quest.id)}
                    />
                  ))}
                </div>

                <div className="space-y-3 panel-soft panel-hover rounded-2xl p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-lg font-semibold text-white">Side Quests</p>
                      <p className="text-sm text-slate-300">Optional tasks that keep life playful.</p>
                    </div>
                    <button onClick={() => toggleForm("side")} className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-slate-100 hover:bg-white/20">
                      {showFormFor === "side" ? "Hide" : "Add side"}
                    </button>
                  </div>
                  {showFormFor === "side" && <QuestForm type="side" onCreate={(data) => createMutation.mutate(data)} />}
                  {questsQuery.isLoading && <SkeletonCard />}
                  {!questsQuery.isLoading && sideQuests.length === 0 && <p className="text-sm text-slate-400">No side quests yet.</p>}
                  {sideQuests.map((quest) => (
                    <QuestCard
                      key={quest.id}
                      quest={quest}
                      coinRate={coinRate}
                      onComplete={(id) => completeMutation.mutate(id)}
                      onEdit={() => setEditing(quest)}
                      onDelete={() => deleteMutation.mutate(quest.id)}
                    />
                  ))}
                </div>

                <div className="space-y-3 panel-soft panel-hover rounded-2xl p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-lg font-semibold text-white">Main Quests</p>
                      <p className="text-sm text-slate-300">Long-term arcs that define your season.</p>
                    </div>
                    <button onClick={() => toggleForm("main")} className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-slate-100 hover:bg-white/20">
                      {showFormFor === "main" ? "Hide" : "Add main"}
                    </button>
                  </div>
                  {showFormFor === "main" && <QuestForm type="main" onCreate={(data) => createMutation.mutate(data)} />}
                  {questsQuery.isLoading && <SkeletonCard />}
                  {!questsQuery.isLoading && mainQuests.length === 0 && <p className="text-sm text-slate-400">No main quests yet.</p>}
                  {mainQuests.map((quest) => (
                    <QuestCard
                      key={quest.id}
                      quest={quest}
                      coinRate={coinRate}
                      onComplete={(id) => completeMutation.mutate(id)}
                      onEdit={() => setEditing(quest)}
                      onDelete={() => deleteMutation.mutate(quest.id)}
                    />
                  ))}
                </div>
              </div>
            </section>
            )}

            {(isDashboard || isBuffsView) && (
              <section className="panel rounded-3xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-white font-display">Titles & Buffs</h2>
                  <p className="text-sm text-slate-300">Equip a title for permanent boosts and stack streak buffs.</p>
                </div>
              </div>
              <div className="mt-4 grid gap-3 lg:grid-cols-2">
                <div className="space-y-2">
                  {titlesQuery.isLoading && <SkeletonCard />}
                  {titles.map((title) => (
                    <div key={title.id} className={`panel-soft panel-hover rounded-2xl border ${title.active ? "border-emerald-400/40 bg-emerald-400/10" : "border-white/10 bg-white/5"} p-4`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-semibold">{title.name}</p>
                          <p className="text-sm text-slate-300">{title.detail}</p>
                        </div>
                        {title.active && <span className="text-xs uppercase text-emerald-200">Active</span>}
                        {!title.active && title.earned && (
                          <button onClick={() => equipMutation.mutate(title.id)} className="rounded-lg border border-emerald-300/40 bg-emerald-300/10 px-3 py-2 text-xs font-semibold text-emerald-100 hover:bg-emerald-300/20">
                            Equip
                          </button>
                        )}
                        {!title.earned && <span className="text-xs text-slate-400">Locked</span>}
                      </div>
                      <p className="mt-2 text-xs text-slate-400">Minimum level: {title.min_level}</p>
                    </div>
                  ))}
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-slate-300">Active Buffs</p>
                  {buffsQuery.isLoading && <SkeletonCard />}
                  {buffs.length === 0 && !buffsQuery.isLoading && <p className="text-sm text-slate-400">No buffs active yet.</p>}
                  <div className="flex flex-wrap gap-2">
                    {buffs.map((buff) => (
                      <BuffChip key={buff.label} label={buff.label} detail={buff.detail} />
                    ))}
                  </div>
                </div>
              </div>
              </section>
            )}

            {(isDashboard || isQuestsView) && (
              <section className="panel rounded-3xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-white font-display">Quest Templates</h2>
                  <p className="text-sm text-slate-300">Turn repeatable wins into one-tap templates.</p>
                </div>
              </div>
              <div className="mt-4 space-y-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <input
                    value={templateForm.title}
                    onChange={(e) => setTemplateForm((prev) => ({ ...prev, title: e.target.value }))}
                    placeholder="Template title"
                    className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                  />
                  <select
                    value={templateForm.type}
                    onChange={(e) => setTemplateForm((prev) => ({ ...prev, type: e.target.value as QuestTemplate["type"] }))}
                    className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                  >
                    <option value="daily">Daily</option>
                    <option value="side">Side</option>
                    <option value="main">Main</option>
                  </select>
                  <input
                    value={templateForm.description}
                    onChange={(e) => setTemplateForm((prev) => ({ ...prev, description: e.target.value }))}
                    placeholder="Template description"
                    className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                  />
                  <input
                    type="number"
                    value={templateForm.xp_reward}
                    onChange={(e) => setTemplateForm((prev) => ({ ...prev, xp_reward: Number(e.target.value) }))}
                    className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                    placeholder="XP"
                  />
                </div>
                <button
                  onClick={() => templateMutation.mutate()}
                  className="rounded-xl bg-gradient-to-r from-emerald-400 to-sky-400 px-4 py-2 text-sm font-semibold text-ink shadow-glow"
                >
                  Save template
                </button>
                <div className="space-y-2">
                  {templatesQuery.isLoading && <SkeletonCard />}
                  {templates.length === 0 && !templatesQuery.isLoading && <p className="text-sm text-slate-400">No templates yet.</p>}
                  {templates.map((template) => (
                    <div key={template.id} className="flex flex-wrap items-center justify-between gap-3 panel-soft rounded-2xl px-4 py-3">
                      <div>
                        <p className="text-white font-semibold">{template.title}</p>
                        <p className="text-sm text-slate-300">{template.type} • {template.xp_reward} XP</p>
                      </div>
                      <button
                        onClick={() => useTemplateMutation.mutate(template.id)}
                        className="rounded-lg border border-emerald-300/40 bg-emerald-300/10 px-3 py-2 text-xs font-semibold text-emerald-100 hover:bg-emerald-300/20"
                      >
                        Use
                      </button>
                    </div>
                  ))}
                </div>
              </div>
              </section>
            )}

            {isProgressView && (
              <section className="panel rounded-3xl p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-white">Progress timeline</h2>
                    <p className="text-sm text-slate-300">XP trends, streak heatmap, and milestones.</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <div className="rounded-2xl border border-white/10 bg-white/10 px-3 py-2 text-xs text-slate-200">
                      7d XP: <span className="text-emerald-200">{xpWeekTotal}</span>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/10 px-3 py-2 text-xs text-slate-200">
                      Avg/day: <span className="text-emerald-200">{xpWeekAvg}</span>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/10 px-3 py-2 text-xs text-slate-200">
                      7d coins: <span className="text-amber-200">{coinWeekTotal}</span>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/10 px-3 py-2 text-xs text-slate-200">
                      Coins/day: <span className="text-amber-200">{coinWeekAvg}</span>
                    </div>
                  </div>
                </div>
                <div className="mt-5 grid gap-4 lg:grid-cols-[1.2fr_1fr]">
                  <div className="space-y-4">
                    <div className="panel-soft rounded-2xl p-4">
                      <p className="text-xs uppercase text-slate-400">XP trend (14 days)</p>
                      <div className="mt-3 h-32 w-full">
                        <svg viewBox="0 0 100 40" className="h-full w-full">
                          <defs>
                            <linearGradient id="xpFill" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="rgba(56,189,248,0.45)" />
                              <stop offset="100%" stopColor="rgba(56,189,248,0)" />
                            </linearGradient>
                          </defs>
                          {xpArea && <path d={xpArea} fill="url(#xpFill)" />}
                          {xpPath && <path d={xpPath} fill="none" stroke="#38bdf8" strokeWidth="1.5" />}
                        </svg>
                      </div>
                      <div className="mt-3 grid grid-cols-7 gap-1 text-[10px] text-slate-400">
                        {xpSeries.labels.slice(-7).map((label) => (
                          <span key={`lbl-${label}`}>{label}</span>
                        ))}
                      </div>
                    </div>
                    <div className="panel-soft rounded-2xl p-4">
                      <p className="text-xs uppercase text-slate-400">Coins earned (14 days)</p>
                      <div className="mt-3 h-32 w-full">
                        <svg viewBox="0 0 100 40" className="h-full w-full">
                          <defs>
                            <linearGradient id="coinFill" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="rgba(251,191,36,0.45)" />
                              <stop offset="100%" stopColor="rgba(251,191,36,0)" />
                            </linearGradient>
                          </defs>
                          {coinArea && <path d={coinArea} fill="url(#coinFill)" />}
                          {coinPath && <path d={coinPath} fill="none" stroke="#fbbf24" strokeWidth="1.5" />}
                        </svg>
                      </div>
                      <div className="mt-3 grid grid-cols-7 gap-1 text-[10px] text-slate-400">
                        {coinSeries.labels.slice(-7).map((label) => (
                          <span key={`coin-lbl-${label}`}>{label}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="panel-soft rounded-2xl p-4">
                    <p className="text-xs uppercase text-slate-400">Streak calendar (3 weeks)</p>
                    <div className="mt-3 grid grid-cols-7 gap-2">
                      {calendarCells.map((cell, idx) => {
                        if (!cell) {
                          return <div key={`pad-${idx}`} className="h-8 rounded-lg bg-white/5" />
                        }
                        const intensity = Math.min(1, cell.xp / Math.max(1, xpMax))
                        return (
                          <div
                            key={cell.key}
                            title={`${formatShort(cell.date)} • ${cell.xp} XP`}
                            className="h-8 rounded-lg border border-white/10"
                            style={{ backgroundColor: `rgba(56, 189, 248, ${0.1 + intensity * 0.6})` }}
                          />
                        )
                      })}
                    </div>
                  </div>
                </div>
                <div className="mt-4 panel-soft rounded-2xl p-4">
                  <p className="text-xs uppercase text-slate-400">Level milestones</p>
                  <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                    {[5, 10, 15, 20].map((lvl) => {
                      const required = Math.floor(100 * Math.pow(lvl, 1.5))
                      const reached = (me?.level ?? 1) >= lvl
                      return (
                        <div key={`lvl-${lvl}`} className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
                          <p className="text-xs text-slate-400">Level {lvl}</p>
                          <p className="text-sm text-white">{required} XP</p>
                          <p className={`text-xs ${reached ? "text-emerald-200" : "text-slate-400"}`}>{reached ? "Unlocked" : "In progress"}</p>
                        </div>
                      )
                    })}
                  </div>
                </div>
                <div className="mt-4 panel-soft rounded-2xl p-4">
                  <p className="text-xs uppercase text-slate-400">Coin history</p>
                  <div className="mt-3 space-y-2">
                    {coinHistory.length === 0 && <p className="text-sm text-slate-400">Complete quests to earn coins.</p>}
                    {coinHistory.map((entry) => (
                      <div key={entry.id} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
                        <div>
                          <p className="text-sm text-white">{entry.quest}</p>
                          <p className="text-xs text-slate-400">{formatShort(new Date(entry.date))} • {entry.xp} XP</p>
                        </div>
                        <span className="text-sm text-amber-200">+{entry.coins} coins</span>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            )}

            {isSettingsView && (
              <section className="panel rounded-3xl p-6">
                <h2 className="text-xl font-semibold text-white">Priority system</h2>
                <p className="text-sm text-slate-300">Tune how “Today” chooses your focus quest.</p>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <label className="text-sm text-slate-300">
                    Main quest weight
                    <input
                      type="number"
                      value={priorityWeights.main}
                      onChange={(e) => updateWeight("main", Number(e.target.value))}
                      className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                    />
                  </label>
                  <label className="text-sm text-slate-300">
                    Daily quest weight
                    <input
                      type="number"
                      value={priorityWeights.daily}
                      onChange={(e) => updateWeight("daily", Number(e.target.value))}
                      className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                    />
                  </label>
                  <label className="text-sm text-slate-300">
                    Side quest weight
                    <input
                      type="number"
                      value={priorityWeights.side}
                      onChange={(e) => updateWeight("side", Number(e.target.value))}
                      className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                    />
                  </label>
                  <label className="text-sm text-slate-300">
                    XP weight (per XP)
                    <input
                      type="number"
                      step="0.05"
                      value={priorityWeights.xpWeight}
                      onChange={(e) => updateWeight("xpWeight", Number(e.target.value))}
                      className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                    />
                  </label>
                  <label className="text-sm text-slate-300">
                    Overdue bonus
                    <input
                      type="number"
                      value={priorityWeights.dueOverdue}
                      onChange={(e) => updateWeight("dueOverdue", Number(e.target.value))}
                      className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                    />
                  </label>
                  <label className="text-sm text-slate-300">
                    Due soon bonus (&lt;6h)
                    <input
                      type="number"
                      value={priorityWeights.dueSoon}
                      onChange={(e) => updateWeight("dueSoon", Number(e.target.value))}
                      className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                    />
                  </label>
                  <label className="text-sm text-slate-300">
                    Due today bonus (&lt;24h)
                    <input
                      type="number"
                      value={priorityWeights.dueToday}
                      onChange={(e) => updateWeight("dueToday", Number(e.target.value))}
                      className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                    />
                  </label>
                  <label className="text-sm text-slate-300">
                    Due soonish bonus (&lt;3d)
                    <input
                      type="number"
                      value={priorityWeights.dueUpcoming}
                      onChange={(e) => updateWeight("dueUpcoming", Number(e.target.value))}
                      className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                    />
                  </label>
                  <label className="text-sm text-slate-300">
                    Completed today penalty
                    <input
                      type="number"
                      value={priorityWeights.completedPenalty}
                      onChange={(e) => updateWeight("completedPenalty", Number(e.target.value))}
                      className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                    />
                  </label>
                  <label className="text-sm text-slate-300">
                    New quest bonus
                    <input
                      type="number"
                      value={priorityWeights.newQuestBonus}
                      onChange={(e) => updateWeight("newQuestBonus", Number(e.target.value))}
                      className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                    />
                  </label>
                </div>
                <div className="mt-4 flex flex-wrap gap-3">
                  <button
                    onClick={resetWeights}
                    className="rounded-xl border border-white/10 bg-white/10 px-4 py-2 text-sm text-slate-100 hover:bg-white/20"
                  >
                    Reset defaults
                  </button>
                </div>
                <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Coins</p>
                      <h3 className="text-lg font-semibold text-white">Earning rate</h3>
                      <p className="text-xs text-slate-400">Coins are earned from quests. Minimum 1 coin per completion.</p>
                    </div>
                    <span className="rounded-full border border-amber-300/40 bg-amber-300/10 px-3 py-1 text-xs text-amber-100">
                      Current: 1 coin / {xpPerCoin} XP
                    </span>
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
                    <label className="text-sm text-slate-300">
                      XP per coin
                      <input
                        type="number"
                        min={10}
                        max={200}
                        value={coinRateForm}
                        onChange={(e) => setCoinRateForm(Number(e.target.value))}
                        className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                      />
                    </label>
                    <button
                      onClick={() => {
                        const normalized = Math.max(10, Math.min(200, Number(coinRateForm) || 50))
                        setCoinRateForm(normalized)
                        coinSettingsMutation.mutate({ xpPerCoin: normalized })
                      }}
                      className="rounded-xl border border-emerald-300/40 bg-emerald-300/10 px-4 py-2 text-sm text-emerald-100 hover:bg-emerald-300/20"
                    >
                      Save rate
                    </button>
                  </div>
                </div>
              </section>
            )}
            {(isJournalView || isShopView) && (
              <section className="panel rounded-3xl p-6">
                {isJournalView ? (
                  <>
                    <p className="text-xs uppercase tracking-[0.35em] text-slate-400">Journal</p>
                    <h2 className="text-2xl font-semibold text-white">Reflection space</h2>
                    <p className="text-sm text-slate-300">Capture daily wins and build self-awareness.</p>
                    <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
                      <div className="space-y-4">
                        <div className="panel-soft rounded-2xl p-4">
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <label className="text-sm text-slate-300">
                              Date
                              <input
                                type="date"
                                value={journalForm.date}
                                onChange={(e) => setJournalForm((prev) => ({ ...prev, date: e.target.value }))}
                                className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                              />
                            </label>
                            <div>
                              <p className="text-sm text-slate-300">Mood</p>
                              <div className="mt-1 flex gap-2">
                                {[1, 2, 3, 4, 5].map((value) => (
                                  <button
                                    key={`mood-${value}`}
                                    onClick={() => setJournalForm((prev) => ({ ...prev, mood: value }))}
                                    className={`h-8 w-8 rounded-full border text-sm font-semibold ${journalForm.mood === value ? "border-emerald-300 bg-emerald-300/20 text-emerald-100" : "border-white/10 bg-white/5 text-slate-300"}`}
                                  >
                                    {value}
                                  </button>
                                ))}
                              </div>
                            </div>
                          </div>
                          <div className="mt-4 grid gap-3 sm:grid-cols-2">
                            <label className="text-sm text-slate-300">
                              Win today
                              <input
                                value={journalForm.win}
                                onChange={(e) => setJournalForm((prev) => ({ ...prev, win: e.target.value }))}
                                placeholder="Biggest win"
                                className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                              />
                            </label>
                            <label className="text-sm text-slate-300">
                              Gratitude
                              <input
                                value={journalForm.gratitude}
                                onChange={(e) => setJournalForm((prev) => ({ ...prev, gratitude: e.target.value }))}
                                placeholder="What felt good"
                                className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                              />
                            </label>
                            <label className="text-sm text-slate-300 sm:col-span-2">
                              Challenge
                              <input
                                value={journalForm.challenge}
                                onChange={(e) => setJournalForm((prev) => ({ ...prev, challenge: e.target.value }))}
                                placeholder="What was tough"
                                className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                              />
                            </label>
                            <label className="text-sm text-slate-300 sm:col-span-2">
                              Notes
                              <textarea
                                value={journalForm.notes}
                                onChange={(e) => setJournalForm((prev) => ({ ...prev, notes: e.target.value }))}
                                placeholder="Quick reflection"
                                className="mt-1 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                              />
                            </label>
                          </div>
                          <div className="mt-4 flex flex-wrap gap-3">
                            <button onClick={saveJournalEntry} className="rounded-xl bg-gradient-to-r from-emerald-400 to-sky-400 px-4 py-2 text-sm font-semibold text-ink shadow-glow hover:scale-[1.02] transition">
                              Save reflection
                            </button>
                            <button onClick={clearJournalForm} className="rounded-xl border border-white/10 bg-white/10 px-4 py-2 text-sm text-slate-100 hover:bg-white/20">
                              Clear
                            </button>
                          </div>
                        </div>
                        <div className="grid gap-3 sm:grid-cols-2">
                          <div className="panel-soft rounded-2xl p-4">
                            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Entries</p>
                            <p className="text-2xl font-semibold text-white">{journalEntries.length}</p>
                          </div>
                          <div className="panel-soft rounded-2xl p-4">
                            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Reflection streak</p>
                            <p className="text-2xl font-semibold text-white">{journalStreak} day</p>
                          </div>
                          <div className="panel-soft rounded-2xl p-4 sm:col-span-2">
                            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Latest summary</p>
                            <p className="text-sm text-slate-200">{journalSummary || "No reflection yet."}</p>
                          </div>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <p className="text-sm text-slate-300">Recent entries</p>
                        {journalEntries.length === 0 && <p className="text-sm text-slate-400">No entries yet. Start your first reflection.</p>}
                        {journalEntries.map((entry) => (
                          <div key={entry.id} className="panel-soft rounded-2xl p-4 space-y-2">
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <p className="text-sm text-slate-300">{formatShort(new Date(`${entry.date}T00:00:00`))}</p>
                                <p className="text-lg font-semibold text-white">Mood {entry.mood}/5</p>
                              </div>
                              <button onClick={() => deleteJournalEntry(entry.id)} className="text-xs text-rose-200 hover:text-rose-100">
                                Remove
                              </button>
                            </div>
                            <p className="text-sm text-slate-200">{buildJournalSummary(entry) || "No notes attached."}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <p className="text-xs uppercase tracking-[0.35em] text-slate-400">Upgrades</p>
                        <h2 className="text-2xl font-semibold text-white">Upgrade store</h2>
                        <p className="text-sm text-slate-300">Spend coins on buffs, themes, and perks that shape your system.</p>
                        <p className="text-xs text-slate-400">Coins are earned from quests (about 1 coin per 50 XP, minimum 1).</p>
                      </div>
                      <div className="panel-soft rounded-2xl px-4 py-3">
                        <p className="text-xs text-slate-400">Available coins</p>
                        <p className="text-2xl font-semibold text-white">{availableCoins}</p>
                        <p className="text-xs text-slate-400">Lifetime spent {shopState.spent} coins</p>
                      </div>
                    </div>
                    <div className="mt-6 grid gap-6 lg:grid-cols-3">
                      {SHOP_CATEGORIES.map((category) => (
                        <div key={category.key} className="panel-soft rounded-2xl p-4">
                          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">{category.label}</p>
                          <p className="text-sm text-slate-300">{category.subtitle}</p>
                          <div className="mt-4 space-y-3">
                            {SHOP_ITEMS.filter((item) => item.category === category.key).map((item) => {
                              const owned = ownedUpgrades.has(item.id)
                              const missingCoins = Math.max(0, item.costCoins - availableCoins)
                              return (
                                <div key={item.id} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                                  <div className="flex items-start justify-between gap-3">
                                    <div>
                                      <p className="text-base font-semibold text-white">{item.name}</p>
                                      <p className="text-xs text-slate-300">{item.description}</p>
                                    </div>
                                    <span className="rounded-full border border-emerald-300/40 bg-emerald-300/10 px-2 py-1 text-xs text-emerald-100">
                                      {item.costCoins} coins
                                    </span>
                                  </div>
                                  <p className="mt-2 text-xs text-slate-300">{item.effect}</p>
                                  <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                                    {owned ? (
                                      <span className="text-xs text-emerald-200">Owned</span>
                                    ) : (
                                      <button
                                        onClick={() => purchaseUpgrade(item)}
                                        className="rounded-lg border border-sky-300/40 bg-sky-300/10 px-3 py-2 text-xs font-semibold text-sky-100 hover:bg-sky-300/20"
                                      >
                                        Unlock
                                      </button>
                                    )}
                                    {!owned && missingCoins > 0 && <span className="text-xs text-rose-200">Need {missingCoins} coins</span>}
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </section>
            )}
          </div>

          {showSidebar && (
            <div className="space-y-6">
            {(isDashboard || isProgressView) && (
              <section className="panel rounded-3xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-white font-display">Weekly Boss</h2>
                  <p className="text-sm text-slate-300">Every quest deals damage. Defeat it to reset next week.</p>
                </div>
              </div>
              <div className="mt-4 space-y-3">
                {bossQuery.isLoading && <SkeletonCard />}
                {boss && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-lg font-semibold text-white">{boss.name}</p>
                        <p className="text-xs text-slate-400">Week of {boss.week_start}</p>
                      </div>
                      <p className="text-sm text-slate-300">{boss.hp_current}/{boss.hp_total} HP</p>
                    </div>
                    <ProgressBar value={boss.hp_total - boss.hp_current} max={boss.hp_total} />
                  </div>
                )}
              </div>
              </section>
            )}

            {(isDashboard || isProgressView) && (
              <section className="panel rounded-3xl p-6">
              <div>
                <h2 className="text-xl font-semibold text-white font-display">Weekly Recap</h2>
                <p className="text-sm text-slate-300">Your streak momentum for the current week.</p>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {recapQuery.isLoading && <SkeletonCard />}
                {recap && (
                  <>
                    <div className="panel-soft rounded-2xl p-4">
                      <p className="text-sm text-slate-300">Total XP</p>
                      <p className="text-2xl font-semibold text-white">{recap.total_xp}</p>
                    </div>
                    <div className="panel-soft rounded-2xl p-4">
                      <p className="text-sm text-slate-300">Quests completed</p>
                      <p className="text-2xl font-semibold text-white">{recap.quests_completed}</p>
                    </div>
                    <div className="panel-soft rounded-2xl p-4">
                      <p className="text-sm text-slate-300">Top quest type</p>
                      <p className="text-2xl font-semibold text-white">{recap.top_type || "-"}</p>
                    </div>
                    <div className="panel-soft rounded-2xl p-4">
                      <p className="text-sm text-slate-300">Current streak</p>
                      <p className="text-2xl font-semibold text-white">{recap.current_streak} days</p>
                    </div>
                  </>
                )}
              </div>
              </section>
            )}

            {(isDashboard || isBuffsView) && (
              <section className="panel rounded-3xl p-6">
              <div>
                <h2 className="text-xl font-semibold text-white font-display">Loot Drops</h2>
                <p className="text-sm text-slate-300">Random rewards drop on quest completion.</p>
              </div>
              <div className="mt-4 space-y-2">
                {rewardsQuery.isLoading && <SkeletonCard />}
                {rewards.length === 0 && !rewardsQuery.isLoading && <p className="text-sm text-slate-400">No rewards yet.</p>}
                {rewards.map((reward) => (
                  <div key={reward.id} className="flex items-center justify-between panel-soft rounded-2xl px-4 py-3">
                    <div>
                      <p className="text-white font-semibold">{reward.label}</p>
                      <p className="text-xs text-slate-400">{reward.detail}</p>
                    </div>
                    <span className="rounded-full border border-amber-300/40 bg-amber-300/10 px-3 py-1 text-xs uppercase text-amber-200">{reward.rarity}</span>
                  </div>
                ))}
              </div>
              </section>
            )}

            {(isDashboard || isStatsView) && (
              <section className="panel rounded-3xl p-6">
              <div>
                <h2 className="text-xl font-semibold text-white font-display">Skill Tree</h2>
                <p className="text-sm text-slate-300">Spend XP on permanent upgrades.</p>
              </div>
              <div className="mt-4 space-y-2">
                {skillsQuery.isLoading && <SkeletonCard />}
                {skills.map((skill) => (
                  <div key={skill.id} className="flex flex-wrap items-center justify-between gap-3 panel-soft rounded-2xl px-4 py-3">
                    <div>
                      <p className="text-white font-semibold">{skill.name}</p>
                      <p className="text-xs text-slate-400">{skill.detail}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-300">{skill.cost_xp} XP</span>
                      {skill.unlocked ? (
                        <span className="rounded-full border border-emerald-300/40 bg-emerald-300/10 px-3 py-1 text-xs uppercase text-emerald-200">Unlocked</span>
                      ) : (
                        <button onClick={() => unlockMutation.mutate(skill.id)} className="rounded-lg border border-sky-300/40 bg-sky-300/10 px-3 py-2 text-xs font-semibold text-sky-100 hover:bg-sky-300/20">
                          Unlock
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              </section>
            )}

            {isDashboard && (
              <section className="panel rounded-3xl p-6">
              <div>
                <h2 className="text-xl font-semibold text-white font-display">Party</h2>
                <p className="text-sm text-slate-300">Invite friends and keep each other accountable.</p>
              </div>
              <div className="mt-4 space-y-3">
                {partyQuery.isLoading && <SkeletonCard />}
                {party ? (
                  <div className="panel-soft rounded-2xl p-4 space-y-3">
                    <div>
                      <p className="text-white font-semibold">{party.name}</p>
                      <p className="text-sm text-slate-300">Code: {party.code}</p>
                      <p className="text-sm text-slate-300">Members: {party.members}</p>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Leaderboard</p>
                      <div className="mt-2 space-y-2">
                        {partyLeaderboardQuery.isLoading && <p className="text-xs text-slate-400">Loading leaderboard…</p>}
                        {!partyLeaderboardQuery.isLoading && partyLeaderboard.length === 0 && (
                          <p className="text-xs text-slate-400">No members yet.</p>
                        )}
                        {partyLeaderboard.map((member, idx) => (
                          <div key={member.id} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2">
                            <div>
                              <p className="text-sm text-white">#{idx + 1} {member.display_name}</p>
                              <p className="text-xs text-slate-400">{member.streak_days} day streak</p>
                            </div>
                            <div className="text-right">
                              <p className="text-sm text-amber-200">{member.coins} coins</p>
                              <p className="text-xs text-slate-400">{member.xp_total} XP</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    <button onClick={() => leavePartyMutation.mutate()} className="rounded-lg border border-rose-300/40 bg-rose-300/10 px-3 py-2 text-sm text-rose-100 hover:bg-rose-300/20">
                      Leave party
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex flex-col gap-2">
                      <input
                        value={partyName}
                        onChange={(e) => setPartyName(e.target.value)}
                        placeholder="Party name"
                        className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                      />
                      <button onClick={() => createPartyMutation.mutate()} className="rounded-xl border border-emerald-300/40 bg-emerald-300/10 px-3 py-2 text-sm text-emerald-100 hover:bg-emerald-300/20">
                        Create party
                      </button>
                    </div>
                    <div className="flex flex-col gap-2">
                      <input
                        value={partyCode}
                        onChange={(e) => setPartyCode(e.target.value)}
                        placeholder="Party code"
                        className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                      />
                      <button onClick={() => joinPartyMutation.mutate()} className="rounded-xl border border-sky-300/40 bg-sky-300/10 px-3 py-2 text-sm text-sky-100 hover:bg-sky-300/20">
                        Join party
                      </button>
                    </div>
                  </div>
                )}
              </div>
              </section>
            )}

            {(isDashboard || isSettingsView) && (
              <section className="panel rounded-3xl p-6">
              <div>
                <h2 className="text-xl font-semibold text-white font-display">Accountability Contract</h2>
                <p className="text-sm text-slate-300">Stake a promise and a reward to keep the streak alive.</p>
              </div>
              <div className="mt-4 space-y-3">
                <input
                  value={contractForm.pledge}
                  onChange={(e) => setContractForm((prev) => ({ ...prev, pledge: e.target.value }))}
                  placeholder="Pledge"
                  className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                />
                <input
                  value={contractForm.reward}
                  onChange={(e) => setContractForm((prev) => ({ ...prev, reward: e.target.value }))}
                  placeholder="Reward"
                  className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                />
                <div className="flex items-center justify-between gap-3">
                  <label className="flex items-center gap-2 text-sm text-slate-300">
                    Target streak
                    <input
                      type="number"
                      min={1}
                      value={contractForm.target_streak}
                      onChange={(e) => setContractForm((prev) => ({ ...prev, target_streak: Number(e.target.value) }))}
                      className="w-24 rounded-lg border border-white/10 bg-white/10 px-2 py-1 text-white outline-none focus:border-sky-400"
                    />
                  </label>
                  <label className="flex items-center gap-2 text-sm text-slate-300">
                    <input
                      type="checkbox"
                      checked={contractForm.active}
                      onChange={(e) => setContractForm((prev) => ({ ...prev, active: e.target.checked }))}
                    />
                    Active
                  </label>
                </div>
                <button onClick={() => contractMutation.mutate()} className="rounded-xl border border-emerald-300/40 bg-emerald-300/10 px-3 py-2 text-sm text-emerald-100 hover:bg-emerald-300/20">
                  Save contract
                </button>
                {contract && <p className="text-xs text-slate-400">Last saved contract targets {contract.target_streak} days.</p>}
              </div>
              </section>
            )}

            {(isDashboard || isSettingsView) && (
              <section className="panel rounded-3xl p-6">
              <div>
                <h2 className="text-xl font-semibold text-white font-display">Smart Reminders</h2>
                <p className="text-sm text-slate-300">Set your focus time and enable push nudges.</p>
              </div>
              <div className="mt-4 space-y-3">
                <div className="flex flex-wrap items-center gap-3">
                  <input
                    type="time"
                    value={reminderForm.time}
                    onChange={(e) => setReminderForm((prev) => ({ ...prev, time: e.target.value }))}
                    className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                  />
                  <select
                    value={reminderForm.timezone}
                    onChange={(e) => setReminderForm((prev) => ({ ...prev, timezone: e.target.value }))}
                    className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-white outline-none focus:border-sky-400"
                  >
                    <option value="local">Local timezone</option>
                    <option value="UTC">UTC</option>
                  </select>
                  <label className="flex items-center gap-2 text-sm text-slate-300">
                    <input
                      type="checkbox"
                      checked={reminderForm.enabled}
                      onChange={(e) => setReminderForm((prev) => ({ ...prev, enabled: e.target.checked }))}
                    />
                    Enabled
                  </label>
                </div>
                <div className="flex flex-wrap gap-3">
                  <button onClick={() => reminderMutation.mutate()} className="rounded-xl border border-emerald-300/40 bg-emerald-300/10 px-3 py-2 text-sm text-emerald-100 hover:bg-emerald-300/20">
                    Save reminder
                  </button>
                  <button onClick={() => pushMutation.mutate()} className="rounded-xl border border-sky-300/40 bg-sky-300/10 px-3 py-2 text-sm text-sky-100 hover:bg-sky-300/20">
                    Enable push
                  </button>
                </div>
                {reminders && <p className="text-xs text-slate-400">Saved reminder: {reminders.time} ({reminders.timezone}).</p>}
              </div>
              </section>
            )}
          </div>
          )}
        </div>
      </div>
    </div>

      {toast && (
        <div className="fixed bottom-6 right-6 rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm text-white shadow-glow">
          <p className={toast.type === "error" ? "text-rose-200" : "text-emerald-200"}>{toast.message}</p>
        </div>
      )}
      {navOverlayOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 px-6 py-10">
          <div className="panel w-full max-w-3xl rounded-3xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-slate-400">Navigation</p>
                <h2 className="text-2xl font-semibold text-white">Explore myLife</h2>
              </div>
              <button
                onClick={() => setNavOverlayOpen(false)}
                className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-slate-100 hover:bg-white/20"
              >
                Close
              </button>
            </div>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              {quickNav.map((item) => (
                <button
                  key={`modal-${item.view}`}
                  onClick={() => {
                    navigate(item.path)
                    setNavOverlayOpen(false)
                  }}
                  className="panel-soft panel-hover flex items-center gap-3 rounded-2xl px-4 py-3 text-left"
                >
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/10 text-sm font-semibold text-white">
                    {item.icon}
                  </span>
                  <div>
                    <p className="text-base font-semibold text-white">{item.title}</p>
                    <p className="text-xs text-slate-300">{item.subtitle}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}









