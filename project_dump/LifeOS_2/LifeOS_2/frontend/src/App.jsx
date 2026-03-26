import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  acceptSpaceInvite,
  addSpaceMember,
  applySpaceNotificationDefaultToMembers,
  clearAuthToken,
  claimChallengeReward,
  claimSeasonPassTier,
  confirmPasswordRecovery,
  completeHabit,
  completeSpaceTask,
  completeTask,
  createSpaceInvite,
  createSpace,
  createSpaceTask,
  createRecurringRule,
  createGoal,
  createHabit,
  createTask,
  deleteSpace,
  deleteSpaceTask,
  deleteRecurringRule,
  deleteGoal,
  deleteHabit,
  deleteTask,
  exportSpaceSnapshot,
  fetchAchievements,
  fetchChallenges,
  fetchDashboard,
  fetchGoals,
  fetchHabits,
  fetchLeaderboard,
  fetchMe,
  fetchNotifications,
  fetchSeasonPass,
  fetchShop,
  fetchTimeline,
  fetchInventory,
  fetchRecurringRules,
  fetchAvatar,
  fetchSpaceAuditEvents,
  fetchSpaceDetail,
  fetchSpaces,
  fetchStats,
  fetchTasks,
  fetchXpRules,
  importAccountSnapshot,
  importSpaceSnapshot,
  previewSpaceSnapshotImport,
  loginUser,
  logoutUser,
  purchaseShopItem,
  redeemInventoryPurchase,
  exportAccountSnapshot,
  fetchReminderChannels,
  fetchReminderDeliveries,
  requestPasswordRecovery,
  registerUser,
  runReminderChannelDelivery,
  sendReminderChannelTest,
  updateAccountPassword,
  updateAccountProfile,
  updateReminderChannels,
  updateRecurringRule,
  updateAvatar,
  updateSpaceNotificationQuietHours,
  updateSpaceNotificationPreference,
  updateSpaceNotificationDefault,
  updateSpaceRoleTemplate,
  updateSpace,
  updateSpaceTask,
  updateSpaceMemberRole,
  updateGoal,
  updateHabit,
  updateTask,
  removeSpaceMember,
  revokeSpaceInvite,
  runRecurringRules
} from "./api";

const ICONS = {
  brand: "\u{1F537}",
  dashboard: "\u{1F4CA}",
  tasks: "\u{2705}",
  quests: "\u{1F9ED}",
  shop: "\u{1FA99}",
  inventory: "\u{1F4E6}",
  achievements: "\u{1F3C5}",
  challenges: "\u{1F3AF}",
  timeline: "\u{1F4DC}",
  leaderboard: "\u{1F3C6}",
  seasonPass: "\u{1F39F}\u{FE0F}",
  avatar: "\u{1F9D1}",
  spaces: "\u{1F465}",
  stats: "\u{1F4C8}",
  settings: "\u{2699}\u{FE0F}",
  level: "\u{2B50}",
  coins: "\u{1FA99}",
  trophy: "\u{1F3C6}",
  spark: "\u{26A1}",
  streak: "\u{1F7E2}",
  fire: "\u{1F525}",
  bell: "\u{1F514}",
  compass: "\u{1F9ED}",
  menu: "\u{2630}",
  close: "\u{2715}"
};

const NAV_ITEMS = [
  { key: "dashboard", path: "/dashboard", icon: ICONS.dashboard, label: "Dashboard" },
  { key: "tasks", path: "/tasks", icon: ICONS.tasks, label: "Tasks" },
  { key: "quests", path: "/quests", icon: ICONS.quests, label: "Quests" },
  { key: "shop", path: "/shop", icon: ICONS.shop, label: "Shop" },
  { key: "inventory", path: "/inventory", icon: ICONS.inventory, label: "Inventory" },
  { key: "achievements", path: "/achievements", icon: ICONS.achievements, label: "Achievements" },
  { key: "challenges", path: "/challenges", icon: ICONS.challenges, label: "Challenges" },
  { key: "timeline", path: "/timeline", icon: ICONS.timeline, label: "Timeline" },
  { key: "leaderboard", path: "/leaderboard", icon: ICONS.leaderboard, label: "Leaderboard" },
  { key: "season_pass", path: "/season-pass", icon: ICONS.seasonPass, label: "Season Pass" },
  { key: "avatar", path: "/avatar", icon: ICONS.avatar, label: "Avatar" },
  { key: "spaces", path: "/spaces", icon: ICONS.spaces, label: "Spaces" },
  { key: "stats", path: "/stats", icon: ICONS.stats, label: "Stats" },
  { key: "settings", path: "/settings", icon: ICONS.settings, label: "Settings" }
];

const VIEW_BY_PATH = {
  "/": "dashboard",
  "/dashboard": "dashboard",
  "/tasks": "tasks",
  "/quests": "quests",
  "/shop": "shop",
  "/inventory": "inventory",
  "/achievements": "achievements",
  "/challenges": "challenges",
  "/timeline": "timeline",
  "/leaderboard": "leaderboard",
  "/season-pass": "season_pass",
  "/avatar": "avatar",
  "/spaces": "spaces",
  "/stats": "stats",
  "/settings": "settings"
};

const TASK_TYPE_ICON = {
  task: "\u{2705}",
  habit: "\u{1F552}",
  quest: "\u{1F6E0}\u{FE0F}"
};
const DASHBOARD_QUICK_TASK_XP_PRESETS = Object.freeze({
  task: "20",
  habit: "15",
  quest: "100"
});

const STATS_RANGE_OPTIONS = [14, 30, 60];
const TIMELINE_RANGE_OPTIONS = [14, 30, 60, 90];
const LEADERBOARD_LIMIT_OPTIONS = [10, 15, 25, 40];
const LEADERBOARD_SCOPE_OPTIONS = [
  { key: "global", label: "Global" },
  { key: "network", label: "Network" }
];
const TASK_FILTER_STATUS_OPTIONS = [
  { key: "all", label: "All status" },
  { key: "todo", label: "Todo" },
  { key: "done", label: "Done" }
];
const TASK_FILTER_TYPE_OPTIONS = [
  { key: "all", label: "All types" },
  { key: "task", label: "Task" },
  { key: "habit", label: "Habit" },
  { key: "quest", label: "Quest" }
];
const TASK_FILTER_PRIORITY_OPTIONS = [
  { key: "all", label: "All priorities" },
  { key: "high", label: "High" },
  { key: "medium", label: "Medium" },
  { key: "low", label: "Low" }
];
const TASK_SORT_OPTIONS = [
  { key: "due_asc", label: "Due date (soonest)" },
  { key: "due_desc", label: "Due date (latest)" },
  { key: "priority_desc", label: "Priority (high-low)" },
  { key: "xp_desc", label: "XP reward (high-low)" },
  { key: "created_desc", label: "Created (newest)" },
  { key: "title_asc", label: "Title (A-Z)" }
];
const HABIT_FILTER_STREAK_OPTIONS = [
  { key: "all", label: "All streaks" },
  { key: "hot", label: "Hot streak (7+)" },
  { key: "active", label: "Active streak (1+)" },
  { key: "idle", label: "Idle (0)" }
];
const HABIT_SORT_OPTIONS = [
  { key: "created_desc", label: "Created (newest)" },
  { key: "streak_desc", label: "Current streak (high-low)" },
  { key: "longest_desc", label: "Longest streak (high-low)" },
  { key: "last_completed_desc", label: "Last completed (recent)" },
  { key: "name_asc", label: "Name (A-Z)" }
];
const GOAL_FILTER_STATUS_OPTIONS = [
  { key: "all", label: "All status" },
  { key: "in_progress", label: "In progress" },
  { key: "completed", label: "Completed" },
  { key: "overdue", label: "Overdue" },
  { key: "no_deadline", label: "No deadline" }
];
const GOAL_SORT_OPTIONS = [
  { key: "created_desc", label: "Created (newest)" },
  { key: "progress_desc", label: "Progress (high-low)" },
  { key: "deadline_asc", label: "Deadline (soonest)" },
  { key: "title_asc", label: "Title (A-Z)" }
];
const SHOP_CATEGORY_FILTER_OPTIONS = [
  { key: "all", label: "All categories" },
  { key: "avatar", label: "Avatar only" },
  { key: "self_reward", label: "Self rewards" },
  { key: "season_pass", label: "Season pass" }
];
const SHOP_OWNERSHIP_FILTER_OPTIONS = [
  { key: "all", label: "All ownership" },
  { key: "unowned", label: "Not owned" },
  { key: "owned", label: "Owned" }
];
const SHOP_AVATAR_VIEW_OPTIONS = [
  { key: "all", label: "All avatar items" },
  { key: "set_bundles", label: "Set bundles" },
  { key: "set_parts", label: "Set parts" },
  { key: "single_unlocks", label: "Single unlocks" }
];
const AVATAR_SLOT_ORDER = ["style", "body_type", "top", "bottom", "accessory", "palette"];
const AVATAR_SLOT_LABELS = Object.freeze({
  style: "Head Type",
  body_type: "Body Type",
  top: "Top Wear",
  bottom: "Bottom Wear",
  accessory: "Accessory",
  palette: "Color Palette"
});
const AVATAR_SET_FILTER_OPTIONS = [
  { key: "all", label: "All sets" },
  { key: "locked", label: "Locked only" },
  { key: "unlocked", label: "Unlocked only" },
  { key: "active", label: "Equipped set" },
  { key: "previewing", label: "Previewing now" },
  { key: "affordable", label: "Affordable now" }
];
const AVATAR_SET_SORT_OPTIONS = [
  { key: "completion_desc", label: "Most complete first" },
  { key: "completion_asc", label: "Least complete first" },
  { key: "bundle_price_asc", label: "Cheapest bundle first" },
  { key: "savings_desc", label: "Best bundle savings first" },
  { key: "label_asc", label: "Name (A-Z)" }
];
const SPACE_NOTIFICATION_MODE_OPTIONS = [
  {
    value: "all",
    label: "All updates",
    description: "Show shared queue updates in reminders and digests."
  },
  {
    value: "priority_only",
    label: "Priority only",
    description: "Only high-signal shared queue updates appear in reminders and digests."
  },
  {
    value: "digest_only",
    label: "Digest only",
    description: "Hide shared queue updates in reminders, but keep them in digests."
  },
  {
    value: "muted",
    label: "Muted",
    description: "Hide shared queue updates in reminders and digests."
  }
];
const DEFAULT_SPACE_QUIET_HOURS = Object.freeze({
  enabled: false,
  start_hour_utc: 22,
  end_hour_utc: 7,
  window_label: "22:00-07:00 UTC",
  is_active_now: false
});
const SPACE_QUIET_HOUR_OPTIONS = Array.from({ length: 24 }, (_value, hour) => ({
  value: hour,
  label: `${String(hour).padStart(2, "0")}:00 UTC`
}));

const SPACE_SNAPSHOT_IMPORT_LABELS = {
  members: "Members",
  tasks: "Shared Tasks",
  role_templates: "Role Templates",
  notification_preferences: "Notification Preferences"
};
const SPACE_IMPORT_REPLACE_CONFIRM_PREFIX = "REPLACE SPACE";
const SPACE_AUDIT_FETCH_LIMIT = 80;
const SPACE_AUDIT_FILTER_DEFAULT = Object.freeze({
  event_type: "all",
  days: "30",
  query: ""
});
const SPACE_AUDIT_LOOKBACK_OPTIONS = [
  { value: "", label: "All time" },
  { value: "7", label: "Last 7 days" },
  { value: "30", label: "Last 30 days" },
  { value: "90", label: "Last 90 days" }
];

const TASK_TYPE_THEME = {
  task: "var(--accent)",
  habit: "var(--accent-2)",
  quest: "#f2b66a"
};

const WEEKDAY_OPTIONS = [
  { value: 0, label: "Mon" },
  { value: 1, label: "Tue" },
  { value: 2, label: "Wed" },
  { value: 3, label: "Thu" },
  { value: 4, label: "Fri" },
  { value: 5, label: "Sat" },
  { value: 6, label: "Sun" }
];

function formatXpRuleKey(ruleKey) {
  return ruleKey.split(".").join(" / ");
}

function prettyNumber(value) {
  return Number(value || 0).toLocaleString();
}

function formatSignedNumber(value) {
  const numeric = Number(value || 0);
  if (numeric > 0) {
    return `+${prettyNumber(numeric)}`;
  }
  return prettyNumber(numeric);
}

function formatRewardNotice(xpValue, coinValue, fallbackMessage) {
  const xp = Number(xpValue || 0);
  const coins = Number(coinValue || 0);
  const parts = [];
  if (xp > 0) {
    parts.push(`+${prettyNumber(xp)} XP`);
  }
  if (coins > 0) {
    parts.push(`+${prettyNumber(coins)} coins`);
  }
  if (parts.length === 0) {
    return fallbackMessage;
  }
  if (parts.length === 1) {
    return `${parts[0]} earned.`;
  }
  return `${parts[0]} and ${parts[1]} earned.`;
}

function formatPercent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return "0%";
  }
  const precision = Number.isInteger(numeric) ? 0 : 1;
  return `${numeric.toFixed(precision)}%`;
}

function formatSeasonPassTrackReward(trackRow, fallbackLabel = "Reward") {
  const row = trackRow && typeof trackRow === "object" ? trackRow : {};
  const description = String(row.reward_description || "").trim();
  if (description) {
    return description;
  }
  const coins = Math.max(Number(row.reward_coins || 0), 0);
  const xp = Math.max(Number(row.reward_xp || 0), 0);
  if (coins > 0 && xp > 0) {
    return `+${prettyNumber(coins)} coins and +${prettyNumber(xp)} XP`;
  }
  if (coins > 0) {
    return `+${prettyNumber(coins)} coins`;
  }
  if (xp > 0) {
    return `+${prettyNumber(xp)} XP`;
  }
  return fallbackLabel;
}

function formatCountdownLabel(rawSeconds) {
  const totalSeconds = Math.max(Number(rawSeconds) || 0, 0);
  if (totalSeconds <= 0) {
    return "under 1m";
  }
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  if (hours <= 0) {
    return `${minutes}m`;
  }
  if (minutes <= 0) {
    return `${hours}h`;
  }
  return `${hours}h ${minutes}m`;
}

function formatDateTime(value) {
  const raw = String(value || "").trim();
  if (!raw) {
    return "-";
  }
  const parsed = new Date(raw);
  if (!Number.isFinite(parsed.getTime())) {
    return raw;
  }
  return parsed.toLocaleString();
}

function getDayStartTimestamp(rawDate = new Date()) {
  const parsed = rawDate instanceof Date ? rawDate : new Date(rawDate);
  if (!Number.isFinite(parsed.getTime())) {
    return Number.NaN;
  }
  return new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate()).getTime();
}

function parseDateOnlyStart(rawValue) {
  const raw = String(rawValue || "").trim();
  if (!raw) {
    return Number.NaN;
  }
  const parsed = Date.parse(`${raw}T00:00:00`);
  return Number.isFinite(parsed) ? parsed : Number.NaN;
}

function formatDateInputValue(rawDate = new Date()) {
  const parsed = rawDate instanceof Date ? rawDate : new Date(rawDate);
  if (!Number.isFinite(parsed.getTime())) {
    return "";
  }
  const year = String(parsed.getFullYear());
  const month = String(parsed.getMonth() + 1).padStart(2, "0");
  const day = String(parsed.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDateLabel(rawValue) {
  const raw = String(rawValue || "").trim();
  if (!raw) {
    return "";
  }
  const parsed = new Date(`${raw}T00:00:00`);
  if (!Number.isFinite(parsed.getTime())) {
    return raw;
  }
  return parsed.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric"
  });
}

function normalizeQuietHour(value, fallback = 0) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return fallback;
  }
  const rounded = Math.trunc(numeric);
  if (rounded < 0 || rounded > 23) {
    return fallback;
  }
  return rounded;
}

function createInviteRoleBreakdownDefault() {
  return {
    member: {
      created: 0,
      accepted: 0,
      revoked: 0,
      expired: 0,
      active: 0,
      accepted_events: 0,
      revoked_events: 0,
      conversion_rate_percent: 0
    },
    admin: {
      created: 0,
      accepted: 0,
      revoked: 0,
      expired: 0,
      active: 0,
      accepted_events: 0,
      revoked_events: 0,
      conversion_rate_percent: 0
    },
    other: {
      created: 0,
      accepted: 0,
      revoked: 0,
      expired: 0,
      active: 0,
      accepted_events: 0,
      revoked_events: 0,
      conversion_rate_percent: 0
    }
  };
}

function humanizeKey(value) {
  return String(value || "")
    .replace(/^can_/, "")
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatPreviewItemSummary(item) {
  if (!item || typeof item !== "object") {
    return "";
  }
  const entries = Object.entries(item)
    .filter(([, value]) => value !== null && value !== undefined && value !== "")
    .slice(0, 3)
    .map(([key, value]) => `${humanizeKey(key)}: ${String(value)}`);
  return entries.join(" | ");
}

function buildSpaceReplaceConfirmationPhrase(spaceId) {
  const safeSpaceId = Number(spaceId);
  if (!Number.isInteger(safeSpaceId) || safeSpaceId <= 0) {
    return "";
  }
  return `${SPACE_IMPORT_REPLACE_CONFIRM_PREFIX} ${safeSpaceId}`;
}

function normalizeSpaceAuditSummary(summary, fallbackTotal = 0) {
  const safeFallbackTotal = Number.isFinite(Number(fallbackTotal)) ? Math.max(Number(fallbackTotal), 0) : 0;
  if (!summary || typeof summary !== "object") {
    return { total: safeFallbackTotal, by_type: {} };
  }

  const rawByType = summary.by_type && typeof summary.by_type === "object" ? summary.by_type : {};
  const byType = Object.fromEntries(
    Object.entries(rawByType)
      .map(([key, value]) => [String(key || "").trim().toLowerCase(), Math.max(Number(value || 0), 0)])
      .filter(([key]) => key)
  );
  const total = Number.isFinite(Number(summary.total)) ? Math.max(Number(summary.total), 0) : safeFallbackTotal;
  return { total, by_type: byType };
}

function normalizeSpaceAuditEventTypes(eventTypes, summary) {
  const fromApi = Array.isArray(eventTypes)
    ? eventTypes.map((value) => String(value || "").trim().toLowerCase()).filter(Boolean)
    : [];
  const fromSummary = Object.keys(summary?.by_type || {}).map((value) => String(value || "").trim().toLowerCase());
  return Array.from(new Set([...fromApi, ...fromSummary])).filter(Boolean).sort((left, right) => left.localeCompare(right));
}

function GoalItem({ goal }) {
  const width = Math.max(0, Math.min(goal.progress, 100));
  return (
    <li className="goal-item">
      <div className="goal-top-row">
        <span>{goal.title}</span>
        <span>{goal.progress}%</span>
      </div>
      <div className="goal-track">
        <span className="goal-fill" style={{ width: `${width}%` }} />
      </div>
      <small>
        {goal.current_value}/{goal.target_value} complete
      </small>
    </li>
  );
}

function DailyXpChart({ rows }) {
  if (!rows.length) {
    return <p className="chart-empty">No XP data yet.</p>;
  }

  const maxXp = Math.max(...rows.map((row) => row.xp), 1);

  return (
    <div className="chart-bars-scroll">
      <div className="chart-bars">
        {rows.map((row) => {
          const barHeight = Math.max((row.xp / maxXp) * 100, row.xp > 0 ? 8 : 2);
          return (
            <div key={row.date} className="chart-bar-column" title={`${row.label}: ${row.xp} XP`}>
              <span className="chart-bar daily-xp-bar" style={{ height: `${barHeight}%` }} />
              <small>{row.label.slice(0, 3)}</small>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function DailyCompletionChart({ rows }) {
  if (!rows.length) {
    return <p className="chart-empty">No completion data yet.</p>;
  }

  const maxCompletions = Math.max(...rows.map((row) => row.total_completions), 1);

  return (
    <div className="chart-bars-scroll">
      <div className="chart-bars">
        {rows.map((row) => {
          const columnHeight = Math.max((row.total_completions / maxCompletions) * 100, row.total_completions > 0 ? 8 : 2);
          const taskPercent = row.total_completions > 0 ? (row.task_completions / row.total_completions) * 100 : 0;
          const habitPercent = row.total_completions > 0 ? (row.habit_completions / row.total_completions) * 100 : 0;
          return (
            <div key={row.date} className="chart-bar-column" title={`${row.label}: ${row.task_completions} tasks, ${row.habit_completions} habits`}>
              <span className="chart-bar-stack" style={{ height: `${columnHeight}%` }}>
                <span className="stack-task" style={{ height: `${taskPercent}%` }} />
                <span className="stack-habit" style={{ height: `${habitPercent}%` }} />
              </span>
              <small>{row.label.slice(0, 3)}</small>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function AuthPanel({ mode, authForm, authSubmitting, error, onModeChange, onChange, onSubmit }) {
  const [recoveryRequest, setRecoveryRequest] = useState("testuser1");
  const [recoveryToken, setRecoveryToken] = useState("");
  const [recoveryNewPassword, setRecoveryNewPassword] = useState("");
  const [recoveryConfirmPassword, setRecoveryConfirmPassword] = useState("");
  const [recoverySubmitting, setRecoverySubmitting] = useState("");
  const [recoveryError, setRecoveryError] = useState("");
  const [recoveryNotice, setRecoveryNotice] = useState("");

  async function handleRecoveryRequestSubmit(event) {
    event.preventDefault();
    setRecoverySubmitting("request");
    setRecoveryError("");
    setRecoveryNotice("");
    try {
      const result = await requestPasswordRecovery({ identifier: recoveryRequest });
      if (result.reset_token) {
        setRecoveryToken(result.reset_token);
      }
      setRecoveryNotice(
        result.reset_token
          ? `Recovery token generated. Expires in ${result.expires_in_seconds || "3600"} seconds.`
          : result.message || "If the account exists, reset instructions were generated."
      );
    } catch (err) {
      setRecoveryError(err.message || "Unable to request recovery token");
    } finally {
      setRecoverySubmitting("");
    }
  }

  async function handleRecoveryConfirmSubmit(event) {
    event.preventDefault();
    setRecoverySubmitting("confirm");
    setRecoveryError("");
    setRecoveryNotice("");
    if (recoveryNewPassword !== recoveryConfirmPassword) {
      setRecoveryError("New password and confirmation must match");
      setRecoverySubmitting("");
      return;
    }
    try {
      const result = await confirmPasswordRecovery({
        token: recoveryToken,
        new_password: recoveryNewPassword
      });
      setRecoveryNotice(result.message || "Password reset successful");
      setRecoveryNewPassword("");
      setRecoveryConfirmPassword("");
    } catch (err) {
      setRecoveryError(err.message || "Unable to reset password");
    } finally {
      setRecoverySubmitting("");
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card panel">
        <h1>{ICONS.brand} LifeOS</h1>
        <p className="auth-subtitle">Sign in to your personal operating system.</p>

        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${mode === "login" ? "active" : ""}`}
            onClick={() => onModeChange("login")}
          >
            Login
          </button>
          <button
            type="button"
            className={`auth-tab ${mode === "register" ? "active" : ""}`}
            onClick={() => onModeChange("register")}
          >
            Register
          </button>
        </div>

        <form className="auth-form" onSubmit={onSubmit}>
          {mode === "register" ? (
            <>
              <label>
                Display name
                <input
                  name="display_name"
                  value={authForm.display_name}
                  onChange={onChange}
                  required
                  autoComplete="name"
                />
              </label>
              <label>
                Username
                <input
                  name="username"
                  value={authForm.username}
                  onChange={onChange}
                  required
                  autoComplete="username"
                />
              </label>
              <label>
                Email
                <input
                  name="email"
                  type="email"
                  value={authForm.email}
                  onChange={onChange}
                  required
                  autoComplete="email"
                />
              </label>
            </>
          ) : (
            <label>
              Username or email
              <input
                name="identifier"
                value={authForm.identifier}
                onChange={onChange}
                required
                autoComplete="username"
              />
            </label>
          )}

          <label>
            Password
            <input
              name="password"
              type="password"
              value={authForm.password}
              onChange={onChange}
              required
              autoComplete={mode === "register" ? "new-password" : "current-password"}
            />
          </label>

          {error ? <p className="notice error">{error}</p> : null}

          <button className="auth-submit-btn" type="submit" disabled={authSubmitting}>
            {authSubmitting ? "Please wait..." : mode === "register" ? "Create account" : "Sign in"}
          </button>
        </form>

        <p className="auth-help">
          Test account: <code>testuser1</code> / <code>testuser123</code>
        </p>

        <section className="auth-recovery">
          <h2>Forgot Password?</h2>
          <form className="auth-recovery-form" onSubmit={handleRecoveryRequestSubmit}>
            <label>
              Username or email
              <input value={recoveryRequest} onChange={(event) => setRecoveryRequest(event.target.value)} required />
            </label>
            <button type="submit" className="secondary-btn" disabled={recoverySubmitting === "request"}>
              {recoverySubmitting === "request" ? "Generating..." : "Generate Reset Token"}
            </button>
          </form>

          <form className="auth-recovery-form" onSubmit={handleRecoveryConfirmSubmit}>
            <label>
              Recovery token
              <input value={recoveryToken} onChange={(event) => setRecoveryToken(event.target.value)} required />
            </label>
            <label>
              New password
              <input
                type="password"
                value={recoveryNewPassword}
                onChange={(event) => setRecoveryNewPassword(event.target.value)}
                required
              />
            </label>
            <label>
              Confirm new password
              <input
                type="password"
                value={recoveryConfirmPassword}
                onChange={(event) => setRecoveryConfirmPassword(event.target.value)}
                required
              />
            </label>
            <button type="submit" className="secondary-btn" disabled={recoverySubmitting === "confirm"}>
              {recoverySubmitting === "confirm" ? "Updating..." : "Reset Password"}
            </button>
          </form>

          {recoveryNotice ? <p className="notice success">{recoveryNotice}</p> : null}
          {recoveryError ? <p className="notice error">{recoveryError}</p> : null}
        </section>
      </section>
    </main>
  );
}

export default function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const [authUser, setAuthUser] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [isBooting, setIsBooting] = useState(true);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [authSubmitting, setAuthSubmitting] = useState(false);
  const [settingsBusyKey, setSettingsBusyKey] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [completingTaskId, setCompletingTaskId] = useState(null);
  const [crudLoading, setCrudLoading] = useState(false);
  const [crudBusyKey, setCrudBusyKey] = useState("");
  const [statsLoading, setStatsLoading] = useState(false);
  const [statsRangeDays, setStatsRangeDays] = useState(30);
  const [statsData, setStatsData] = useState(null);
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [notificationsData, setNotificationsData] = useState(null);
  const [shopLoading, setShopLoading] = useState(false);
  const [shopBusyKey, setShopBusyKey] = useState("");
  const [shopData, setShopData] = useState(null);
  const [shopSearchQuery, setShopSearchQuery] = useState("");
  const [shopCategoryFilter, setShopCategoryFilter] = useState("all");
  const [shopOwnershipFilter, setShopOwnershipFilter] = useState("all");
  const [shopAvatarViewFilter, setShopAvatarViewFilter] = useState("all");
  const [shopAvatarSetFilter, setShopAvatarSetFilter] = useState("all");
  const [shopHighlightSetKey, setShopHighlightSetKey] = useState("");
  const [shopHighlightMode, setShopHighlightMode] = useState("");
  const [shopHighlightScrollToken, setShopHighlightScrollToken] = useState(0);
  const [inventoryLoading, setInventoryLoading] = useState(false);
  const [inventoryRedeemBusyKey, setInventoryRedeemBusyKey] = useState("");
  const [inventoryData, setInventoryData] = useState(null);
  const [inventoryCategoryFilter, setInventoryCategoryFilter] = useState("all");
  const [inventoryTypeFilter, setInventoryTypeFilter] = useState("all");
  const [achievementsLoading, setAchievementsLoading] = useState(false);
  const [achievementsData, setAchievementsData] = useState(null);
  const [challengesLoading, setChallengesLoading] = useState(false);
  const [challengesData, setChallengesData] = useState(null);
  const [challengeBusyKey, setChallengeBusyKey] = useState("");
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineData, setTimelineData] = useState(null);
  const [timelineRangeDays, setTimelineRangeDays] = useState(30);
  const [leaderboardLoading, setLeaderboardLoading] = useState(false);
  const [leaderboardData, setLeaderboardData] = useState(null);
  const [leaderboardLimit, setLeaderboardLimit] = useState(15);
  const [leaderboardScope, setLeaderboardScope] = useState("global");
  const [leaderboardBoardKey, setLeaderboardBoardKey] = useState("xp_7d");
  const [seasonPassLoading, setSeasonPassLoading] = useState(false);
  const [seasonPassData, setSeasonPassData] = useState(null);
  const [seasonPassBusyKey, setSeasonPassBusyKey] = useState("");
  const [avatarLoading, setAvatarLoading] = useState(false);
  const [avatarBusyKey, setAvatarBusyKey] = useState("");
  const [avatarData, setAvatarData] = useState(null);
  const [avatarPreviewSetKey, setAvatarPreviewSetKey] = useState("");
  const [avatarSetFilter, setAvatarSetFilter] = useState("all");
  const [avatarSetSort, setAvatarSetSort] = useState("completion_desc");
  const [reminderSettingsLoading, setReminderSettingsLoading] = useState(false);
  const [reminderDeliveries, setReminderDeliveries] = useState([]);
  const [reminderProviders, setReminderProviders] = useState({ email: "console", sms: "console" });
  const [recurringLoading, setRecurringLoading] = useState(false);
  const [recurringBusyKey, setRecurringBusyKey] = useState("");
  const [spacesLoading, setSpacesLoading] = useState(false);
  const [spacesBusyKey, setSpacesBusyKey] = useState("");
  const [sidebarExpanded, setSidebarExpanded] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [taskRows, setTaskRows] = useState([]);
  const [habitRows, setHabitRows] = useState([]);
  const [goalRows, setGoalRows] = useState([]);
  const [recurringRows, setRecurringRows] = useState([]);
  const [spaceRows, setSpaceRows] = useState([]);
  const [spaceDetails, setSpaceDetails] = useState(null);
  const [selectedSpaceId, setSelectedSpaceId] = useState(null);
  const [xpRules, setXpRules] = useState({});
  const [taskEdits, setTaskEdits] = useState({});
  const [habitEdits, setHabitEdits] = useState({});
  const [goalEdits, setGoalEdits] = useState({});
  const [taskForm, setTaskForm] = useState({
    title: "",
    task_type: "task",
    priority: "medium",
    xp_reward: 20,
    due_on: ""
  });
  const [habitForm, setHabitForm] = useState({ name: "" });
  const [goalForm, setGoalForm] = useState({ title: "", target_value: 10, deadline: "" });
  const [dashboardQuickBusyKey, setDashboardQuickBusyKey] = useState("");
  const [dashboardQuickTaskForm, setDashboardQuickTaskForm] = useState({
    title: "",
    task_type: "task",
    priority: "medium",
    xp_reward: "20",
    due_on: ""
  });
  const [dashboardQuickHabitForm, setDashboardQuickHabitForm] = useState({ name: "" });
  const [dashboardQuickGoalForm, setDashboardQuickGoalForm] = useState({ title: "", target_value: "10", deadline: "" });
  const [recurringForm, setRecurringForm] = useState({
    title: "",
    task_type: "task",
    priority: "medium",
    xp_reward: 20,
    frequency: "daily",
    interval: 1,
    days_of_week: [0],
    active: true
  });
  const [recurringRunBackfill, setRecurringRunBackfill] = useState(1);
  const [spaceForm, setSpaceForm] = useState({ name: "" });
  const [spaceRenameForm, setSpaceRenameForm] = useState({ name: "" });
  const [spaceMemberForm, setSpaceMemberForm] = useState({ identifier: "", role: "member" });
  const [spaceInviteForm, setSpaceInviteForm] = useState({ role: "member", expires_in_hours: 72 });
  const [spaceJoinForm, setSpaceJoinForm] = useState({ token: "" });
  const [spaceNotificationPreferenceMode, setSpaceNotificationPreferenceMode] = useState("all");
  const [spaceNotificationDefaultMode, setSpaceNotificationDefaultMode] = useState("all");
  const [spaceNotificationQuietHoursForm, setSpaceNotificationQuietHoursForm] = useState({
    enabled: Boolean(DEFAULT_SPACE_QUIET_HOURS.enabled),
    start_hour_utc: Number(DEFAULT_SPACE_QUIET_HOURS.start_hour_utc),
    end_hour_utc: Number(DEFAULT_SPACE_QUIET_HOURS.end_hour_utc)
  });
  const [spaceTemplateEdits, setSpaceTemplateEdits] = useState({});
  const [spaceTaskForm, setSpaceTaskForm] = useState({
    title: "",
    task_type: "task",
    priority: "medium",
    xp_reward: 25,
    due_on: ""
  });
  const [spaceTaskEdits, setSpaceTaskEdits] = useState({});
  const [taskSearchQuery, setTaskSearchQuery] = useState("");
  const [taskStatusFilter, setTaskStatusFilter] = useState("all");
  const [taskTypeFilter, setTaskTypeFilter] = useState("all");
  const [taskPriorityFilter, setTaskPriorityFilter] = useState("all");
  const [taskSortMode, setTaskSortMode] = useState("due_asc");
  const [habitSearchQuery, setHabitSearchQuery] = useState("");
  const [habitStreakFilter, setHabitStreakFilter] = useState("all");
  const [habitSortMode, setHabitSortMode] = useState("created_desc");
  const [goalSearchQuery, setGoalSearchQuery] = useState("");
  const [goalStatusFilter, setGoalStatusFilter] = useState("all");
  const [goalSortMode, setGoalSortMode] = useState("created_desc");
  const [reminderSettingsForm, setReminderSettingsForm] = useState({
    in_app_enabled: true,
    email_enabled: false,
    sms_enabled: false,
    email_address: "",
    phone_number: "",
    digest_hour_utc: 14
  });
  const [reminderTestForm, setReminderTestForm] = useState({ channel: "all", message: "" });
  const [authForm, setAuthForm] = useState({
    identifier: "testuser1",
    display_name: "",
    username: "",
    email: "",
    password: "testuser123"
  });
  const [profileForm, setProfileForm] = useState({ display_name: "", username: "", email: "" });
  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_new_password: ""
  });
  const [importForm, setImportForm] = useState({
    mode: "merge",
    apply_profile: false,
    snapshot_text: ""
  });
  const [spaceImportForm, setSpaceImportForm] = useState({
    mode: "merge",
    snapshot_text: "",
    confirmation_phrase: ""
  });
  const [spaceImportPreview, setSpaceImportPreview] = useState(null);
  const [spaceReplaceConfirmOpen, setSpaceReplaceConfirmOpen] = useState(false);
  const [spaceAuditForm, setSpaceAuditForm] = useState({ ...SPACE_AUDIT_FILTER_DEFAULT });
  const [spaceAuditRows, setSpaceAuditRows] = useState([]);
  const [spaceAuditSummary, setSpaceAuditSummary] = useState(() => normalizeSpaceAuditSummary(null));
  const [spaceAuditAvailableEventTypes, setSpaceAuditAvailableEventTypes] = useState([]);
  const [spaceAuditLoading, setSpaceAuditLoading] = useState(false);

  const taskEditFromRow = useCallback(
    (task) => ({
      title: task.title,
      status: task.status,
      task_type: task.task_type,
      priority: task.priority,
      xp_reward: task.xp_reward,
      due_on: task.due_on || ""
    }),
    []
  );

  const habitEditFromRow = useCallback(
    (habit) => ({
      name: habit.name,
      current_streak: habit.current_streak,
      longest_streak: habit.longest_streak,
      last_completed_on: habit.last_completed_on || ""
    }),
    []
  );

  const goalEditFromRow = useCallback(
    (goal) => ({
      title: goal.title,
      current_value: goal.current_value,
      target_value: goal.target_value,
      deadline: goal.deadline || ""
    }),
    []
  );

  const spaceTaskEditFromRow = useCallback(
    (task) => ({
      title: task.title,
      status: task.status,
      task_type: task.task_type,
      priority: task.priority,
      xp_reward: task.xp_reward,
      due_on: task.due_on || ""
    }),
    []
  );

  const spaceTemplateEditFromRow = useCallback(
    (template) => ({
      display_name: template.display_name || "",
      can_manage_space: Boolean(template.can_manage_space),
      can_manage_members: Boolean(template.can_manage_members),
      can_assign_admin: Boolean(template.can_assign_admin),
      can_delete_space: Boolean(template.can_delete_space),
      can_manage_invites: Boolean(template.can_manage_invites),
      can_manage_tasks: Boolean(template.can_manage_tasks),
      can_create_tasks: Boolean(template.can_create_tasks),
      can_complete_tasks: Boolean(template.can_complete_tasks)
    }),
    []
  );

  const loadDashboard = useCallback(async () => {
    setDashboardLoading(true);
    try {
      const data = await fetchDashboard();
      setDashboard(data);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load dashboard");
    } finally {
      setDashboardLoading(false);
    }
  }, []);

  const loadStats = useCallback(async (days) => {
    const dayWindow = Number(days) || 30;
    setStatsLoading(true);
    try {
      const payload = await fetchStats(dayWindow);
      setStatsData(payload);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load stats");
    } finally {
      setStatsLoading(false);
    }
  }, []);

  const loadNotifications = useCallback(async () => {
    setNotificationsLoading(true);
    try {
      const payload = await fetchNotifications();
      setNotificationsData(payload);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load notifications");
    } finally {
      setNotificationsLoading(false);
    }
  }, []);

  const loadShop = useCallback(async () => {
    setShopLoading(true);
    try {
      const payload = await fetchShop();
      setShopData(payload);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load shop");
    } finally {
      setShopLoading(false);
    }
  }, []);

  const loadInventory = useCallback(async () => {
    setInventoryLoading(true);
    try {
      const payload = await fetchInventory(240);
      setInventoryData(payload);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load inventory");
    } finally {
      setInventoryLoading(false);
    }
  }, []);

  const loadAchievements = useCallback(async (refresh = true) => {
    setAchievementsLoading(true);
    try {
      const payload = await fetchAchievements(refresh);
      setAchievementsData(payload);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load achievements");
    } finally {
      setAchievementsLoading(false);
    }
  }, []);

  const loadChallenges = useCallback(async (windowType = "") => {
    setChallengesLoading(true);
    try {
      const payload = await fetchChallenges(windowType);
      setChallengesData(payload);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load challenges");
    } finally {
      setChallengesLoading(false);
    }
  }, []);

  const loadTimeline = useCallback(async (days = timelineRangeDays) => {
    setTimelineLoading(true);
    try {
      const payload = await fetchTimeline(days);
      setTimelineData(payload);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load timeline");
    } finally {
      setTimelineLoading(false);
    }
  }, [timelineRangeDays]);

  const loadLeaderboard = useCallback(async (limit = leaderboardLimit, scope = leaderboardScope) => {
    setLeaderboardLoading(true);
    try {
      const payload = await fetchLeaderboard(limit, scope);
      setLeaderboardData(payload);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load leaderboard");
    } finally {
      setLeaderboardLoading(false);
    }
  }, [leaderboardLimit, leaderboardScope]);

  const loadSeasonPass = useCallback(async () => {
    setSeasonPassLoading(true);
    try {
      const payload = await fetchSeasonPass();
      setSeasonPassData(payload);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load season pass");
    } finally {
      setSeasonPassLoading(false);
    }
  }, []);

  const loadAvatar = useCallback(async () => {
    setAvatarLoading(true);
    try {
      const payload = await fetchAvatar();
      setAvatarData(payload);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load avatar");
    } finally {
      setAvatarLoading(false);
    }
  }, []);

  const loadReminderChannels = useCallback(async () => {
    setReminderSettingsLoading(true);
    try {
      const payload = await fetchReminderChannels();
      const settings = payload?.settings || {};
      setReminderSettingsForm({
        in_app_enabled: Boolean(settings.in_app_enabled ?? true),
        email_enabled: Boolean(settings.email_enabled ?? false),
        sms_enabled: Boolean(settings.sms_enabled ?? false),
        email_address: settings.email_address || "",
        phone_number: settings.phone_number || "",
        digest_hour_utc: Number(settings.digest_hour_utc ?? 14)
      });
      setReminderDeliveries(payload?.recent_deliveries || []);
      setReminderProviders(payload?.providers || { email: "console", sms: "console" });
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load reminder channels");
    } finally {
      setReminderSettingsLoading(false);
    }
  }, []);

  const loadRecurringRules = useCallback(async () => {
    setRecurringLoading(true);
    try {
      const rows = await fetchRecurringRules();
      setRecurringRows(rows);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load recurring rules");
    } finally {
      setRecurringLoading(false);
    }
  }, []);

  const loadSpaceDetail = useCallback(async (spaceId) => {
    if (!spaceId) {
      setSpaceDetails(null);
      setSpaceRenameForm({ name: "" });
      setSpaceNotificationPreferenceMode("all");
      setSpaceNotificationDefaultMode("all");
      setSpaceNotificationQuietHoursForm({
        enabled: Boolean(DEFAULT_SPACE_QUIET_HOURS.enabled),
        start_hour_utc: Number(DEFAULT_SPACE_QUIET_HOURS.start_hour_utc),
        end_hour_utc: Number(DEFAULT_SPACE_QUIET_HOURS.end_hour_utc)
      });
      setSpaceTaskEdits({});
      setSpaceTemplateEdits({});
      setSpaceImportPreview(null);
      setSpaceAuditRows([]);
      setSpaceAuditSummary(normalizeSpaceAuditSummary(null));
      setSpaceAuditAvailableEventTypes([]);
      setSpaceAuditForm({ ...SPACE_AUDIT_FILTER_DEFAULT });
      setSpaceAuditLoading(false);
      return null;
    }

    try {
      const payload = await fetchSpaceDetail(spaceId);
      setSpaceDetails(payload);
      setSpaceRenameForm({ name: payload?.space?.name || "" });
      setSpaceNotificationPreferenceMode(payload?.notification_preference?.mode || "all");
      setSpaceNotificationDefaultMode(
        payload?.notification_default?.mode || payload?.space?.default_member_notification_mode || "all"
      );
      const quietHoursPayload =
        payload?.notification_quiet_hours && typeof payload.notification_quiet_hours === "object"
          ? payload.notification_quiet_hours
          : {};
      const quietHoursSpaceFallback = payload?.space && typeof payload.space === "object" ? payload.space : {};
      setSpaceNotificationQuietHoursForm({
        enabled: Boolean(
          quietHoursPayload.enabled ??
            quietHoursSpaceFallback.notification_quiet_hours_enabled ??
            DEFAULT_SPACE_QUIET_HOURS.enabled
        ),
        start_hour_utc: normalizeQuietHour(
          quietHoursPayload.start_hour_utc ?? quietHoursSpaceFallback.notification_quiet_hours_start_utc,
          Number(DEFAULT_SPACE_QUIET_HOURS.start_hour_utc)
        ),
        end_hour_utc: normalizeQuietHour(
          quietHoursPayload.end_hour_utc ?? quietHoursSpaceFallback.notification_quiet_hours_end_utc,
          Number(DEFAULT_SPACE_QUIET_HOURS.end_hour_utc)
        )
      });
      const taskRows = Array.isArray(payload?.tasks) ? payload.tasks : [];
      const roleTemplates = Array.isArray(payload?.role_templates) ? payload.role_templates : [];
      const auditRows = Array.isArray(payload?.audit_events) ? payload.audit_events : [];
      const auditSummary = normalizeSpaceAuditSummary(payload?.audit_summary, auditRows.length);
      setSpaceTaskEdits(Object.fromEntries(taskRows.map((task) => [task.id, spaceTaskEditFromRow(task)])));
      setSpaceTemplateEdits(Object.fromEntries(roleTemplates.map((row) => [row.role, spaceTemplateEditFromRow(row)])));
      setSpaceAuditRows(auditRows);
      setSpaceAuditSummary(auditSummary);
      setSpaceAuditAvailableEventTypes(
        normalizeSpaceAuditEventTypes(payload?.audit_available_event_types, auditSummary)
      );
      setSpaceAuditForm({ ...SPACE_AUDIT_FILTER_DEFAULT });
      setError("");
      return payload;
    } catch (err) {
      setSpaceDetails(null);
      setSpaceRenameForm({ name: "" });
      setSpaceNotificationPreferenceMode("all");
      setSpaceNotificationDefaultMode("all");
      setSpaceNotificationQuietHoursForm({
        enabled: Boolean(DEFAULT_SPACE_QUIET_HOURS.enabled),
        start_hour_utc: Number(DEFAULT_SPACE_QUIET_HOURS.start_hour_utc),
        end_hour_utc: Number(DEFAULT_SPACE_QUIET_HOURS.end_hour_utc)
      });
      setSpaceTaskEdits({});
      setSpaceTemplateEdits({});
      setSpaceImportPreview(null);
      setSpaceAuditRows([]);
      setSpaceAuditSummary(normalizeSpaceAuditSummary(null));
      setSpaceAuditAvailableEventTypes([]);
      setSpaceAuditForm({ ...SPACE_AUDIT_FILTER_DEFAULT });
      setSpaceAuditLoading(false);
      setError(err.message || "Unable to load space");
      return null;
    }
  }, [spaceTaskEditFromRow, spaceTemplateEditFromRow]);

  const loadSpaces = useCallback(async (preferredSpaceId = null) => {
    setSpacesLoading(true);
    try {
      const spaces = await fetchSpaces();
      setSpaceRows(spaces);
      setError("");

      let nextSelectedId = null;
      setSelectedSpaceId((previousId) => {
        if (preferredSpaceId && spaces.some((space) => space.id === preferredSpaceId)) {
          nextSelectedId = preferredSpaceId;
          return preferredSpaceId;
        }
        if (previousId && spaces.some((space) => space.id === previousId)) {
          nextSelectedId = previousId;
          return previousId;
        }
        const fallbackId = spaces[0]?.id || null;
        nextSelectedId = fallbackId;
        return fallbackId;
      });
      await loadSpaceDetail(nextSelectedId);
    } catch (err) {
      setError(err.message || "Unable to load spaces");
    } finally {
      setSpacesLoading(false);
    }
  }, [loadSpaceDetail]);

  const loadCrudData = useCallback(async () => {
    setCrudLoading(true);
    try {
      const [tasks, habits, goals, rules] = await Promise.all([fetchTasks(), fetchHabits(), fetchGoals(), fetchXpRules()]);
      setTaskRows(tasks);
      setHabitRows(habits);
      setGoalRows(goals);
      setXpRules(rules);
      setTaskEdits(Object.fromEntries(tasks.map((task) => [task.id, taskEditFromRow(task)])));
      setHabitEdits(Object.fromEntries(habits.map((habit) => [habit.id, habitEditFromRow(habit)])));
      setGoalEdits(Object.fromEntries(goals.map((goal) => [goal.id, goalEditFromRow(goal)])));
      setError("");
    } catch (err) {
      setError(err.message || "Unable to load management data");
    } finally {
      setCrudLoading(false);
    }
  }, [goalEditFromRow, habitEditFromRow, taskEditFromRow]);

  const refreshAllData = useCallback(
    async (days = statsRangeDays) =>
      Promise.all([
        loadDashboard(),
        loadCrudData(),
        loadStats(days),
        loadNotifications(),
        loadShop(),
        loadInventory(),
        loadAchievements(),
        loadChallenges(),
        loadTimeline(timelineRangeDays),
        loadLeaderboard(leaderboardLimit, leaderboardScope),
        loadSeasonPass(),
        loadAvatar(),
        loadReminderChannels(),
        loadRecurringRules(),
        loadSpaces()
      ]),
    [
      loadAchievements,
      loadAvatar,
      loadChallenges,
      loadCrudData,
      loadDashboard,
      loadInventory,
      loadLeaderboard,
      loadNotifications,
      loadRecurringRules,
      loadReminderChannels,
      loadSeasonPass,
      loadShop,
      loadSpaces,
      loadStats,
      loadTimeline,
      leaderboardLimit,
      leaderboardScope,
      statsRangeDays,
      timelineRangeDays
    ]
  );

  useEffect(() => {
    let active = true;
    async function bootstrapSession() {
      try {
        const me = await fetchMe();
        if (!active) {
          return;
        }
        setAuthUser(me.user);
        await refreshAllData(30);
      } catch (_err) {
        clearAuthToken();
      } finally {
        if (active) {
          setIsBooting(false);
        }
      }
    }
    bootstrapSession();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!authUser) {
      return;
    }
    setProfileForm({
      display_name: authUser.display_name || "",
      username: authUser.username || "",
      email: authUser.email || ""
    });
  }, [authUser]);

  async function handleAuthSubmit(event) {
    event.preventDefault();
    setAuthSubmitting(true);
    setError("");
    setNotice("");
    try {
      const payload =
        authMode === "register"
          ? await registerUser({
              display_name: authForm.display_name,
              username: authForm.username,
              email: authForm.email,
              password: authForm.password
            })
          : await loginUser({ identifier: authForm.identifier, password: authForm.password });

      setAuthUser(payload.user);
      navigate("/dashboard", { replace: true });
      await refreshAllData(statsRangeDays);
      setNotice(authMode === "register" ? "Account created." : "Signed in.");
    } catch (err) {
      setError(err.message || "Authentication failed");
    } finally {
      setAuthSubmitting(false);
    }
  }

  async function handleCompleteTask(taskId) {
    setCompletingTaskId(taskId);
    setNotice("");
    setError("");
    try {
      const result = await completeTask(taskId);
      setDashboard(result.dashboard);
      setNotice(formatRewardNotice(result?.xp_gained, result?.coins_gained, "Task completed."));
      await Promise.all([
        loadCrudData(),
        loadStats(statsRangeDays),
        loadNotifications(),
        loadShop(),
        loadInventory(),
        loadAchievements(),
        loadChallenges(),
        loadTimeline(timelineRangeDays),
        loadLeaderboard(leaderboardLimit, leaderboardScope),
        loadSeasonPass(),
        loadAvatar(),
        loadRecurringRules(),
        loadReminderChannels()
      ]);
    } catch (err) {
      setError(err.message || "Unable to complete task");
    } finally {
      setCompletingTaskId(null);
    }
  }

  async function handleTaskCreate(event) {
    event.preventDefault();
    setCrudBusyKey("task-create");
    setError("");
    setNotice("");
    try {
      await createTask({
        title: taskForm.title,
        task_type: taskForm.task_type,
        priority: taskForm.priority,
        xp_reward: Number(taskForm.xp_reward),
        due_on: taskForm.due_on || null
      });
      setTaskForm((prev) => ({ ...prev, title: "", due_on: "" }));
      await refreshAllData(statsRangeDays);
      setNotice("Task created.");
    } catch (err) {
      setError(err.message || "Unable to create task");
    } finally {
      setCrudBusyKey("");
    }
  }

  async function handleTaskSave(taskId) {
    const edit = taskEdits[taskId];
    if (!edit) {
      return;
    }

    setCrudBusyKey(`task-save-${taskId}`);
    setError("");
    setNotice("");
    try {
      await updateTask(taskId, {
        title: edit.title,
        status: edit.status,
        task_type: edit.task_type,
        priority: edit.priority,
        xp_reward: Number(edit.xp_reward),
        due_on: edit.due_on || null
      });
      await refreshAllData(statsRangeDays);
      setNotice("Task updated.");
    } catch (err) {
      setError(err.message || "Unable to update task");
    } finally {
      setCrudBusyKey("");
    }
  }

  async function handleTaskDelete(taskId) {
    setCrudBusyKey(`task-delete-${taskId}`);
    setError("");
    setNotice("");
    try {
      await deleteTask(taskId);
      await refreshAllData(statsRangeDays);
      setNotice("Task deleted.");
    } catch (err) {
      setError(err.message || "Unable to delete task");
    } finally {
      setCrudBusyKey("");
    }
  }

  async function handleHabitCreate(event) {
    event.preventDefault();
    setCrudBusyKey("habit-create");
    setError("");
    setNotice("");
    try {
      const result = await createHabit({ name: habitForm.name });
      setHabitForm({ name: "" });
      await refreshAllData(statsRangeDays);
      setNotice(formatRewardNotice(result?.xp_gained, result?.coins_gained, "Habit created."));
    } catch (err) {
      setError(err.message || "Unable to create habit");
    } finally {
      setCrudBusyKey("");
    }
  }

  async function handleHabitSave(habitId) {
    const edit = habitEdits[habitId];
    if (!edit) {
      return;
    }
    setCrudBusyKey(`habit-save-${habitId}`);
    setError("");
    setNotice("");
    try {
      await updateHabit(habitId, {
        name: edit.name,
        current_streak: Number(edit.current_streak),
        longest_streak: Number(edit.longest_streak),
        last_completed_on: edit.last_completed_on || null
      });
      await refreshAllData(statsRangeDays);
      setNotice("Habit updated.");
    } catch (err) {
      setError(err.message || "Unable to update habit");
    } finally {
      setCrudBusyKey("");
    }
  }

  async function handleHabitComplete(habitId) {
    setCrudBusyKey(`habit-complete-${habitId}`);
    setError("");
    setNotice("");
    try {
      const result = await completeHabit(habitId);
      setDashboard(result.dashboard);
      await Promise.all([
        loadCrudData(),
        loadStats(statsRangeDays),
        loadNotifications(),
        loadShop(),
        loadInventory(),
        loadAchievements(),
        loadChallenges(),
        loadTimeline(timelineRangeDays),
        loadLeaderboard(leaderboardLimit, leaderboardScope),
        loadSeasonPass(),
        loadAvatar(),
        loadRecurringRules(),
        loadReminderChannels()
      ]);
      setNotice(formatRewardNotice(result?.xp_gained, result?.coins_gained, "Habit already completed today."));
    } catch (err) {
      setError(err.message || "Unable to complete habit");
    } finally {
      setCrudBusyKey("");
    }
  }

  async function handleHabitDelete(habitId) {
    setCrudBusyKey(`habit-delete-${habitId}`);
    setError("");
    setNotice("");
    try {
      await deleteHabit(habitId);
      await refreshAllData(statsRangeDays);
      setNotice("Habit deleted.");
    } catch (err) {
      setError(err.message || "Unable to delete habit");
    } finally {
      setCrudBusyKey("");
    }
  }

  async function handleGoalCreate(event) {
    event.preventDefault();
    setCrudBusyKey("goal-create");
    setError("");
    setNotice("");
    try {
      const result = await createGoal({
        title: goalForm.title,
        target_value: Number(goalForm.target_value),
        deadline: goalForm.deadline || null
      });
      setGoalForm({ title: "", target_value: 10, deadline: "" });
      await refreshAllData(statsRangeDays);
      setNotice(formatRewardNotice(result?.xp_gained, result?.coins_gained, "Goal created."));
    } catch (err) {
      setError(err.message || "Unable to create goal");
    } finally {
      setCrudBusyKey("");
    }
  }

  function handleDashboardQuickTaskTypeChange(nextType) {
    const raw = String(nextType || "").trim().toLowerCase();
    const safeType = raw === "habit" || raw === "quest" ? raw : "task";
    const xpPreset = DASHBOARD_QUICK_TASK_XP_PRESETS[safeType] || DASHBOARD_QUICK_TASK_XP_PRESETS.task;
    setDashboardQuickTaskForm((prev) => ({
      ...prev,
      task_type: safeType,
      xp_reward: xpPreset
    }));
  }

  function handleDashboardQuickTaskDuePreset(presetKey) {
    const normalizedKey = String(presetKey || "").trim().toLowerCase();
    let dueOnValue = "";
    if (normalizedKey === "today") {
      dueOnValue = formatDateInputValue(new Date());
    } else if (normalizedKey === "tomorrow") {
      const nextDay = new Date();
      nextDay.setDate(nextDay.getDate() + 1);
      dueOnValue = formatDateInputValue(nextDay);
    }
    setDashboardQuickTaskForm((prev) => ({ ...prev, due_on: dueOnValue }));
  }

  async function handleDashboardQuickTaskCreate(event) {
    event.preventDefault();
    setDashboardQuickBusyKey("task-create");
    setError("");
    setNotice("");
    try {
      const title = String(dashboardQuickTaskForm.title || "").trim();
      if (!title) {
        throw new Error("Task title is required");
      }
      const xpRewardRaw = Number(dashboardQuickTaskForm.xp_reward);
      const xpReward = Number.isFinite(xpRewardRaw) ? Math.max(1, Math.round(xpRewardRaw)) : NaN;
      if (!Number.isFinite(xpReward)) {
        throw new Error("Task XP reward must be a valid number");
      }
      await createTask({
        title,
        task_type: dashboardQuickTaskForm.task_type,
        priority: dashboardQuickTaskForm.priority,
        xp_reward: xpReward,
        due_on: String(dashboardQuickTaskForm.due_on || "").trim() || null
      });
      setDashboardQuickTaskForm((prev) => ({ ...prev, title: "", due_on: "" }));
      await refreshAllData(statsRangeDays);
      setNotice("Quick task created.");
    } catch (err) {
      setError(err.message || "Unable to create quick task");
    } finally {
      setDashboardQuickBusyKey("");
    }
  }

  async function handleDashboardQuickHabitCreate(event) {
    event.preventDefault();
    setDashboardQuickBusyKey("habit-create");
    setError("");
    setNotice("");
    try {
      const name = String(dashboardQuickHabitForm.name || "").trim();
      if (!name) {
        throw new Error("Habit name is required");
      }
      const result = await createHabit({ name });
      setDashboardQuickHabitForm({ name: "" });
      await refreshAllData(statsRangeDays);
      setNotice(formatRewardNotice(result?.xp_gained, result?.coins_gained, "Quick habit created."));
    } catch (err) {
      setError(err.message || "Unable to create quick habit");
    } finally {
      setDashboardQuickBusyKey("");
    }
  }

  async function handleDashboardQuickGoalCreate(event) {
    event.preventDefault();
    setDashboardQuickBusyKey("goal-create");
    setError("");
    setNotice("");
    try {
      const title = String(dashboardQuickGoalForm.title || "").trim();
      if (!title) {
        throw new Error("Goal title is required");
      }
      const targetRaw = Number(dashboardQuickGoalForm.target_value);
      const targetValue = Number.isFinite(targetRaw) ? Math.max(1, Math.round(targetRaw)) : NaN;
      if (!Number.isFinite(targetValue)) {
        throw new Error("Goal target must be a valid number");
      }
      const result = await createGoal({
        title,
        target_value: targetValue,
        deadline: String(dashboardQuickGoalForm.deadline || "").trim() || null
      });
      setDashboardQuickGoalForm((prev) => ({ ...prev, title: "" }));
      await refreshAllData(statsRangeDays);
      setNotice(formatRewardNotice(result?.xp_gained, result?.coins_gained, "Quick goal created."));
    } catch (err) {
      setError(err.message || "Unable to create quick goal");
    } finally {
      setDashboardQuickBusyKey("");
    }
  }

  async function handleGoalSave(goalId) {
    const edit = goalEdits[goalId];
    if (!edit) {
      return;
    }
    setCrudBusyKey(`goal-save-${goalId}`);
    setError("");
    setNotice("");
    try {
      await updateGoal(goalId, {
        title: edit.title,
        current_value: Number(edit.current_value),
        target_value: Number(edit.target_value),
        deadline: edit.deadline || null
      });
      await refreshAllData(statsRangeDays);
      setNotice("Goal updated.");
    } catch (err) {
      setError(err.message || "Unable to update goal");
    } finally {
      setCrudBusyKey("");
    }
  }

  async function handleGoalDelete(goalId) {
    setCrudBusyKey(`goal-delete-${goalId}`);
    setError("");
    setNotice("");
    try {
      await deleteGoal(goalId);
      await refreshAllData(statsRangeDays);
      setNotice("Goal deleted.");
    } catch (err) {
      setError(err.message || "Unable to delete goal");
    } finally {
      setCrudBusyKey("");
    }
  }

  function handleRecurringWeekdayToggle(dayValue) {
    setRecurringForm((prev) => {
      const current = Array.isArray(prev.days_of_week) ? prev.days_of_week : [];
      const exists = current.includes(dayValue);
      const nextDays = exists ? current.filter((day) => day !== dayValue) : [...current, dayValue].sort((a, b) => a - b);
      return { ...prev, days_of_week: nextDays };
    });
  }

  async function handleRecurringCreate(event) {
    event.preventDefault();
    setRecurringBusyKey("recurring-create");
    setError("");
    setNotice("");
    try {
      await createRecurringRule({
        title: recurringForm.title,
        task_type: recurringForm.task_type,
        priority: recurringForm.priority,
        xp_reward: Number(recurringForm.xp_reward),
        frequency: recurringForm.frequency,
        interval: Number(recurringForm.interval),
        days_of_week: recurringForm.frequency === "weekly" ? recurringForm.days_of_week : [],
        active: recurringForm.active
      });
      setRecurringForm((prev) => ({ ...prev, title: "", xp_reward: prev.task_type === "habit" ? 15 : 20 }));
      await refreshAllData(statsRangeDays);
      setNotice("Recurring rule created.");
    } catch (err) {
      setError(err.message || "Unable to create recurring rule");
    } finally {
      setRecurringBusyKey("");
    }
  }

  async function handleRecurringActiveToggle(rule) {
    setRecurringBusyKey(`recurring-toggle-${rule.id}`);
    setError("");
    setNotice("");
    try {
      await updateRecurringRule(rule.id, { active: !rule.active });
      await loadRecurringRules();
      setNotice(`Recurring rule ${rule.active ? "paused" : "activated"}.`);
    } catch (err) {
      setError(err.message || "Unable to update recurring rule");
    } finally {
      setRecurringBusyKey("");
    }
  }

  async function handleRecurringDelete(ruleId) {
    setRecurringBusyKey(`recurring-delete-${ruleId}`);
    setError("");
    setNotice("");
    try {
      await deleteRecurringRule(ruleId);
      await refreshAllData(statsRangeDays);
      setNotice("Recurring rule deleted.");
    } catch (err) {
      setError(err.message || "Unable to delete recurring rule");
    } finally {
      setRecurringBusyKey("");
    }
  }

  async function handleRecurringRunNow() {
    setRecurringBusyKey("recurring-run");
    setError("");
    setNotice("");
    try {
      const result = await runRecurringRules({ backfill_days: Number(recurringRunBackfill) || 1 });
      await refreshAllData(statsRangeDays);
      const created = result?.summary?.created ?? 0;
      setNotice(`Recurring generation complete (${created} tasks created).`);
    } catch (err) {
      setError(err.message || "Unable to run recurring generation");
    } finally {
      setRecurringBusyKey("");
    }
  }

  async function handleReminderSettingsSave(event) {
    event.preventDefault();
    setSettingsBusyKey("reminders-save");
    setError("");
    setNotice("");
    try {
      const digestHour = Number.isFinite(Number(reminderSettingsForm.digest_hour_utc))
        ? Number(reminderSettingsForm.digest_hour_utc)
        : 14;
      const result = await updateReminderChannels({
        in_app_enabled: Boolean(reminderSettingsForm.in_app_enabled),
        email_enabled: Boolean(reminderSettingsForm.email_enabled),
        sms_enabled: Boolean(reminderSettingsForm.sms_enabled),
        email_address: reminderSettingsForm.email_address || null,
        phone_number: reminderSettingsForm.phone_number || null,
        digest_hour_utc: digestHour
      });
      if (result?.settings) {
        setReminderSettingsForm({
          in_app_enabled: Boolean(result.settings.in_app_enabled),
          email_enabled: Boolean(result.settings.email_enabled),
          sms_enabled: Boolean(result.settings.sms_enabled),
          email_address: result.settings.email_address || "",
          phone_number: result.settings.phone_number || "",
          digest_hour_utc: Number(result.settings.digest_hour_utc ?? 14)
        });
      }
      await Promise.all([loadNotifications(), loadReminderChannels()]);
      setNotice("Reminder channel settings updated.");
    } catch (err) {
      setError(err.message || "Unable to update reminder channels");
    } finally {
      setSettingsBusyKey("");
    }
  }

  async function handleReminderTestSend(event) {
    event.preventDefault();
    setSettingsBusyKey("reminders-test");
    setError("");
    setNotice("");
    try {
      const result = await sendReminderChannelTest({
        channel: reminderTestForm.channel,
        message: reminderTestForm.message || undefined
      });
      await loadReminderChannels();
      setNotice(result.message || "Test reminder sent.");
    } catch (err) {
      setError(err.message || "Unable to send test reminder");
    } finally {
      setSettingsBusyKey("");
    }
  }

  async function handleReminderRunNow() {
    setSettingsBusyKey("reminders-run");
    setError("");
    setNotice("");
    try {
      const result = await runReminderChannelDelivery({});
      await Promise.all([loadReminderChannels(), loadNotifications()]);
      const sent = result?.summary?.sent ?? 0;
      setNotice(`Reminder delivery run complete (${sent} messages sent).`);
    } catch (err) {
      setError(err.message || "Unable to run reminder delivery");
    } finally {
      setSettingsBusyKey("");
    }
  }

  async function handleReminderRefreshLogs() {
    setSettingsBusyKey("reminders-logs");
    setError("");
    try {
      const rows = await fetchReminderDeliveries(30);
      setReminderDeliveries(rows);
    } catch (err) {
      setError(err.message || "Unable to refresh reminder deliveries");
    } finally {
      setSettingsBusyKey("");
    }
  }

  async function handleProfileUpdate(event) {
    event.preventDefault();
    setSettingsBusyKey("profile");
    setError("");
    setNotice("");
    try {
      const result = await updateAccountProfile({
        display_name: profileForm.display_name,
        username: profileForm.username,
        email: profileForm.email
      });
      setAuthUser(result.user);
      setDashboard((prev) =>
        prev
          ? {
              ...prev,
              user: {
                ...prev.user,
                username: result.user.username,
                display_name: result.user.display_name
              }
            }
          : prev
      );
      setNotice("Profile updated.");
    } catch (err) {
      setError(err.message || "Unable to update profile");
    } finally {
      setSettingsBusyKey("");
    }
  }

  async function handlePasswordUpdate(event) {
    event.preventDefault();
    setSettingsBusyKey("password");
    setError("");
    setNotice("");
    if (passwordForm.new_password !== passwordForm.confirm_new_password) {
      setError("New password and confirmation must match");
      setSettingsBusyKey("");
      return;
    }
    try {
      const result = await updateAccountPassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password
      });
      setPasswordForm({ current_password: "", new_password: "", confirm_new_password: "" });
      setNotice(result.message || "Password updated.");
    } catch (err) {
      setError(err.message || "Unable to update password");
    } finally {
      setSettingsBusyKey("");
    }
  }

  function downloadSnapshotFile(snapshot, fileName) {
    const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = fileName;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  async function handleExportSnapshot() {
    setSettingsBusyKey("export");
    setError("");
    setNotice("");
    try {
      const snapshot = await exportAccountSnapshot();
      const stamp = new Date().toISOString().replace(/[:]/g, "-");
      const fileName = `lifeos_snapshot_${stamp}.json`;
      downloadSnapshotFile(snapshot, fileName);
      setNotice("Snapshot exported.");
    } catch (err) {
      setError(err.message || "Unable to export snapshot");
    } finally {
      setSettingsBusyKey("");
    }
  }

  async function handleImportSnapshot(event) {
    event.preventDefault();
    setSettingsBusyKey("import");
    setError("");
    setNotice("");

    let snapshotObject;
    try {
      snapshotObject = JSON.parse(importForm.snapshot_text);
    } catch (_err) {
      setError("Snapshot JSON is invalid");
      setSettingsBusyKey("");
      return;
    }

    try {
      const result = await importAccountSnapshot({
        snapshot: snapshotObject,
        mode: importForm.mode,
        apply_profile: importForm.apply_profile
      });
      if (result.user) {
        setAuthUser(result.user);
      }
      if (result.dashboard) {
        setDashboard(result.dashboard);
      }
      await Promise.all([loadCrudData(), loadStats(statsRangeDays), loadNotifications(), loadRecurringRules(), loadReminderChannels()]);

      const imported = result.summary?.imported || {};
      const importedTotal =
        Number(imported.tasks || 0) +
        Number(imported.habits || 0) +
        Number(imported.habit_logs || 0) +
        Number(imported.goals || 0) +
        Number(imported.recurring_rules || 0) +
        Number(imported.reminder_channels || 0) +
        Number(imported.xp_ledger || 0);

      setNotice(result.message ? `${result.message} (${importedTotal} records).` : `Import completed (${importedTotal} records).`);
      setImportForm((prev) => ({ ...prev, snapshot_text: "" }));
    } catch (err) {
      setError(err.message || "Unable to import snapshot");
    } finally {
      setSettingsBusyKey("");
    }
  }

  async function handleSpaceExportSnapshot() {
    if (!selectedSpaceId || !selectedSpacePermissions.can_manage_space) {
      return;
    }
    setSpacesBusyKey("space-export");
    setError("");
    setNotice("");
    try {
      const snapshot = await exportSpaceSnapshot(selectedSpaceId);
      const safeName = String(selectedSpace?.name || "space")
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "")
        .slice(0, 48);
      const stamp = new Date().toISOString().replace(/[:]/g, "-");
      const fileName = `lifeos_space_${safeName || "snapshot"}_${stamp}.json`;
      downloadSnapshotFile(snapshot, fileName);
      setNotice("Space snapshot exported.");
    } catch (err) {
      setError(err.message || "Unable to export space snapshot");
    } finally {
      setSpacesBusyKey("");
    }
  }

  function parseSpaceSnapshotImportText() {
    try {
      return JSON.parse(spaceImportForm.snapshot_text);
    } catch (_err) {
      setSpaceImportPreview(null);
      setError("Space snapshot JSON is invalid");
      return null;
    }
  }

  async function handleSpaceImportPreview() {
    if (!selectedSpaceId) {
      return;
    }
    setSpaceReplaceConfirmOpen(false);
    setSpacesBusyKey("space-import-preview");
    setError("");
    setNotice("");

    const snapshotObject = parseSpaceSnapshotImportText();
    if (!snapshotObject) {
      setSpacesBusyKey("");
      return;
    }

    try {
      const result = await previewSpaceSnapshotImport(selectedSpaceId, {
        snapshot: snapshotObject,
        mode: spaceImportForm.mode
      });
      setSpaceImportPreview(result);
      const imported = result.summary?.imported || {};
      const importedTotal =
        Number(imported.members || 0) +
        Number(imported.tasks || 0) +
        Number(imported.role_templates || 0) +
        Number(imported.notification_preferences || 0);
      setNotice(
        result.message
          ? `${result.message} (${importedTotal} records would import).`
          : `Preview generated (${importedTotal} records would import).`
      );
    } catch (err) {
      setSpaceImportPreview(null);
      setError(err.message || "Unable to preview space snapshot import");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function runSpaceImportSnapshot(snapshotObject) {
    if (!selectedSpaceId) {
      return;
    }
    setSpacesBusyKey("space-import");
    setError("");
    setNotice("");

    const typedConfirmationPhrase = String(spaceImportForm.confirmation_phrase || "").trim();
    try {
      const result = await importSpaceSnapshot(selectedSpaceId, {
        snapshot: snapshotObject,
        mode: spaceImportForm.mode,
        confirmation_phrase: spaceImportForm.mode === "replace" ? typedConfirmationPhrase : undefined
      });
      await Promise.all([loadSpaces(selectedSpaceId), loadNotifications()]);
      const imported = result.summary?.imported || {};
      const importedTotal =
        Number(imported.members || 0) +
        Number(imported.tasks || 0) +
        Number(imported.role_templates || 0) +
        Number(imported.notification_preferences || 0);
      setNotice(
        result.message
          ? `${result.message} (${importedTotal} records).`
          : `Space import completed (${importedTotal} records).`
      );
      setSpaceImportForm((prev) => ({ ...prev, snapshot_text: "", confirmation_phrase: "" }));
      setSpaceImportPreview(null);
      setSpaceReplaceConfirmOpen(false);
    } catch (err) {
      setError(err.message || "Unable to import space snapshot");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceImportSnapshot(event) {
    event.preventDefault();
    if (!selectedSpaceId) {
      return;
    }
    setError("");
    setNotice("");

    const snapshotObject = parseSpaceSnapshotImportText();
    if (!snapshotObject) {
      return;
    }

    if (spaceImportForm.mode === "replace" && !spaceReplacePreviewReady) {
      setError("Run Preview Import in replace mode before importing this snapshot.");
      return;
    }

    if (spaceImportForm.mode === "replace" && !spaceImportConfirmationMatches) {
      setError(
        spaceImportRequiredPhrase
          ? `Type the required confirmation phrase exactly: ${spaceImportRequiredPhrase}`
          : "Replace import confirmation phrase is required."
      );
      return;
    }

    if (spaceImportForm.mode === "replace") {
      setSpaceReplaceConfirmOpen(true);
      return;
    }

    await runSpaceImportSnapshot(snapshotObject);
  }

  async function handleSpaceImportReplaceConfirm() {
    if (!selectedSpaceId || spacesBusyKey === "space-import") {
      return;
    }
    if (!spaceReplacePreviewReady) {
      setError("Run Preview Import in replace mode before importing this snapshot.");
      return;
    }
    if (!spaceImportConfirmationMatches) {
      setError(
        spaceImportRequiredPhrase
          ? `Type the required confirmation phrase exactly: ${spaceImportRequiredPhrase}`
          : "Replace import confirmation phrase is required."
      );
      return;
    }
    const snapshotObject = parseSpaceSnapshotImportText();
    if (!snapshotObject) {
      return;
    }
    await runSpaceImportSnapshot(snapshotObject);
  }

  async function handleSpaceAuditFilterApply(event) {
    event.preventDefault();
    if (!selectedSpaceId) {
      return;
    }
    setSpaceAuditLoading(true);
    setError("");
    setNotice("");
    try {
      const payload = await fetchSpaceAuditEvents(selectedSpaceId, {
        limit: SPACE_AUDIT_FETCH_LIMIT,
        event_type: spaceAuditForm.event_type,
        days: spaceAuditForm.days,
        query: spaceAuditForm.query
      });
      const rows = Array.isArray(payload?.events) ? payload.events : [];
      const summary = normalizeSpaceAuditSummary(payload?.summary, rows.length);
      setSpaceAuditRows(rows);
      setSpaceAuditSummary(summary);
      setSpaceAuditAvailableEventTypes(normalizeSpaceAuditEventTypes(payload?.available_event_types, summary));
      setNotice(`Audit filters applied (${prettyNumber(rows.length)} event${rows.length === 1 ? "" : "s"}).`);
    } catch (err) {
      setError(err.message || "Unable to filter audit trail");
    } finally {
      setSpaceAuditLoading(false);
    }
  }

  function handleSpaceAuditFilterReset() {
    const auditRows = Array.isArray(spaceDetails?.audit_events) ? spaceDetails.audit_events : [];
    const auditSummary = normalizeSpaceAuditSummary(spaceDetails?.audit_summary, auditRows.length);
    setSpaceAuditRows(auditRows);
    setSpaceAuditSummary(auditSummary);
    setSpaceAuditAvailableEventTypes(
      normalizeSpaceAuditEventTypes(spaceDetails?.audit_available_event_types, auditSummary)
    );
    setSpaceAuditForm({ ...SPACE_AUDIT_FILTER_DEFAULT });
    setSpaceAuditLoading(false);
    setNotice("");
    setError("");
  }

  function handleSpaceSelect(spaceId) {
    setSelectedSpaceId(spaceId);
    setSpaceImportForm((prev) => ({ ...prev, snapshot_text: "", confirmation_phrase: "" }));
    setSpaceImportPreview(null);
    setSpaceReplaceConfirmOpen(false);
    setSpaceAuditForm({ ...SPACE_AUDIT_FILTER_DEFAULT });
    setSpaceAuditRows([]);
    setSpaceAuditSummary(normalizeSpaceAuditSummary(null));
    setSpaceAuditAvailableEventTypes([]);
    setSpaceAuditLoading(false);
    void loadSpaceDetail(spaceId);
    setNotice("");
    setError("");
  }

  async function handleSpaceCreate(event) {
    event.preventDefault();
    setSpacesBusyKey("space-create");
    setError("");
    setNotice("");
    try {
      const result = await createSpace({ name: spaceForm.name });
      const newSpaceId = result?.space?.id || null;
      setSpaceForm({ name: "" });
      await loadSpaces(newSpaceId);
      setNotice("Space created.");
    } catch (err) {
      setError(err.message || "Unable to create space");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceRename(event) {
    event.preventDefault();
    if (!selectedSpaceId) {
      return;
    }
    setSpacesBusyKey("space-rename");
    setError("");
    setNotice("");
    try {
      await updateSpace(selectedSpaceId, { name: spaceRenameForm.name });
      await loadSpaces(selectedSpaceId);
      setNotice("Space updated.");
    } catch (err) {
      setError(err.message || "Unable to update space");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceDelete() {
    if (!selectedSpaceId) {
      return;
    }
    setSpacesBusyKey("space-delete");
    setError("");
    setNotice("");
    try {
      await deleteSpace(selectedSpaceId);
      await loadSpaces();
      setNotice("Space deleted.");
    } catch (err) {
      setError(err.message || "Unable to delete space");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceMemberAdd(event) {
    event.preventDefault();
    if (!selectedSpaceId) {
      return;
    }
    setSpacesBusyKey("space-member-add");
    setError("");
    setNotice("");
    try {
      await addSpaceMember(selectedSpaceId, {
        identifier: spaceMemberForm.identifier,
        role: spaceMemberForm.role
      });
      setSpaceMemberForm({ identifier: "", role: "member" });
      await loadSpaces(selectedSpaceId);
      setNotice("Member added.");
    } catch (err) {
      setError(err.message || "Unable to add member");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceMemberRoleChange(memberUserId, role) {
    if (!selectedSpaceId) {
      return;
    }
    setSpacesBusyKey(`space-member-role-${memberUserId}`);
    setError("");
    setNotice("");
    try {
      await updateSpaceMemberRole(selectedSpaceId, memberUserId, { role });
      await loadSpaces(selectedSpaceId);
      setNotice("Member role updated.");
    } catch (err) {
      setError(err.message || "Unable to update member role");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceMemberRemove(memberUserId) {
    if (!selectedSpaceId) {
      return;
    }
    const isSelf = Number(memberUserId) === Number(authUser?.id);
    setSpacesBusyKey(`space-member-remove-${memberUserId}`);
    setError("");
    setNotice("");
    try {
      await removeSpaceMember(selectedSpaceId, memberUserId);
      await loadSpaces(isSelf ? null : selectedSpaceId);
      setNotice(isSelf ? "You left the space." : "Member removed.");
    } catch (err) {
      setError(err.message || "Unable to remove member");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceInviteCreate(event) {
    event.preventDefault();
    if (!selectedSpaceId) {
      return;
    }
    setSpacesBusyKey("space-invite-create");
    setError("");
    setNotice("");
    try {
      const result = await createSpaceInvite(selectedSpaceId, {
        role: spaceInviteForm.role,
        expires_in_hours: Number(spaceInviteForm.expires_in_hours) || 72
      });
      await loadSpaceDetail(selectedSpaceId);
      const inviteToken = result?.invite?.invite_token || "";
      setNotice(inviteToken ? `Invite created: ${inviteToken}` : "Invite created.");
    } catch (err) {
      setError(err.message || "Unable to create invite");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceInviteRevoke(inviteId) {
    if (!selectedSpaceId) {
      return;
    }
    const busyKey = `space-invite-revoke-${inviteId}`;
    setSpacesBusyKey(busyKey);
    setError("");
    setNotice("");
    try {
      await revokeSpaceInvite(selectedSpaceId, inviteId);
      await loadSpaceDetail(selectedSpaceId);
      setNotice("Invite revoked.");
    } catch (err) {
      setError(err.message || "Unable to revoke invite");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceInviteCopy(token) {
    if (!token) {
      setError("Invite token is missing");
      return;
    }
    setError("");
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(token);
      }
      setNotice("Invite token copied.");
    } catch (_err) {
      setNotice(`Invite token: ${token}`);
    }
  }

  async function handleSpaceInviteAccept(event) {
    event.preventDefault();
    const token = String(spaceJoinForm.token || "").trim();
    if (!token) {
      setError("Invite token is required");
      return;
    }
    setSpacesBusyKey("space-invite-accept");
    setError("");
    setNotice("");
    try {
      const result = await acceptSpaceInvite({ token });
      const joinedSpaceId = result?.space?.id || null;
      setSpaceJoinForm({ token: "" });
      await loadSpaces(joinedSpaceId);
      setNotice(result?.message || "Joined space.");
    } catch (err) {
      setError(err.message || "Unable to accept invite");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceNotificationPreferenceSave(event) {
    event.preventDefault();
    if (!selectedSpaceId) {
      return;
    }
    setSpacesBusyKey("space-notification-preference-save");
    setError("");
    setNotice("");
    try {
      const result = await updateSpaceNotificationPreference(selectedSpaceId, {
        mode: spaceNotificationPreferenceMode
      });
      await Promise.all([loadSpaceDetail(selectedSpaceId), loadNotifications()]);
      const label =
        result?.preference?.label ||
        SPACE_NOTIFICATION_MODE_OPTIONS.find((option) => option.value === spaceNotificationPreferenceMode)?.label ||
        "Updated";
      setNotice(`Space reminder mode set to ${label}.`);
    } catch (err) {
      setError(err.message || "Unable to update space reminder mode");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceNotificationDefaultSave(event) {
    event.preventDefault();
    if (!selectedSpaceId || selectedSpace?.current_role !== "owner") {
      return;
    }
    setSpacesBusyKey("space-notification-default-save");
    setError("");
    setNotice("");
    try {
      const result = await updateSpaceNotificationDefault(selectedSpaceId, {
        mode: spaceNotificationDefaultMode
      });
      await Promise.all([loadSpaceDetail(selectedSpaceId), loadNotifications()]);
      const label =
        result?.default?.label ||
        SPACE_NOTIFICATION_MODE_OPTIONS.find((option) => option.value === spaceNotificationDefaultMode)?.label ||
        "Updated";
      setNotice(`New-member reminder default set to ${label}.`);
    } catch (err) {
      setError(err.message || "Unable to update new-member reminder default");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceNotificationDefaultApplyToMembers() {
    if (!selectedSpaceId || selectedSpace?.current_role !== "owner") {
      return;
    }
    const confirmed = window.confirm(
      "Apply this default reminder mode to all existing non-owner members in this space?"
    );
    if (!confirmed) {
      return;
    }

    setSpacesBusyKey("space-notification-default-apply");
    setError("");
    setNotice("");
    try {
      const result = await applySpaceNotificationDefaultToMembers(selectedSpaceId, { include_owner: false });
      await Promise.all([loadSpaceDetail(selectedSpaceId), loadNotifications()]);
      const summary = result?.summary || {};
      const applied = Number(summary.applied || 0);
      const unchanged = Number(summary.unchanged || 0);
      setNotice(
        `Applied default mode to ${applied} member${applied === 1 ? "" : "s"} (${unchanged} unchanged).`
      );
    } catch (err) {
      setError(err.message || "Unable to apply default mode to existing members");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceNotificationQuietHoursSave(event) {
    event.preventDefault();
    if (!selectedSpaceId || !canManageSpace) {
      return;
    }

    const startHour = normalizeQuietHour(
      spaceNotificationQuietHoursForm.start_hour_utc,
      Number(DEFAULT_SPACE_QUIET_HOURS.start_hour_utc)
    );
    const endHour = normalizeQuietHour(
      spaceNotificationQuietHoursForm.end_hour_utc,
      Number(DEFAULT_SPACE_QUIET_HOURS.end_hour_utc)
    );

    setSpacesBusyKey("space-notification-quiet-hours-save");
    setError("");
    setNotice("");
    try {
      const result = await updateSpaceNotificationQuietHours(selectedSpaceId, {
        enabled: Boolean(spaceNotificationQuietHoursForm.enabled),
        start_hour_utc: startHour,
        end_hour_utc: endHour
      });
      await Promise.all([loadSpaceDetail(selectedSpaceId), loadNotifications()]);
      const quietHours = result?.quiet_hours || {};
      if (quietHours.enabled) {
        setNotice(`Quiet hours enabled (${quietHours.window_label || `${startHour}:00-${endHour}:00 UTC`}).`);
      } else {
        setNotice("Quiet hours disabled for shared reminders.");
      }
    } catch (err) {
      setError(err.message || "Unable to update quiet hours");
    } finally {
      setSpacesBusyKey("");
    }
  }

  function handleSpaceTemplateEditChange(role, field, value) {
    setSpaceTemplateEdits((prev) => {
      const existing = prev[role] || {};
      return {
        ...prev,
        [role]: {
          ...existing,
          [field]: value
        }
      };
    });
  }

  async function handleSpaceTemplateSave(role) {
    if (!selectedSpaceId) {
      return;
    }
    const edit = spaceTemplateEdits[role];
    if (!edit) {
      return;
    }
    const busyKey = `space-template-save-${role}`;
    setSpacesBusyKey(busyKey);
    setError("");
    setNotice("");
    try {
      await updateSpaceRoleTemplate(selectedSpaceId, role, {
        display_name: edit.display_name,
        can_manage_space: Boolean(edit.can_manage_space),
        can_manage_members: Boolean(edit.can_manage_members),
        can_assign_admin: Boolean(edit.can_assign_admin),
        can_delete_space: Boolean(edit.can_delete_space),
        can_manage_invites: Boolean(edit.can_manage_invites),
        can_manage_tasks: Boolean(edit.can_manage_tasks),
        can_create_tasks: Boolean(edit.can_create_tasks),
        can_complete_tasks: Boolean(edit.can_complete_tasks)
      });
      await loadSpaceDetail(selectedSpaceId);
      setNotice(`${role} template updated.`);
    } catch (err) {
      setError(err.message || "Unable to update role template");
    } finally {
      setSpacesBusyKey("");
    }
  }

  function handleSpaceTaskEditChange(taskId, field, value) {
    setSpaceTaskEdits((prev) => {
      const existing = prev[taskId] || {};
      return {
        ...prev,
        [taskId]: {
          ...existing,
          [field]: value
        }
      };
    });
  }

  async function refreshAfterSpaceTaskXp() {
    await Promise.all([
      loadDashboard(),
      loadCrudData(),
      loadStats(statsRangeDays),
      loadNotifications(),
      loadShop(),
      loadInventory(),
      loadAchievements(),
      loadChallenges(),
      loadTimeline(timelineRangeDays),
      loadLeaderboard(leaderboardLimit, leaderboardScope),
      loadSeasonPass(),
      loadAvatar(),
      loadReminderChannels()
    ]);
  }

  async function handleSpaceTaskCreate(event) {
    event.preventDefault();
    if (!selectedSpaceId) {
      return;
    }
    setSpacesBusyKey("space-task-create");
    setError("");
    setNotice("");
    try {
      const result = await createSpaceTask(selectedSpaceId, {
        title: spaceTaskForm.title,
        task_type: spaceTaskForm.task_type,
        priority: spaceTaskForm.priority,
        xp_reward: Number(spaceTaskForm.xp_reward),
        due_on: spaceTaskForm.due_on || null
      });
      setSpaceTaskForm((prev) => ({ ...prev, title: "", due_on: "" }));
      await loadSpaceDetail(selectedSpaceId);
      if (result?.dashboard) {
        setDashboard(result.dashboard);
        await refreshAfterSpaceTaskXp();
      }
      setNotice(formatRewardNotice(result?.xp_gained, result?.coins_gained, "Shared task created."));
    } catch (err) {
      setError(err.message || "Unable to create shared task");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceTaskSave(taskId) {
    if (!selectedSpaceId) {
      return;
    }
    const edit = spaceTaskEdits[taskId];
    if (!edit) {
      return;
    }
    const busyKey = `space-task-save-${taskId}`;
    setSpacesBusyKey(busyKey);
    setError("");
    setNotice("");
    try {
      const result = await updateSpaceTask(selectedSpaceId, taskId, {
        title: edit.title,
        status: edit.status,
        task_type: edit.task_type,
        priority: edit.priority,
        xp_reward: Number(edit.xp_reward),
        due_on: edit.due_on || null
      });
      await loadSpaceDetail(selectedSpaceId);
      if (result?.dashboard) {
        setDashboard(result.dashboard);
        await refreshAfterSpaceTaskXp();
      }
      setNotice(formatRewardNotice(result?.xp_gained, result?.coins_gained, "Space task updated."));
    } catch (err) {
      setError(err.message || "Unable to update shared task");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceTaskDelete(taskId) {
    if (!selectedSpaceId) {
      return;
    }
    const busyKey = `space-task-delete-${taskId}`;
    setSpacesBusyKey(busyKey);
    setError("");
    setNotice("");
    try {
      await deleteSpaceTask(selectedSpaceId, taskId);
      await loadSpaceDetail(selectedSpaceId);
      setNotice("Shared task deleted.");
    } catch (err) {
      setError(err.message || "Unable to delete shared task");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleSpaceTaskComplete(taskId) {
    if (!selectedSpaceId) {
      return;
    }
    const busyKey = `space-task-complete-${taskId}`;
    setSpacesBusyKey(busyKey);
    setError("");
    setNotice("");
    try {
      const result = await completeSpaceTask(selectedSpaceId, taskId);
      if (result?.dashboard) {
        setDashboard(result.dashboard);
      }
      await Promise.all([loadSpaceDetail(selectedSpaceId), refreshAfterSpaceTaskXp()]);
      setNotice(formatRewardNotice(result?.xp_gained, result?.coins_gained, "Shared task completed."));
    } catch (err) {
      setError(err.message || "Unable to complete shared task");
    } finally {
      setSpacesBusyKey("");
    }
  }

  async function handleShopPurchase(itemKey) {
    if (!itemKey) {
      return;
    }
    const busyKey = `shop-buy-${itemKey}`;
    setShopBusyKey(busyKey);
    setError("");
    setNotice("");
    try {
      const result = await purchaseShopItem(itemKey);
      if (result?.user) {
        setAuthUser(result.user);
      }
      if (result?.dashboard) {
        setDashboard(result.dashboard);
      }
      if (result?.shop) {
        setShopData(result.shop);
      }
      if (result?.inventory) {
        setInventoryData(result.inventory);
      }
      if (result?.season_pass) {
        setSeasonPassData(result.season_pass);
      }
      if (result?.avatar) {
        setAvatarData(result.avatar);
      }
      if (result?.achievements) {
        setAchievementsData(result.achievements);
      }
      if (result?.challenges) {
        setChallengesData(result.challenges);
      }
      await Promise.all([
        loadShop(),
        loadInventory(),
        loadAchievements(),
        loadChallenges(),
        loadTimeline(timelineRangeDays),
        loadLeaderboard(leaderboardLimit, leaderboardScope),
        loadSeasonPass(),
        loadAvatar(),
        loadStats(statsRangeDays),
        loadNotifications(),
        loadReminderChannels()
      ]);
      const spent = Number(result?.coins_spent || 0);
      const baseMessage = result?.message || "Purchase complete";
      setNotice(spent > 0 ? `${baseMessage} (-${prettyNumber(spent)} coins).` : baseMessage);
    } catch (err) {
      setError(err.message || "Unable to complete purchase");
    } finally {
      setShopBusyKey("");
    }
  }

  async function handleInventoryRewardRedeem(purchaseId) {
    if (!purchaseId) {
      return;
    }
    const busyKey = `inventory-redeem-${purchaseId}`;
    setInventoryRedeemBusyKey(busyKey);
    setError("");
    setNotice("");
    try {
      const result = await redeemInventoryPurchase(purchaseId);
      if (result?.dashboard) {
        setDashboard(result.dashboard);
      }
      if (result?.inventory) {
        setInventoryData(result.inventory);
      }
      if (result?.achievements) {
        setAchievementsData(result.achievements);
      }
      await Promise.all([
        loadInventory(),
        loadAchievements(),
        loadChallenges(),
        loadTimeline(timelineRangeDays),
        loadLeaderboard(leaderboardLimit, leaderboardScope),
        loadSeasonPass(),
        loadShop(),
        loadAvatar(),
        loadStats(statsRangeDays),
        loadNotifications(),
        loadReminderChannels()
      ]);
      setNotice(formatRewardNotice(result?.xp_gained, result?.coins_gained, result?.message || "Reward redeemed."));
    } catch (err) {
      setError(err.message || "Unable to redeem reward");
    } finally {
      setInventoryRedeemBusyKey("");
    }
  }

  async function handleChallengeClaim(windowType, challengeKey) {
    if (!windowType || !challengeKey) {
      return;
    }
    const busyKey = `challenge-claim-${windowType}-${challengeKey}`;
    setChallengeBusyKey(busyKey);
    setError("");
    setNotice("");
    try {
      const result = await claimChallengeReward({ window_type: windowType, challenge_key: challengeKey });
      if (result?.dashboard) {
        setDashboard(result.dashboard);
      }
      if (result?.challenges) {
        setChallengesData(result.challenges);
      }
      if (result?.achievements) {
        setAchievementsData(result.achievements);
      }
      await Promise.all([
        loadDashboard(),
        loadChallenges(),
        loadAchievements(),
        loadTimeline(timelineRangeDays),
        loadLeaderboard(leaderboardLimit, leaderboardScope),
        loadSeasonPass(),
        loadShop(),
        loadInventory(),
        loadAvatar(),
        loadStats(statsRangeDays),
        loadNotifications(),
        loadReminderChannels()
      ]);
      setNotice(
        formatRewardNotice(
          result?.claim?.reward_xp,
          result?.claim?.reward_coins,
          result?.message || "Challenge reward claimed."
        )
      );
    } catch (err) {
      setError(err.message || "Unable to claim challenge reward");
    } finally {
      setChallengeBusyKey("");
    }
  }

  async function handleSeasonPassTierClaim(tier, track = "free") {
    const safeTier = Number(tier);
    if (!Number.isFinite(safeTier) || safeTier < 1) {
      return;
    }
    const safeTrack = String(track || "free").trim().toLowerCase() === "premium" ? "premium" : "free";
    const busyKey = `season-pass-claim-${safeTier}-${safeTrack}`;
    setSeasonPassBusyKey(busyKey);
    setError("");
    setNotice("");
    try {
      const result = await claimSeasonPassTier(safeTier, safeTrack);
      if (result?.dashboard) {
        setDashboard(result.dashboard);
      }
      if (result?.season_pass) {
        setSeasonPassData(result.season_pass);
      }
      if (result?.leaderboard && String(result.leaderboard.scope || "global") === String(leaderboardScope || "global")) {
        setLeaderboardData(result.leaderboard);
      }
      if (result?.achievements) {
        setAchievementsData(result.achievements);
      }
      await Promise.all([
        loadDashboard(),
        loadSeasonPass(),
        loadLeaderboard(leaderboardLimit, leaderboardScope),
        loadAchievements(),
        loadChallenges(),
        loadTimeline(timelineRangeDays),
        loadShop(),
        loadInventory(),
        loadAvatar(),
        loadStats(statsRangeDays),
        loadNotifications(),
        loadReminderChannels()
      ]);
      setNotice(
        formatRewardNotice(
          result?.claim?.reward_xp,
          result?.claim?.reward_coins,
          result?.message || `Season pass ${safeTrack} tier claimed.`
        )
      );
    } catch (err) {
      setError(err.message || "Unable to claim season pass tier");
    } finally {
      setSeasonPassBusyKey("");
    }
  }

  async function handleAvatarOptionSelect(slot, optionKey) {
    if (!slot || !optionKey) {
      return;
    }
    const busyKey = `avatar-${slot}-${optionKey}`;
    setAvatarBusyKey(busyKey);
    setError("");
    setNotice("");
    try {
      const result = await updateAvatar({ [slot]: optionKey });
      if (result?.dashboard) {
        setDashboard(result.dashboard);
      }
      setAvatarData(result);
      setAvatarPreviewSetKey("");
      await loadShop();
      setNotice(result?.message || "Avatar updated");
    } catch (err) {
      setError(err.message || "Unable to update avatar");
    } finally {
      setAvatarBusyKey("");
    }
  }

  async function handleAvatarSetApply(setPreset) {
    const presetSlots = setPreset?.slots && typeof setPreset.slots === "object" ? setPreset.slots : null;
    if (!setPreset?.key || !presetSlots) {
      return;
    }
    const busyKey = `avatar-set-${setPreset.key}`;
    setAvatarBusyKey(busyKey);
    setError("");
    setNotice("");
    try {
      const result = await updateAvatar(presetSlots);
      if (result?.dashboard) {
        setDashboard(result.dashboard);
      }
      setAvatarData(result);
      setAvatarPreviewSetKey("");
      await loadShop();
      setNotice(result?.message || `${setPreset.label || "Avatar set"} equipped`);
    } catch (err) {
      setError(err.message || "Unable to apply avatar set");
    } finally {
      setAvatarBusyKey("");
    }
  }

  function handleAvatarSetPreview(setKey) {
    const normalizedSetKey = String(setKey || "").trim().toLowerCase();
    if (!normalizedSetKey) {
      setAvatarPreviewSetKey("");
      return;
    }
    setAvatarPreviewSetKey((currentKey) => (currentKey === normalizedSetKey ? "" : normalizedSetKey));
  }

  async function handleAvatarSetQuickPurchase(itemKey, setKey, mode = "bundle") {
    const normalizedItemKey = String(itemKey || "").trim();
    if (!normalizedItemKey) {
      handleAvatarSetShopOpen(setKey, mode);
      return;
    }
    await handleShopPurchase(normalizedItemKey);
  }

  function handleAvatarSetShopOpen(setKey, mode = "bundle") {
    const normalizedSetKey = String(setKey || "").trim().toLowerCase();
    const normalizedMode = mode === "parts" ? "parts" : "bundle";
    setShopSearchQuery("");
    setShopCategoryFilter("avatar");
    setShopOwnershipFilter("all");
    setShopAvatarViewFilter(normalizedMode === "parts" ? "set_parts" : "set_bundles");
    setShopAvatarSetFilter(normalizedSetKey || "all");
    setShopHighlightSetKey(normalizedSetKey);
    setShopHighlightMode(normalizedMode);
    setShopHighlightScrollToken((value) => value + 1);
    setNotice("");
    setError("");
    navigate("/shop");
    setMobileSidebarOpen(false);
  }

  async function handleLeaderboardLimitChange(nextLimit) {
    const safeLimit = Number(nextLimit);
    const normalizedLimit = Number.isFinite(safeLimit) ? Math.max(3, Math.min(Math.round(safeLimit), 50)) : 15;
    setLeaderboardLimit(normalizedLimit);
    await loadLeaderboard(normalizedLimit, leaderboardScope);
  }

  async function handleLeaderboardScopeChange(nextScope) {
    const scopeKey = String(nextScope || "").trim().toLowerCase();
    const isKnown = LEADERBOARD_SCOPE_OPTIONS.some((option) => option.key === scopeKey);
    const normalizedScope = isKnown ? scopeKey : "global";
    setLeaderboardScope(normalizedScope);
    await loadLeaderboard(leaderboardLimit, normalizedScope);
  }

  async function handleLogout() {
    try {
      await logoutUser();
    } finally {
      clearAuthToken();
      setAuthUser(null);
      setDashboard(null);
      setTaskRows([]);
      setHabitRows([]);
      setGoalRows([]);
      setRecurringRows([]);
      setSpaceRows([]);
      setSpaceDetails(null);
      setSelectedSpaceId(null);
      setStatsData(null);
      setNotificationsData(null);
      setShopData(null);
      setShopBusyKey("");
      setShopLoading(false);
      setShopSearchQuery("");
      setShopCategoryFilter("all");
      setShopOwnershipFilter("all");
      setShopAvatarViewFilter("all");
      setShopAvatarSetFilter("all");
      setShopHighlightSetKey("");
      setShopHighlightMode("");
      setShopHighlightScrollToken(0);
      setInventoryData(null);
      setInventoryRedeemBusyKey("");
      setInventoryLoading(false);
      setInventoryCategoryFilter("all");
      setInventoryTypeFilter("all");
      setAchievementsData(null);
      setAchievementsLoading(false);
      setChallengesData(null);
      setChallengesLoading(false);
      setChallengeBusyKey("");
      setTimelineData(null);
      setTimelineLoading(false);
      setTimelineRangeDays(30);
      setLeaderboardData(null);
      setLeaderboardLoading(false);
      setLeaderboardLimit(15);
      setLeaderboardScope("global");
      setLeaderboardBoardKey("xp_7d");
      setSeasonPassData(null);
      setSeasonPassLoading(false);
      setSeasonPassBusyKey("");
      setAvatarData(null);
      setAvatarBusyKey("");
      setAvatarLoading(false);
      setAvatarPreviewSetKey("");
      setAvatarSetFilter("all");
      setAvatarSetSort("completion_desc");
      setReminderSettingsLoading(false);
      setReminderDeliveries([]);
      setReminderProviders({ email: "console", sms: "console" });
      setXpRules({});
      setTaskEdits({});
      setHabitEdits({});
      setGoalEdits({});
      setRecurringBusyKey("");
      setRecurringForm({
        title: "",
        task_type: "task",
        priority: "medium",
        xp_reward: 20,
        frequency: "daily",
        interval: 1,
        days_of_week: [0],
        active: true
      });
      setRecurringRunBackfill(1);
      setSpaceForm({ name: "" });
      setSpaceRenameForm({ name: "" });
      setSpaceMemberForm({ identifier: "", role: "member" });
      setSpaceInviteForm({ role: "member", expires_in_hours: 72 });
      setSpaceJoinForm({ token: "" });
      setSpaceNotificationPreferenceMode("all");
      setSpaceNotificationDefaultMode("all");
      setSpaceNotificationQuietHoursForm({
        enabled: Boolean(DEFAULT_SPACE_QUIET_HOURS.enabled),
        start_hour_utc: Number(DEFAULT_SPACE_QUIET_HOURS.start_hour_utc),
        end_hour_utc: Number(DEFAULT_SPACE_QUIET_HOURS.end_hour_utc)
      });
      setSpaceTemplateEdits({});
      setSpaceTaskForm({
        title: "",
        task_type: "task",
        priority: "medium",
        xp_reward: 25,
        due_on: ""
      });
      setSpaceTaskEdits({});
      setTaskSearchQuery("");
      setTaskStatusFilter("all");
      setTaskTypeFilter("all");
      setTaskPriorityFilter("all");
      setTaskSortMode("due_asc");
      setHabitSearchQuery("");
      setHabitStreakFilter("all");
      setHabitSortMode("created_desc");
      setGoalSearchQuery("");
      setGoalStatusFilter("all");
      setGoalSortMode("created_desc");
      setReminderSettingsForm({
        in_app_enabled: true,
        email_enabled: false,
        sms_enabled: false,
        email_address: "",
        phone_number: "",
        digest_hour_utc: 14
      });
      setReminderTestForm({ channel: "all", message: "" });
      setSpacesBusyKey("");
      setProfileForm({ display_name: "", username: "", email: "" });
      setPasswordForm({ current_password: "", new_password: "", confirm_new_password: "" });
      setImportForm({ mode: "merge", apply_profile: false, snapshot_text: "" });
      setSpaceImportForm({ mode: "merge", snapshot_text: "", confirmation_phrase: "" });
      setSpaceImportPreview(null);
      setSpaceReplaceConfirmOpen(false);
      setSpaceAuditForm({ ...SPACE_AUDIT_FILTER_DEFAULT });
      setSpaceAuditRows([]);
      setSpaceAuditSummary(normalizeSpaceAuditSummary(null));
      setSpaceAuditAvailableEventTypes([]);
      setSpaceAuditLoading(false);
      setSettingsBusyKey("");
      navigate("/dashboard", { replace: true });
      setNotice("");
      setError("");
    }
  }

  const levelPercent = useMemo(() => {
    if (!dashboard) {
      return 0;
    }
    const base = Math.max(dashboard.user.xp_for_next_level, 1);
    return Math.round((dashboard.user.xp_into_level / base) * 100);
  }, [dashboard]);

  const xpRuleEntries = useMemo(
    () => Object.entries(xpRules).sort(([left], [right]) => left.localeCompare(right)),
    [xpRules]
  );

  const statsSummary = statsData?.summary || null;
  const statsGoalStatus = statsData?.goal_status || null;
  const statsXpRows = statsData?.xp_by_day || [];
  const statsCompletionRows = statsData?.completion_by_day || [];
  const statsTaskTypeRows = statsData?.task_type_breakdown || [];
  const statsXpSourceRows = statsData?.xp_source_breakdown || [];
  const notificationItems = notificationsData?.items || [];
  const notificationCounts = notificationsData?.counts || {
    total: 0,
    overdue_tasks: 0,
    streak_risk_habits: 0,
    goals_due_soon: 0,
    space_updates: 0,
    space_invites_expiring: 0
  };
  const todayStartTimestamp = getDayStartTimestamp();
  const coinBalance = Number(dashboard?.user?.coins ?? shopData?.coins_balance ?? authUser?.coins ?? 0);
  const shopRotation = shopData?.rotation || null;
  const shopResetLabel = useMemo(
    () => formatCountdownLabel(shopRotation?.seconds_until_reset),
    [shopRotation?.seconds_until_reset]
  );
  const shopItems = Array.isArray(shopData?.items) ? shopData.items : [];
  const shopAvatarSetOptions = useMemo(() => {
    const rowsByKey = {};
    shopItems.forEach((item) => {
      const category = String(item?.category || "").trim().toLowerCase();
      if (category !== "avatar") {
        return;
      }
      const setKey = String(item?.set_key || item?.unlock_set_key || "").trim().toLowerCase();
      if (!setKey) {
        return;
      }
      const setLabel = String(item?.set_label || humanizeKey(setKey)).trim() || humanizeKey(setKey);
      if (!rowsByKey[setKey]) {
        rowsByKey[setKey] = { key: setKey, label: setLabel, count: 0 };
      }
      rowsByKey[setKey].count += 1;
    });
    const rows = Object.values(rowsByKey).sort((left, right) => String(left.label).localeCompare(String(right.label)));
    return [{ key: "all", label: "All sets" }].concat(
      rows.map((row) => ({
        key: row.key,
        label: `${row.label} (${prettyNumber(row.count)})`
      }))
    );
  }, [shopItems]);
  const shopHighlightSetLabel = useMemo(() => {
    if (!shopHighlightSetKey) {
      return "";
    }
    const option = shopAvatarSetOptions.find((row) => row.key === shopHighlightSetKey);
    const optionLabel = String(option?.label || "").replace(/\s+\(\d+\)\s*$/, "").trim();
    if (optionLabel) {
      return optionLabel;
    }
    return humanizeKey(shopHighlightSetKey);
  }, [shopAvatarSetOptions, shopHighlightSetKey]);
  const shopAvatarSetPartTotals = useMemo(() => {
    const totals = {};
    shopItems.forEach((item) => {
      const rewardType = String(item?.reward_type || "").trim().toLowerCase();
      const setKey = String(item?.set_key || "").trim().toLowerCase();
      if (rewardType !== "avatar_unlock" || !setKey) {
        return;
      }
      totals[setKey] = Number(totals[setKey] || 0) + Math.max(Number(item?.price_coins || 0), 0);
    });
    return totals;
  }, [shopItems]);
  const avatarSetBundleItemsByKey = useMemo(() => {
    const rows = {};
    shopItems.forEach((item) => {
      const category = String(item?.category || "").trim().toLowerCase();
      const rewardType = String(item?.reward_type || "").trim().toLowerCase();
      if (category !== "avatar" || rewardType !== "avatar_set_unlock") {
        return;
      }
      const setKey = String(item?.set_key || item?.unlock_set_key || "").trim().toLowerCase();
      if (!setKey) {
        return;
      }
      rows[setKey] = item;
    });
    return rows;
  }, [shopItems]);
  const avatarSetPartItemsByKey = useMemo(() => {
    const rows = {};
    shopItems.forEach((item) => {
      const category = String(item?.category || "").trim().toLowerCase();
      const rewardType = String(item?.reward_type || "").trim().toLowerCase();
      if (category !== "avatar" || rewardType !== "avatar_unlock") {
        return;
      }
      const setKey = String(item?.set_key || "").trim().toLowerCase();
      if (!setKey) {
        return;
      }
      if (!rows[setKey]) {
        rows[setKey] = [];
      }
      rows[setKey].push(item);
    });
    Object.values(rows).forEach((itemRows) => {
      itemRows.sort((left, right) => {
        const leftSlot = String(left?.unlock_slot || "");
        const rightSlot = String(right?.unlock_slot || "");
        if (leftSlot !== rightSlot) {
          return leftSlot.localeCompare(rightSlot);
        }
        const leftPrice = Number(left?.price_coins || 0);
        const rightPrice = Number(right?.price_coins || 0);
        if (leftPrice !== rightPrice) {
          return leftPrice - rightPrice;
        }
        return String(left?.title || "").localeCompare(String(right?.title || ""));
      });
    });
    return rows;
  }, [shopItems]);
  const filteredShopItems = useMemo(() => {
    const query = String(shopSearchQuery || "").trim().toLowerCase();
    const avatarSpecificFilterActive = shopAvatarViewFilter !== "all" || shopAvatarSetFilter !== "all";
    const applyAvatarSpecificFilter = avatarSpecificFilterActive && (shopCategoryFilter === "all" || shopCategoryFilter === "avatar");
    return shopItems.filter((item) => {
      const category = String(item?.category || "").trim().toLowerCase();
      const rewardType = String(item?.reward_type || "").trim().toLowerCase();
      const setKey = String(item?.set_key || item?.unlock_set_key || "").trim().toLowerCase();
      const setLabel = String(item?.set_label || "").trim().toLowerCase();
      const title = String(item?.title || "").trim().toLowerCase();
      const description = String(item?.description || "").trim().toLowerCase();
      const categoryLabel = String(item?.category_label || "").trim().toLowerCase();
      const owned = Boolean(item?.owned);

      if (shopCategoryFilter !== "all" && category !== shopCategoryFilter) {
        return false;
      }
      if (shopOwnershipFilter === "owned" && !owned) {
        return false;
      }
      if (shopOwnershipFilter === "unowned" && owned) {
        return false;
      }
      if (applyAvatarSpecificFilter && category !== "avatar") {
        return false;
      }
      if (category === "avatar") {
        if (shopAvatarViewFilter === "set_bundles" && rewardType !== "avatar_set_unlock") {
          return false;
        }
        if (shopAvatarViewFilter === "set_parts" && !(rewardType === "avatar_unlock" && Boolean(setKey))) {
          return false;
        }
        if (shopAvatarViewFilter === "single_unlocks" && !(rewardType === "avatar_unlock" && !setKey)) {
          return false;
        }
        if (shopAvatarSetFilter !== "all" && setKey !== shopAvatarSetFilter) {
          return false;
        }
      }
      if (!query) {
        return true;
      }
      const searchBlob = `${title} ${description} ${categoryLabel} ${rewardType} ${setLabel} ${setKey}`;
      return searchBlob.includes(query);
    });
  }, [shopItems, shopSearchQuery, shopCategoryFilter, shopOwnershipFilter, shopAvatarViewFilter, shopAvatarSetFilter]);
  const shopCategoryRows = useMemo(() => {
    const grouped = {};
    filteredShopItems.forEach((item) => {
      const categoryKey = item?.category || "shop";
      if (!grouped[categoryKey]) {
        grouped[categoryKey] = {
          key: categoryKey,
          label: item?.category_label || categoryKey.replace(/_/g, " "),
          items: []
        };
      }
      grouped[categoryKey].items.push(item);
    });
    return Object.values(grouped)
      .map((group) => ({
        ...group,
        items: [...group.items].sort((left, right) => {
          const leftAvailable = left?.available_today === false ? 1 : 0;
          const rightAvailable = right?.available_today === false ? 1 : 0;
          if (leftAvailable !== rightAvailable) {
            return leftAvailable - rightAvailable;
          }
          const leftOwned = left?.owned ? 1 : 0;
          const rightOwned = right?.owned ? 1 : 0;
          if (leftOwned !== rightOwned) {
            return leftOwned - rightOwned;
          }
          const leftPrice = Number(left?.price_coins || 0);
          const rightPrice = Number(right?.price_coins || 0);
          if (leftPrice !== rightPrice) {
            return leftPrice - rightPrice;
          }
          return String(left?.title || "").localeCompare(String(right?.title || ""));
        })
      }))
      .sort((left, right) => String(left.label).localeCompare(String(right.label)));
  }, [filteredShopItems]);
  const shopFilterActive = Boolean(
    String(shopSearchQuery || "").trim() ||
      shopCategoryFilter !== "all" ||
      shopOwnershipFilter !== "all" ||
      shopAvatarViewFilter !== "all" ||
      shopAvatarSetFilter !== "all"
  );
  const inventorySummary = inventoryData?.summary || null;
  const inventoryFilters = inventoryData?.filters || {};
  const inventoryCategoryOptions = useMemo(() => {
    const base = [{ key: "all", label: "All Categories" }];
    const rows = Array.isArray(inventoryFilters?.categories) ? inventoryFilters.categories : [];
    return base.concat(
      rows.map((row) => ({
        key: String(row?.key || "").trim().toLowerCase() || "shop",
        label: String(row?.label || row?.key || "Category")
      }))
    );
  }, [inventoryFilters?.categories]);
  const inventoryTypeOptions = useMemo(() => {
    const base = [{ key: "all", label: "All Types" }];
    const rows = Array.isArray(inventoryFilters?.reward_types) ? inventoryFilters.reward_types : [];
    return base.concat(
      rows.map((row) => ({
        key: String(row?.key || "").trim().toLowerCase() || "self_reward",
        label: String(row?.label || row?.key || "Type")
      }))
    );
  }, [inventoryFilters?.reward_types]);
  const inventoryHistoryRows = Array.isArray(inventoryData?.purchase_history) ? inventoryData.purchase_history : [];
  const inventoryAvatarUnlockRows = Array.isArray(inventoryData?.avatar_unlocks) ? inventoryData.avatar_unlocks : [];
  const inventoryRewardRows = Array.isArray(inventoryData?.reward_redemptions) ? inventoryData.reward_redemptions : [];
  const inventorySpendingRows = Array.isArray(inventoryData?.spending_by_day) ? inventoryData.spending_by_day : [];
  const filteredInventoryRows = useMemo(() => {
    return inventoryHistoryRows.filter((row) => {
      const category = String(row?.category || "").trim().toLowerCase();
      const rewardType = String(row?.reward_type || "").trim().toLowerCase();
      if (inventoryCategoryFilter !== "all" && category !== inventoryCategoryFilter) {
        return false;
      }
      if (inventoryTypeFilter !== "all" && rewardType !== inventoryTypeFilter) {
        return false;
      }
      return true;
    });
  }, [inventoryCategoryFilter, inventoryHistoryRows, inventoryTypeFilter]);
  const achievementsSummary = achievementsData?.summary || {
    total: 0,
    unlocked: 0,
    locked: 0,
    completion_rate: 0,
    newly_unlocked: 0
  };
  const achievementRows = Array.isArray(achievementsData?.items) ? achievementsData.items : [];
  const recentAchievementUnlocks = Array.isArray(achievementsData?.recent_unlocks) ? achievementsData.recent_unlocks : [];
  const challengeSummary = challengesData?.summary || {
    total: 0,
    completed: 0,
    claimable: 0
  };
  const dailyChallengeWindow = challengesData?.daily || null;
  const weeklyChallengeWindow = challengesData?.weekly || null;
  const challengeWindows = [dailyChallengeWindow, weeklyChallengeWindow].filter((row) => row && typeof row === "object");
  const timelineRange = timelineData?.range || null;
  const timelineSummary = timelineData?.summary || { event_count: 0, active_days: 0 };
  const timelineDayBuckets = Array.isArray(timelineData?.day_buckets) ? timelineData.day_buckets : [];
  const timelineEvents = Array.isArray(timelineData?.events) ? timelineData.events : [];
  const leaderboardBoards = Array.isArray(leaderboardData?.boards) ? leaderboardData.boards : [];
  const activeLeaderboardBoard = useMemo(() => {
    if (!leaderboardBoards.length) {
      return null;
    }
    const selectedBoard = leaderboardBoards.find((board) => board?.key === leaderboardBoardKey);
    return selectedBoard || leaderboardBoards[0];
  }, [leaderboardBoardKey, leaderboardBoards]);
  const activeLeaderboardEntries = Array.isArray(activeLeaderboardBoard?.entries) ? activeLeaderboardBoard.entries : [];
  const leaderboardScopeLabel = String(leaderboardData?.scope_label || (leaderboardScope === "network" ? "Network" : "Global"));
  const leaderboardScopeUserCount = Math.max(Number(leaderboardData?.scope_user_count || 0), 0);
  const seasonPassSeason = seasonPassData?.season || null;
  const seasonPassSummary = seasonPassData?.summary || {
    xp_per_tier: 300,
    max_tier: 20,
    current_tier: 1,
    xp_earned: 0,
    xp_into_tier: 0,
    xp_needed_for_next_tier: 0,
    progress_percent: 0,
    premium_enabled: false,
    claimable: 0,
    claimable_free: 0,
    claimable_premium: 0,
    claimed: 0,
    claimed_free: 0,
    claimed_premium: 0
  };
  const seasonPassPremiumEnabled = Boolean(
    seasonPassSummary.premium_enabled ?? seasonPassSeason?.premium_enabled ?? authUser?.season_pass_premium
  );
  const seasonPassTiers = Array.isArray(seasonPassData?.tiers) ? seasonPassData.tiers : [];
  const seasonPassVisibleTiers = useMemo(() => {
    const currentTier = Number(seasonPassSummary?.current_tier || 1);
    return seasonPassTiers.filter((tierRow) => {
      const tier = Number(tierRow?.tier || 0);
      const freeTrack = tierRow?.free && typeof tierRow.free === "object" ? tierRow.free : {};
      const premiumTrack = tierRow?.premium && typeof tierRow.premium === "object" ? tierRow.premium : {};
      const hasClaimable = Boolean(freeTrack.claimable || premiumTrack.claimable);
      const hasClaimed = Boolean(freeTrack.claimed || premiumTrack.claimed);
      return tier <= currentTier + 4 || hasClaimable || hasClaimed;
    });
  }, [seasonPassSummary?.current_tier, seasonPassTiers]);
  const avatarProfile = avatarData?.avatar || null;
  const avatarOptions = avatarData?.options || {};
  const avatarSetPresets = useMemo(() => {
    const rows = Array.isArray(avatarData?.set_presets) ? avatarData.set_presets : [];
    return [...rows].sort((left, right) => {
      const leftLocked = left?.unlocked ? 0 : 1;
      const rightLocked = right?.unlocked ? 0 : 1;
      if (leftLocked !== rightLocked) {
        return leftLocked - rightLocked;
      }
      return String(left?.label || "").localeCompare(String(right?.label || ""));
    });
  }, [avatarData?.set_presets]);
  const avatarSetRows = useMemo(() => {
    return avatarSetPresets.map((preset, presetIndex) => {
      const presetKeyRaw = String(preset?.key || "").trim();
      const presetKey = presetKeyRaw.toLowerCase();
      const presetSlots = preset?.slots && typeof preset.slots === "object" ? preset.slots : {};
      const missingSlotsRaw = Array.isArray(preset?.missing_slots) ? preset.missing_slots : [];
      const missingSlots = missingSlotsRaw.map((slot) => String(slot || "").trim().toLowerCase()).filter(Boolean);
      const locked = !preset?.unlocked;
      const missingSlotCount = missingSlots.length;
      const totalSlotCount = Object.keys(presetSlots).length;
      const unlockedSlotCount = Math.max(totalSlotCount - missingSlotCount, 0);
      const completionPercent = totalSlotCount > 0 ? Math.round((unlockedSlotCount / totalSlotCount) * 100) : 0;
      const previewing = Boolean(presetKey && avatarPreviewSetKey === presetKey);
      const equipped = Boolean(
        presetKey &&
          avatarProfile &&
          Object.entries(presetSlots).every(([slot, value]) => avatarProfile?.[slot] === value)
      );
      const setBundleItem = avatarSetBundleItemsByKey[presetKey] || null;
      const setPartItems = avatarSetPartItemsByKey[presetKey] || [];
      const setPartTotal = Number(shopAvatarSetPartTotals[presetKey] || 0);
      const bundlePrice = Math.max(Number(setBundleItem?.price_coins || 0), 0);
      const bundleSavings = setBundleItem ? Math.max(setPartTotal - bundlePrice, 0) : 0;
      const missingSlotSet = new Set(missingSlots);
      const missingPartItems = setPartItems.filter((item) => {
        const unlockSlot = String(item?.unlock_slot || "").trim().toLowerCase();
        return Boolean(unlockSlot) && missingSlotSet.has(unlockSlot) && !Boolean(item?.owned);
      });
      const nextMissingPart =
        [...missingPartItems].sort((left, right) => {
          const leftUnavailable = left?.can_purchase_today === false ? 1 : 0;
          const rightUnavailable = right?.can_purchase_today === false ? 1 : 0;
          if (leftUnavailable !== rightUnavailable) {
            return leftUnavailable - rightUnavailable;
          }
          const leftUnaffordable = left?.coin_affordable === false ? 1 : 0;
          const rightUnaffordable = right?.coin_affordable === false ? 1 : 0;
          if (leftUnaffordable !== rightUnaffordable) {
            return leftUnaffordable - rightUnaffordable;
          }
          const leftPrice = Number(left?.price_coins || 0);
          const rightPrice = Number(right?.price_coins || 0);
          if (leftPrice !== rightPrice) {
            return leftPrice - rightPrice;
          }
          return String(left?.title || "").localeCompare(String(right?.title || ""));
        })[0] || null;
      const nextPartSlotKey = String(nextMissingPart?.unlock_slot || "").trim().toLowerCase();
      const nextPartSlotLabel = AVATAR_SLOT_LABELS[nextPartSlotKey] || humanizeKey(nextPartSlotKey || "part");
      const bundleQuickBuyReady = Boolean(
        setBundleItem &&
          !setBundleItem?.owned &&
          setBundleItem?.can_purchase_today !== false &&
          setBundleItem?.coin_affordable !== false
      );
      const nextPartQuickBuyReady = Boolean(
        nextMissingPart &&
          nextMissingPart?.can_purchase_today !== false &&
          nextMissingPart?.coin_affordable !== false
      );
      return {
        preset,
        presetIndex,
        presetKey,
        locked,
        missingSlotCount,
        totalSlotCount,
        unlockedSlotCount,
        completionPercent,
        previewing,
        equipped,
        setBundleItem,
        bundlePrice,
        bundleSavings,
        nextMissingPart,
        nextPartSlotLabel,
        bundleQuickBuyReady,
        nextPartQuickBuyReady
      };
    });
  }, [
    avatarPreviewSetKey,
    avatarProfile,
    avatarSetBundleItemsByKey,
    avatarSetPartItemsByKey,
    avatarSetPresets,
    shopAvatarSetPartTotals
  ]);
  const avatarVisibleSetRows = useMemo(() => {
    const rows = avatarSetRows.filter((row) => {
      if (avatarSetFilter === "locked") {
        return row.locked;
      }
      if (avatarSetFilter === "unlocked") {
        return !row.locked;
      }
      if (avatarSetFilter === "active") {
        return row.equipped;
      }
      if (avatarSetFilter === "previewing") {
        return row.previewing;
      }
      if (avatarSetFilter === "affordable") {
        return row.bundleQuickBuyReady || row.nextPartQuickBuyReady;
      }
      return true;
    });
    const sortedRows = [...rows];
    sortedRows.sort((left, right) => {
      if (avatarSetSort === "completion_asc" && left.completionPercent !== right.completionPercent) {
        return left.completionPercent - right.completionPercent;
      }
      if (avatarSetSort === "bundle_price_asc") {
        const leftPrice = left.setBundleItem ? left.bundlePrice : Number.MAX_SAFE_INTEGER;
        const rightPrice = right.setBundleItem ? right.bundlePrice : Number.MAX_SAFE_INTEGER;
        if (leftPrice !== rightPrice) {
          return leftPrice - rightPrice;
        }
      }
      if (avatarSetSort === "savings_desc" && left.bundleSavings !== right.bundleSavings) {
        return right.bundleSavings - left.bundleSavings;
      }
      if (avatarSetSort === "label_asc") {
        return String(left.preset?.label || left.presetKey).localeCompare(String(right.preset?.label || right.presetKey));
      }
      if (left.completionPercent !== right.completionPercent) {
        return right.completionPercent - left.completionPercent;
      }
      return String(left.preset?.label || left.presetKey).localeCompare(String(right.preset?.label || right.presetKey));
    });
    return sortedRows;
  }, [avatarSetFilter, avatarSetRows, avatarSetSort]);
  const avatarUnlockedSetCount = avatarSetRows.filter((row) => !row.locked).length;
  const avatarSetFilterActive = avatarSetFilter !== "all" || avatarSetSort !== "completion_desc";
  const avatarOptionSlots = useMemo(() => {
    const rows = Object.entries(avatarOptions || {});
    rows.sort(([leftSlot], [rightSlot]) => {
      const leftIndex = AVATAR_SLOT_ORDER.indexOf(leftSlot);
      const rightIndex = AVATAR_SLOT_ORDER.indexOf(rightSlot);
      const safeLeft = leftIndex === -1 ? Number.MAX_SAFE_INTEGER : leftIndex;
      const safeRight = rightIndex === -1 ? Number.MAX_SAFE_INTEGER : rightIndex;
      if (safeLeft !== safeRight) {
        return safeLeft - safeRight;
      }
      return leftSlot.localeCompare(rightSlot);
    });
    return rows;
  }, [avatarOptions]);
  const avatarOptionLookup = useMemo(() => {
    const rows = {};
    for (const [slot, options] of Object.entries(avatarOptions || {})) {
      rows[slot] = Object.fromEntries((Array.isArray(options) ? options : []).map((option) => [option.key, option]));
    }
    return rows;
  }, [avatarOptions]);
  const avatarSelectedLabelBySlot = useMemo(() => {
    if (!avatarProfile) {
      return {};
    }
    const rows = {};
    for (const [slot, value] of Object.entries(avatarProfile)) {
      if (slot === "updated_at") {
        continue;
      }
      const optionLabel = avatarOptionLookup?.[slot]?.[value]?.label;
      rows[slot] = optionLabel || humanizeKey(value);
    }
    return rows;
  }, [avatarOptionLookup, avatarProfile]);
  const avatarActiveSet = useMemo(() => {
    if (!avatarProfile || !avatarSetPresets.length) {
      return null;
    }
    return (
      avatarSetPresets.find((preset) => {
        const slots = preset?.slots && typeof preset.slots === "object" ? preset.slots : {};
        return Object.entries(slots).every(([slot, value]) => avatarProfile?.[slot] === value);
      }) || null
    );
  }, [avatarProfile, avatarSetPresets]);
  const avatarPreviewSet = useMemo(() => {
    if (!avatarPreviewSetKey) {
      return null;
    }
    return (
      avatarSetPresets.find((preset) => String(preset?.key || "").trim().toLowerCase() === avatarPreviewSetKey) || null
    );
  }, [avatarPreviewSetKey, avatarSetPresets]);
  const avatarPreviewProfile = useMemo(() => {
    if (!avatarProfile) {
      return null;
    }
    const previewSlots = avatarPreviewSet?.slots && typeof avatarPreviewSet.slots === "object" ? avatarPreviewSet.slots : null;
    if (!previewSlots) {
      return avatarProfile;
    }
    return { ...avatarProfile, ...previewSlots };
  }, [avatarPreviewSet, avatarProfile]);
  const avatarDisplayLabelBySlot = useMemo(() => {
    if (!avatarPreviewProfile) {
      return {};
    }
    const rows = {};
    for (const [slot, value] of Object.entries(avatarPreviewProfile)) {
      if (slot === "updated_at") {
        continue;
      }
      const optionLabel = avatarOptionLookup?.[slot]?.[value]?.label;
      rows[slot] = optionLabel || humanizeKey(value);
    }
    return rows;
  }, [avatarOptionLookup, avatarPreviewProfile]);
  const avatarPreviewingSet = Boolean(avatarPreviewSet?.key && avatarActiveSet?.key !== avatarPreviewSet?.key);
  const avatarPreviewSummary = useMemo(() => {
    if (!avatarPreviewProfile) {
      return "Avatar loading...";
    }
    if (avatarPreviewingSet && avatarPreviewSet?.label) {
      return `Previewing ${avatarPreviewSet.label}`;
    }
    if (avatarActiveSet?.label) {
      return `${avatarActiveSet.label} equipped`;
    }
    const headLabel = avatarDisplayLabelBySlot.style || "Classic Human";
    const topLabel = avatarDisplayLabelBySlot.top || "Blue Hoodie";
    const accessoryLabel = avatarDisplayLabelBySlot.accessory || "None";
    return `${headLabel} | ${topLabel} | ${accessoryLabel}`;
  }, [avatarActiveSet?.label, avatarDisplayLabelBySlot, avatarPreviewProfile, avatarPreviewSet?.label, avatarPreviewingSet]);
  const avatarVisual = useMemo(() => {
    if (!avatarPreviewProfile) {
      return null;
    }
    const styleKey = String(avatarPreviewProfile.style || "urban").trim();
    const topKey = String(avatarPreviewProfile.top || "hoodie_blue").trim();
    const bottomKey = String(avatarPreviewProfile.bottom || "jeans_dark").trim();
    const accessoryKey = String(avatarPreviewProfile.accessory || "none").trim();
    const paletteKey = String(avatarPreviewProfile.palette || "cool").trim();
    const bodyTypeKey = String(avatarPreviewProfile.body_type || "nonbinary").trim().toLowerCase();
    const bodyTypeOption = avatarOptionLookup?.body_type?.[bodyTypeKey];
    const styleOption = avatarOptionLookup?.style?.[styleKey];
    const topOption = avatarOptionLookup?.top?.[topKey];
    const bottomOption = avatarOptionLookup?.bottom?.[bottomKey];
    const accessoryOption = avatarOptionLookup?.accessory?.[accessoryKey];
    return {
      bodyTypeIcon: bodyTypeOption?.icon || "\u26A7",
      headIcon: styleOption?.icon || ICONS.avatar,
      topIcon: topOption?.icon || "\u{1F455}",
      bottomIcon: bottomOption?.icon || "\u{1F456}",
      accessoryIcon: accessoryOption?.icon || "",
      bodyTypeLabel: avatarDisplayLabelBySlot.body_type || humanizeKey(bodyTypeKey),
      paletteLabel: avatarDisplayLabelBySlot.palette || humanizeKey(paletteKey)
    };
  }, [avatarDisplayLabelBySlot, avatarOptionLookup, avatarPreviewProfile]);
  const avatarProfileRows = useMemo(() => {
    if (!avatarProfile) {
      return [];
    }
    return Object.entries(avatarProfile)
      .filter(([slot]) => slot !== "updated_at")
      .map(([slot, value]) => ({
        slot,
        slotLabel: AVATAR_SLOT_LABELS[slot] || humanizeKey(slot),
        valueLabel: avatarSelectedLabelBySlot[slot] || humanizeKey(value)
      }));
  }, [avatarProfile, avatarSelectedLabelBySlot]);
  const selectedSpace = spaceDetails?.space || null;
  const selectedSpaceMembers = spaceDetails?.members || [];
  const selectedSpaceRoleTemplates = spaceDetails?.role_templates || [];
  const selectedSpacePermissions = spaceDetails?.permissions || {};
  const selectedSpaceInvites = spaceDetails?.invites || [];
  const selectedSpaceInviteSummary = spaceDetails?.invite_summary || {
    total: 0,
    active: 0,
    accepted: 0,
    revoked: 0,
    expired: 0
  };
  const selectedSpaceNotificationPreference = spaceDetails?.notification_preference || {
    mode: "all",
    label: "All updates",
    description: "Show shared queue updates in reminders and digests."
  };
  const selectedSpaceNotificationDefault = spaceDetails?.notification_default || {
    mode: "all",
    label: "All updates",
    description: "Show all shared queue updates in reminders and digests."
  };
  const selectedSpaceNotificationQuietHoursRaw =
    spaceDetails?.notification_quiet_hours && typeof spaceDetails.notification_quiet_hours === "object"
      ? spaceDetails.notification_quiet_hours
      : {};
  const selectedSpaceNotificationQuietHours = {
    enabled: Boolean(
      selectedSpaceNotificationQuietHoursRaw.enabled ??
        selectedSpace?.notification_quiet_hours_enabled ??
        DEFAULT_SPACE_QUIET_HOURS.enabled
    ),
    start_hour_utc: normalizeQuietHour(
      selectedSpaceNotificationQuietHoursRaw.start_hour_utc ?? selectedSpace?.notification_quiet_hours_start_utc,
      Number(DEFAULT_SPACE_QUIET_HOURS.start_hour_utc)
    ),
    end_hour_utc: normalizeQuietHour(
      selectedSpaceNotificationQuietHoursRaw.end_hour_utc ?? selectedSpace?.notification_quiet_hours_end_utc,
      Number(DEFAULT_SPACE_QUIET_HOURS.end_hour_utc)
    ),
    window_label:
      selectedSpaceNotificationQuietHoursRaw.window_label ||
      `${String(
        normalizeQuietHour(
          selectedSpaceNotificationQuietHoursRaw.start_hour_utc ?? selectedSpace?.notification_quiet_hours_start_utc,
          Number(DEFAULT_SPACE_QUIET_HOURS.start_hour_utc)
        )
      ).padStart(2, "0")}:00-${String(
        normalizeQuietHour(
          selectedSpaceNotificationQuietHoursRaw.end_hour_utc ?? selectedSpace?.notification_quiet_hours_end_utc,
          Number(DEFAULT_SPACE_QUIET_HOURS.end_hour_utc)
        )
      ).padStart(2, "0")}:00 UTC`,
    is_active_now: Boolean(selectedSpaceNotificationQuietHoursRaw.is_active_now)
  };
  const selectedSpaceNotificationModeDescription =
    SPACE_NOTIFICATION_MODE_OPTIONS.find((option) => option.value === spaceNotificationPreferenceMode)?.description ||
    selectedSpaceNotificationPreference.description ||
    "";
  const selectedSpaceNotificationDefaultDescription =
    SPACE_NOTIFICATION_MODE_OPTIONS.find((option) => option.value === spaceNotificationDefaultMode)?.description ||
    selectedSpaceNotificationDefault.description ||
    "";
  const selectedSpaceInviteAnalytics = spaceDetails?.invite_analytics || null;
  const defaultInviteRoleBreakdown = createInviteRoleBreakdownDefault();
  const selectedSpaceInviteRoleLabels = selectedSpaceInviteAnalytics?.role_labels || {
    member: "Member links",
    admin: "Admin links",
    other: "Other links"
  };
  const selectedSpaceInviteLifetime = selectedSpaceInviteAnalytics?.lifetime || {
    created: 0,
    accepted: 0,
    revoked: 0,
    expired: 0,
    active: 0,
    conversion_rate_percent: 0,
    role_breakdown: defaultInviteRoleBreakdown
  };
  const selectedSpaceInviteLast7Days = selectedSpaceInviteAnalytics?.recent?.last_7_days || {
    created: 0,
    accepted: 0,
    revoked: 0,
    accepted_events: 0,
    revoked_events: 0,
    conversion_rate_percent: 0,
    role_breakdown: defaultInviteRoleBreakdown
  };
  const selectedSpaceInviteLast30Days = selectedSpaceInviteAnalytics?.recent?.last_30_days || {
    created: 0,
    accepted: 0,
    revoked: 0,
    accepted_events: 0,
    revoked_events: 0,
    conversion_rate_percent: 0,
    role_breakdown: defaultInviteRoleBreakdown
  };
  const selectedSpaceInviteLifetimeByRole = selectedSpaceInviteLifetime.role_breakdown || defaultInviteRoleBreakdown;
  const selectedSpaceInviteLast7DaysByRole = selectedSpaceInviteLast7Days.role_breakdown || defaultInviteRoleBreakdown;
  const selectedSpaceInviteLast30DaysByRole = selectedSpaceInviteLast30Days.role_breakdown || defaultInviteRoleBreakdown;
  const selectedSpaceInviteRoleKeys = ["member", "admin", "other"].filter(
    (roleKey) =>
      roleKey !== "other" ||
      Number(selectedSpaceInviteLifetimeByRole?.other?.created || 0) > 0 ||
      Number(selectedSpaceInviteLast7DaysByRole?.other?.created || 0) > 0 ||
      Number(selectedSpaceInviteLast30DaysByRole?.other?.created || 0) > 0
  );
  const selectedSpaceAuditEvents = spaceAuditRows;
  const selectedSpaceAuditSummary = spaceAuditSummary;
  const selectedSpaceAuditEventTypeOptions = spaceAuditAvailableEventTypes.length
    ? spaceAuditAvailableEventTypes
    : Object.keys(selectedSpaceAuditSummary.by_type || {}).sort((left, right) => left.localeCompare(right));
  const selectedSpaceTasks = spaceDetails?.tasks || [];
  const selectedSpaceTaskSummary = spaceDetails?.task_summary || { total: 0, todo: 0, done: 0 };
  const canManageSpace = Boolean(selectedSpacePermissions.can_manage_space);
  const canImportSpaceSnapshot = selectedSpace?.current_role === "owner";
  const canManageRoleTemplates = selectedSpace?.current_role === "owner";
  const canManageSpaceNotificationDefault = selectedSpace?.current_role === "owner";
  const canManageSpaceQuietHours = Boolean(selectedSpacePermissions.can_manage_space);
  const canManageSpaceInvites = Boolean(selectedSpacePermissions.can_manage_invites);
  const canCreateSpaceTasks = Boolean(selectedSpacePermissions.can_create_tasks);
  const canCompleteSpaceTasks = Boolean(selectedSpacePermissions.can_complete_tasks);
  const canManageAnySpaceTask = Boolean(selectedSpacePermissions.can_manage_tasks);
  const spaceImportPreviewSummary = spaceImportPreview?.summary || null;
  const spaceImportPreviewDetailsMeta =
    spaceImportPreviewSummary && typeof spaceImportPreviewSummary.details === "object"
      ? spaceImportPreviewSummary.details
      : null;
  const spaceImportPreviewSkippedDetails =
    spaceImportPreviewDetailsMeta && typeof spaceImportPreviewDetailsMeta.skipped === "object"
      ? spaceImportPreviewDetailsMeta.skipped
      : {};
  const spaceImportPreviewTruncatedMap =
    spaceImportPreviewDetailsMeta && typeof spaceImportPreviewDetailsMeta.truncated === "object"
      ? spaceImportPreviewDetailsMeta.truncated
      : {};
  const spaceImportPreviewDetailLimit = Number(spaceImportPreviewDetailsMeta?.detail_limit || 0);
  const spaceImportPreviewWarnings = Array.isArray(spaceImportPreview?.warnings) ? spaceImportPreview.warnings : [];
  const spaceImportPreviewConfirmation =
    spaceImportPreview && typeof spaceImportPreview.confirmation === "object" ? spaceImportPreview.confirmation : null;
  const spaceImportPreviewConfirmationPhrase = String(spaceImportPreviewConfirmation?.phrase || "").trim();
  const spaceImportRequiredPhrase = spaceImportForm.mode === "replace"
    ? spaceImportPreviewConfirmationPhrase || buildSpaceReplaceConfirmationPhrase(selectedSpaceId)
    : "";
  const spaceImportEnteredPhrase = String(spaceImportForm.confirmation_phrase || "").trim();
  const spaceReplacePreviewReady =
    spaceImportForm.mode !== "replace" || (spaceImportPreview && spaceImportPreview.mode === "replace");
  const spaceImportConfirmationMatches =
    spaceImportForm.mode !== "replace" ||
    (spaceImportRequiredPhrase.length > 0 && spaceImportEnteredPhrase === spaceImportRequiredPhrase);
  const spaceImportPreviewRows = Object.entries(SPACE_SNAPSHOT_IMPORT_LABELS).map(([key, label]) => ({
    key,
    label,
    current: Number(spaceImportPreview?.current?.[key] || 0),
    projected: Number(spaceImportPreview?.projected?.[key] || 0),
    diff: Number(spaceImportPreview?.diff?.[key] || 0),
    imported: Number(spaceImportPreviewSummary?.imported?.[key] || 0),
    skipped: Number(spaceImportPreviewSummary?.skipped?.[key] || 0)
  }));
  const spaceReplacePreviewRows = spaceImportPreviewRows.filter(
    (row) => row.diff !== 0 || row.imported > 0 || row.skipped > 0
  );
  const spaceImportPreviewDetailRows = Object.entries(SPACE_SNAPSHOT_IMPORT_LABELS).flatMap(([key, label]) => {
    const entries = Array.isArray(spaceImportPreviewSkippedDetails?.[key]) ? spaceImportPreviewSkippedDetails[key] : [];
    return entries.map((entry, index) => ({
      id: `${key}-${index}`,
      key,
      label,
      reason: String(entry?.reason || "Skipped"),
      itemSummary: formatPreviewItemSummary(entry?.item)
    }));
  });
  const spaceImportPreviewTruncatedTotal = Object.values(spaceImportPreviewTruncatedMap).reduce(
    (total, value) => total + Math.max(Number(value || 0), 0),
    0
  );
  const questRows = useMemo(() => taskRows.filter((row) => row.task_type === "quest"), [taskRows]);
  const openQuestRows = useMemo(() => questRows.filter((row) => row.status !== "done"), [questRows]);
  const filteredTaskRows = useMemo(() => {
    const query = String(taskSearchQuery || "").trim().toLowerCase();
    const priorityRank = { high: 3, medium: 2, low: 1 };
    const dueSortValue = (value, fallbackValue) => {
      const raw = String(value || "").trim();
      if (!raw) {
        return fallbackValue;
      }
      const parsed = Date.parse(`${raw}T00:00:00`);
      return Number.isFinite(parsed) ? parsed : fallbackValue;
    };
    const rows = taskRows.filter((row) => {
      const statusValue = String(row?.status || "").trim().toLowerCase();
      const typeValue = String(row?.task_type || "").trim().toLowerCase();
      const priorityValue = String(row?.priority || "").trim().toLowerCase();
      if (taskStatusFilter !== "all" && statusValue !== taskStatusFilter) {
        return false;
      }
      if (taskTypeFilter !== "all" && typeValue !== taskTypeFilter) {
        return false;
      }
      if (taskPriorityFilter !== "all" && priorityValue !== taskPriorityFilter) {
        return false;
      }
      if (!query) {
        return true;
      }
      const titleValue = String(row?.title || "").toLowerCase();
      const dueValue = String(row?.due_on || "").toLowerCase();
      return titleValue.includes(query) || dueValue.includes(query) || typeValue.includes(query) || priorityValue.includes(query);
    });
    rows.sort((left, right) => {
      const leftId = Number(left?.id || 0);
      const rightId = Number(right?.id || 0);
      if (taskSortMode === "due_asc") {
        const leftDue = dueSortValue(left?.due_on, Number.MAX_SAFE_INTEGER);
        const rightDue = dueSortValue(right?.due_on, Number.MAX_SAFE_INTEGER);
        if (leftDue !== rightDue) {
          return leftDue - rightDue;
        }
        return rightId - leftId;
      }
      if (taskSortMode === "due_desc") {
        const leftDue = dueSortValue(left?.due_on, Number.MIN_SAFE_INTEGER);
        const rightDue = dueSortValue(right?.due_on, Number.MIN_SAFE_INTEGER);
        if (leftDue !== rightDue) {
          return rightDue - leftDue;
        }
        return rightId - leftId;
      }
      if (taskSortMode === "priority_desc") {
        const leftPriority = priorityRank[String(left?.priority || "").toLowerCase()] || 0;
        const rightPriority = priorityRank[String(right?.priority || "").toLowerCase()] || 0;
        if (leftPriority !== rightPriority) {
          return rightPriority - leftPriority;
        }
        return rightId - leftId;
      }
      if (taskSortMode === "xp_desc") {
        const leftXp = Number(left?.xp_effective ?? left?.xp_reward ?? 0);
        const rightXp = Number(right?.xp_effective ?? right?.xp_reward ?? 0);
        if (leftXp !== rightXp) {
          return rightXp - leftXp;
        }
        return rightId - leftId;
      }
      if (taskSortMode === "title_asc") {
        const leftTitle = String(left?.title || "").trim().toLowerCase();
        const rightTitle = String(right?.title || "").trim().toLowerCase();
        if (leftTitle !== rightTitle) {
          return leftTitle.localeCompare(rightTitle);
        }
        return rightId - leftId;
      }
      return rightId - leftId;
    });
    return rows;
  }, [taskRows, taskSearchQuery, taskStatusFilter, taskTypeFilter, taskPriorityFilter, taskSortMode]);
  const taskFilterActive = Boolean(
    String(taskSearchQuery || "").trim() ||
      taskStatusFilter !== "all" ||
      taskTypeFilter !== "all" ||
      taskPriorityFilter !== "all" ||
      taskSortMode !== "due_asc"
  );
  const filteredHabitRows = useMemo(() => {
    const query = String(habitSearchQuery || "").trim().toLowerCase();
    const completedSortValue = (value, fallbackValue) => {
      const raw = String(value || "").trim();
      if (!raw) {
        return fallbackValue;
      }
      const parsed = Date.parse(`${raw}T00:00:00`);
      return Number.isFinite(parsed) ? parsed : fallbackValue;
    };
    const rows = habitRows.filter((row) => {
      const currentStreak = Number(row?.current_streak || 0);
      if (habitStreakFilter === "hot" && currentStreak < 7) {
        return false;
      }
      if (habitStreakFilter === "active" && currentStreak < 1) {
        return false;
      }
      if (habitStreakFilter === "idle" && currentStreak !== 0) {
        return false;
      }
      if (!query) {
        return true;
      }
      const nameValue = String(row?.name || "").toLowerCase();
      const currentValue = String(row?.current_streak ?? "").toLowerCase();
      const longestValue = String(row?.longest_streak ?? "").toLowerCase();
      const lastCompletedValue = String(row?.last_completed_on || "").toLowerCase();
      return (
        nameValue.includes(query) ||
        currentValue.includes(query) ||
        longestValue.includes(query) ||
        lastCompletedValue.includes(query)
      );
    });
    rows.sort((left, right) => {
      const leftId = Number(left?.id || 0);
      const rightId = Number(right?.id || 0);
      if (habitSortMode === "streak_desc") {
        const leftCurrent = Number(left?.current_streak || 0);
        const rightCurrent = Number(right?.current_streak || 0);
        if (leftCurrent !== rightCurrent) {
          return rightCurrent - leftCurrent;
        }
        const leftLongest = Number(left?.longest_streak || 0);
        const rightLongest = Number(right?.longest_streak || 0);
        if (leftLongest !== rightLongest) {
          return rightLongest - leftLongest;
        }
        return rightId - leftId;
      }
      if (habitSortMode === "longest_desc") {
        const leftLongest = Number(left?.longest_streak || 0);
        const rightLongest = Number(right?.longest_streak || 0);
        if (leftLongest !== rightLongest) {
          return rightLongest - leftLongest;
        }
        const leftCurrent = Number(left?.current_streak || 0);
        const rightCurrent = Number(right?.current_streak || 0);
        if (leftCurrent !== rightCurrent) {
          return rightCurrent - leftCurrent;
        }
        return rightId - leftId;
      }
      if (habitSortMode === "last_completed_desc") {
        const leftCompleted = completedSortValue(left?.last_completed_on, Number.MIN_SAFE_INTEGER);
        const rightCompleted = completedSortValue(right?.last_completed_on, Number.MIN_SAFE_INTEGER);
        if (leftCompleted !== rightCompleted) {
          return rightCompleted - leftCompleted;
        }
        return rightId - leftId;
      }
      if (habitSortMode === "name_asc") {
        const leftName = String(left?.name || "").trim().toLowerCase();
        const rightName = String(right?.name || "").trim().toLowerCase();
        if (leftName !== rightName) {
          return leftName.localeCompare(rightName);
        }
        return rightId - leftId;
      }
      return rightId - leftId;
    });
    return rows;
  }, [habitRows, habitSearchQuery, habitStreakFilter, habitSortMode]);
  const habitFilterActive = Boolean(
    String(habitSearchQuery || "").trim() || habitStreakFilter !== "all" || habitSortMode !== "created_desc"
  );
  const filteredGoalRows = useMemo(() => {
    const query = String(goalSearchQuery || "").trim().toLowerCase();
    const today = new Date();
    const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
    const deadlineSortValue = (value, fallbackValue) => {
      const raw = String(value || "").trim();
      if (!raw) {
        return fallbackValue;
      }
      const parsed = Date.parse(`${raw}T00:00:00`);
      return Number.isFinite(parsed) ? parsed : fallbackValue;
    };
    const rows = goalRows.filter((row) => {
      const currentValue = Number(row?.current_value || 0);
      const targetValue = Math.max(Number(row?.target_value || 0), 1);
      const completed = currentValue >= targetValue;
      const deadlineRaw = String(row?.deadline || "").trim();
      const hasDeadline = Boolean(deadlineRaw);
      const deadlineParsed = hasDeadline ? Date.parse(`${deadlineRaw}T00:00:00`) : Number.NaN;
      const hasValidDeadline = Number.isFinite(deadlineParsed);
      const overdue = !completed && hasValidDeadline && deadlineParsed < todayStart;
      if (goalStatusFilter === "completed" && !completed) {
        return false;
      }
      if (goalStatusFilter === "in_progress" && completed) {
        return false;
      }
      if (goalStatusFilter === "overdue" && !overdue) {
        return false;
      }
      if (goalStatusFilter === "no_deadline" && hasDeadline) {
        return false;
      }
      if (!query) {
        return true;
      }
      const titleValue = String(row?.title || "").toLowerCase();
      const deadlineValue = String(row?.deadline || "").toLowerCase();
      const currentNumberValue = String(row?.current_value ?? "").toLowerCase();
      const targetNumberValue = String(row?.target_value ?? "").toLowerCase();
      return (
        titleValue.includes(query) ||
        deadlineValue.includes(query) ||
        currentNumberValue.includes(query) ||
        targetNumberValue.includes(query)
      );
    });
    rows.sort((left, right) => {
      const leftId = Number(left?.id || 0);
      const rightId = Number(right?.id || 0);
      if (goalSortMode === "progress_desc") {
        const leftCurrent = Number(left?.current_value || 0);
        const leftTarget = Math.max(Number(left?.target_value || 0), 1);
        const rightCurrent = Number(right?.current_value || 0);
        const rightTarget = Math.max(Number(right?.target_value || 0), 1);
        const leftProgress = leftCurrent / leftTarget;
        const rightProgress = rightCurrent / rightTarget;
        if (leftProgress !== rightProgress) {
          return rightProgress - leftProgress;
        }
        return rightId - leftId;
      }
      if (goalSortMode === "deadline_asc") {
        const leftDeadline = deadlineSortValue(left?.deadline, Number.MAX_SAFE_INTEGER);
        const rightDeadline = deadlineSortValue(right?.deadline, Number.MAX_SAFE_INTEGER);
        if (leftDeadline !== rightDeadline) {
          return leftDeadline - rightDeadline;
        }
        return rightId - leftId;
      }
      if (goalSortMode === "title_asc") {
        const leftTitle = String(left?.title || "").trim().toLowerCase();
        const rightTitle = String(right?.title || "").trim().toLowerCase();
        if (leftTitle !== rightTitle) {
          return leftTitle.localeCompare(rightTitle);
        }
        return rightId - leftId;
      }
      return rightId - leftId;
    });
    return rows;
  }, [goalRows, goalSearchQuery, goalStatusFilter, goalSortMode]);
  const goalFilterActive = Boolean(
    String(goalSearchQuery || "").trim() || goalStatusFilter !== "all" || goalSortMode !== "created_desc"
  );
  const maxTaskTypeCount = useMemo(
    () => Math.max(...statsTaskTypeRows.map((row) => row.count), 1),
    [statsTaskTypeRows]
  );
  const normalizedPath = useMemo(() => {
    const trimmed = location.pathname.replace(/\/+$/, "");
    return trimmed || "/";
  }, [location.pathname]);
  const activeView = VIEW_BY_PATH[normalizedPath] || "dashboard";
  const activeNavItem = NAV_ITEMS.find((item) => item.key === activeView) || NAV_ITEMS[0];
  const topbarTitle = activeView === "dashboard" ? "Welcome back!" : activeNavItem.label;
  const topbarSubtitle = activeView === "dashboard" ? `@${authUser?.username || ""}` : "LifeOS workspace";
  const dashboardQuickBusy = Boolean(dashboardQuickBusyKey);

  useEffect(() => {
    if (!VIEW_BY_PATH[normalizedPath]) {
      navigate("/dashboard", { replace: true });
    }
  }, [navigate, normalizedPath]);

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }, [activeView]);

  useEffect(() => {
    if (inventoryCategoryFilter === "all") {
      return;
    }
    if (inventoryCategoryOptions.some((option) => option.key === inventoryCategoryFilter)) {
      return;
    }
    setInventoryCategoryFilter("all");
  }, [inventoryCategoryFilter, inventoryCategoryOptions]);

  useEffect(() => {
    if (inventoryTypeFilter === "all") {
      return;
    }
    if (inventoryTypeOptions.some((option) => option.key === inventoryTypeFilter)) {
      return;
    }
    setInventoryTypeFilter("all");
  }, [inventoryTypeFilter, inventoryTypeOptions]);

  useEffect(() => {
    if (shopAvatarSetFilter === "all") {
      return;
    }
    if (shopAvatarSetOptions.some((option) => option.key === shopAvatarSetFilter)) {
      return;
    }
    setShopAvatarSetFilter("all");
  }, [shopAvatarSetFilter, shopAvatarSetOptions]);

  useEffect(() => {
    if (!shopHighlightSetKey) {
      return;
    }
    if (shopCategoryFilter !== "avatar") {
      setShopHighlightSetKey("");
      setShopHighlightMode("");
      return;
    }
    if (shopAvatarSetFilter !== "all" && shopAvatarSetFilter !== shopHighlightSetKey) {
      setShopHighlightSetKey("");
      setShopHighlightMode("");
      return;
    }
    if (shopAvatarViewFilter !== "all" && shopHighlightMode) {
      const expectedView = shopHighlightMode === "parts" ? "set_parts" : "set_bundles";
      if (shopAvatarViewFilter !== expectedView) {
        setShopHighlightSetKey("");
        setShopHighlightMode("");
      }
    }
  }, [shopAvatarSetFilter, shopAvatarViewFilter, shopCategoryFilter, shopHighlightSetKey, shopHighlightMode]);

  useEffect(() => {
    if (shopCategoryFilter === "all" || shopCategoryFilter === "avatar") {
      return;
    }
    if (shopAvatarViewFilter !== "all") {
      setShopAvatarViewFilter("all");
    }
    if (shopAvatarSetFilter !== "all") {
      setShopAvatarSetFilter("all");
    }
    if (shopHighlightSetKey || shopHighlightMode) {
      setShopHighlightSetKey("");
      setShopHighlightMode("");
    }
  }, [shopAvatarSetFilter, shopAvatarViewFilter, shopCategoryFilter, shopHighlightSetKey, shopHighlightMode]);

  useEffect(() => {
    if (activeView !== "shop" || !shopHighlightSetKey || shopHighlightScrollToken < 1) {
      return;
    }
    const rafId = window.requestAnimationFrame(() => {
      const target = document.querySelector(".shop-item.highlight");
      if (target instanceof HTMLElement) {
        target.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    });
    return () => window.cancelAnimationFrame(rafId);
  }, [activeView, shopHighlightSetKey, shopHighlightScrollToken]);

  useEffect(() => {
    if (!avatarPreviewSetKey) {
      return;
    }
    const hasPreviewSet = avatarSetPresets.some(
      (preset) => String(preset?.key || "").trim().toLowerCase() === avatarPreviewSetKey
    );
    if (!hasPreviewSet) {
      setAvatarPreviewSetKey("");
    }
  }, [avatarPreviewSetKey, avatarSetPresets]);

  useEffect(() => {
    if (spaceAuditForm.event_type === "all") {
      return;
    }
    if (selectedSpaceAuditEventTypeOptions.includes(spaceAuditForm.event_type)) {
      return;
    }
    setSpaceAuditForm((prev) => ({ ...prev, event_type: "all" }));
  }, [selectedSpaceAuditEventTypeOptions, spaceAuditForm.event_type]);

  useEffect(() => {
    if (!leaderboardBoards.length) {
      return;
    }
    if (leaderboardBoards.some((board) => board?.key === leaderboardBoardKey)) {
      return;
    }
    setLeaderboardBoardKey(String(leaderboardBoards[0]?.key || "xp_7d"));
  }, [leaderboardBoardKey, leaderboardBoards]);

  useEffect(() => {
    if (!spaceReplaceConfirmOpen) {
      return undefined;
    }
    function handleEscape(event) {
      if (event.key === "Escape" && spacesBusyKey !== "space-import") {
        setSpaceReplaceConfirmOpen(false);
      }
    }
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [spaceReplaceConfirmOpen, spacesBusyKey]);

  async function handleStatsRangeChange(days) {
    setStatsRangeDays(days);
    await loadStats(days);
  }

  async function handleTimelineRangeChange(days) {
    const safeDays = Number(days) || 30;
    setTimelineRangeDays(safeDays);
    await loadTimeline(safeDays);
  }

  function normalizeAppPath(pathValue) {
    const raw = String(pathValue || "").trim();
    if (!raw) {
      return "/dashboard";
    }
    const prefixed = raw.startsWith("/") ? raw : `/${raw}`;
    const normalized = prefixed.replace(/\/+$/, "") || "/";
    return VIEW_BY_PATH[normalized] ? normalized : "/dashboard";
  }

  function handleNavItemClick(itemPath) {
    const nextPath = normalizeAppPath(itemPath);
    navigate(nextPath);
    setNotice("");
    setMobileSidebarOpen(false);
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }

  function handleNotificationClick(item) {
    const rawTargetPath = String(item?.related?.path || "").trim();
    if (rawTargetPath) {
      handleNavItemClick(rawTargetPath);
    }
  }

  const appClassName = [
    "app-layout",
    sidebarExpanded ? "sidebar-expanded" : "sidebar-collapsed",
    mobileSidebarOpen ? "sidebar-mobile-open" : ""
  ]
    .filter(Boolean)
    .join(" ");

  const getTaskEdit = (task) => taskEdits[task.id] || taskEditFromRow(task);
  const getHabitEdit = (habit) => habitEdits[habit.id] || habitEditFromRow(habit);
  const getGoalEdit = (goal) => goalEdits[goal.id] || goalEditFromRow(goal);
  const getSpaceTaskEdit = (task) => spaceTaskEdits[task.id] || spaceTaskEditFromRow(task);
  const getSpaceTemplateEdit = (template) => spaceTemplateEdits[template.role] || spaceTemplateEditFromRow(template);

  if (isBooting) {
    return <main className="loading-state">Starting LifeOS...</main>;
  }

  if (!authUser) {
    return (
      <AuthPanel
        mode={authMode}
        authForm={authForm}
        authSubmitting={authSubmitting}
        error={error}
        onModeChange={(mode) => {
          setAuthMode(mode);
          setError("");
        }}
        onChange={(event) => {
          const { name, value } = event.target;
          setAuthForm((prev) => ({ ...prev, [name]: value }));
        }}
        onSubmit={handleAuthSubmit}
      />
    );
  }

  if (!dashboard) {
    return <main className="loading-state">Loading dashboard...</main>;
  }

  return (
    <div className={appClassName}>
      <div className="sidebar-overlay" onClick={() => setMobileSidebarOpen(false)} />
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand">
            <span className="brand-icon">{ICONS.brand}</span>
            <span className="brand-text">LifeOS</span>
          </div>
          <div className="sidebar-controls">
            <button className="icon-btn desktop-only" type="button" onClick={() => setSidebarExpanded((v) => !v)}>
              {sidebarExpanded ? "<" : ">"}
            </button>
            <button className="icon-btn mobile-only" type="button" onClick={() => setMobileSidebarOpen(false)}>
              {ICONS.close}
            </button>
          </div>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              type="button"
              data-nav-key={item.key}
              className={`nav-item ${activeView === item.key ? "active" : ""}`}
              onClick={() => handleNavItemClick(item.path)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <p className="sidebar-level">{ICONS.level} Level {dashboard.user.level}</p>
          <div className="mini-progress">
            <span style={{ width: `${levelPercent}%` }} />
          </div>
          <p className="sidebar-xp">XP: {dashboard.user.xp_into_level} / {dashboard.user.xp_for_next_level}</p>
          <p className="sidebar-xp">{ICONS.coins} Coins: {prettyNumber(coinBalance)}</p>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar panel">
          <div className="topbar-left">
            <button className="icon-btn mobile-only" type="button" onClick={() => setMobileSidebarOpen(true)}>
              {ICONS.menu}
            </button>
            <div>
              <h1>{topbarTitle}</h1>
              <p>{topbarSubtitle}</p>
            </div>
          </div>
          <div className="topbar-right">
            <span className="notify-chip">
              {ICONS.bell} {notificationCounts.total}
            </span>
            <span className="coin-chip">
              {ICONS.coins} {prettyNumber(coinBalance)}
            </span>
            <span className="user-chip">{authUser.display_name}</span>
            <button className="secondary-btn" type="button" onClick={handleLogout}>
              Sign out
            </button>
          </div>
        </header>

        <section className="panel xp-panel" hidden={activeView !== "dashboard"}>
          <div className="xp-title-row">
            <h2>{ICONS.trophy} Level {dashboard.user.level}</h2>
            <span>{dashboard.user.xp_total} Total XP</span>
          </div>
          <div className="xp-bar">
            <span style={{ width: `${levelPercent}%` }} />
          </div>
          <p>
            {ICONS.spark} {dashboard.user.xp_into_level} / {dashboard.user.xp_for_next_level} XP
          </p>
        </section>

        <section className="chip-row" hidden={activeView !== "dashboard"}>
          <div className="chip">{ICONS.streak} Current Streak: {dashboard.stats.current_streak} Days</div>
          <div className="chip">{ICONS.fire} Longest Streak: {dashboard.stats.longest_streak} Days</div>
          <div className="chip">{ICONS.compass} Open Quests: {dashboard.stats.open_quests}</div>
          <div className="chip">{ICONS.coins} Wallet: {prettyNumber(coinBalance)} coins</div>
          <div className="chip">
            {ICONS.achievements} Achievements: {prettyNumber(dashboard.stats.achievements_unlocked || 0)}/
            {prettyNumber(dashboard.stats.achievements_total || 0)}
          </div>
          <div className="chip">
            {ICONS.challenges} Claimable Challenges: {prettyNumber(dashboard.stats.challenge_claimable || 0)}
          </div>
          <div className="chip">
            {ICONS.seasonPass} Season Tier: {prettyNumber(dashboard.stats.season_tier || 1)} | Claimable:{" "}
            {prettyNumber(dashboard.stats.season_pass_claimable || 0)}
          </div>
        </section>

        <section className="panel dashboard-quick-actions" hidden={activeView !== "dashboard"}>
          <div className="dashboard-quick-actions-header">
            <h2>Quick Actions</h2>
            <span>Jump to key areas fast</span>
          </div>
          <div className="dashboard-quick-actions-grid">
            <button
              type="button"
              className="secondary-btn dashboard-action-btn"
              data-quick-nav="tasks"
              onClick={() => handleNavItemClick("/tasks")}
            >
              {ICONS.tasks} Open Tasks
            </button>
            <button
              type="button"
              className="secondary-btn dashboard-action-btn"
              data-quick-nav="quests"
              onClick={() => handleNavItemClick("/quests")}
            >
              {ICONS.quests} Open Quests
            </button>
            <button
              type="button"
              className="secondary-btn dashboard-action-btn"
              data-quick-nav="shop"
              onClick={() => handleNavItemClick("/shop")}
            >
              {ICONS.shop} Open Shop
            </button>
            <button
              type="button"
              className="secondary-btn dashboard-action-btn"
              data-quick-nav="avatar"
              onClick={() => handleNavItemClick("/avatar")}
            >
              {ICONS.avatar} Avatar Studio
            </button>
            <button
              type="button"
              className="secondary-btn dashboard-action-btn"
              data-quick-nav="spaces"
              onClick={() => handleNavItemClick("/spaces")}
            >
              {ICONS.spaces} Team Spaces
            </button>
          </div>
        </section>

        <section className="panel dashboard-create-panel" hidden={activeView !== "dashboard"}>
          <div className="dashboard-create-header">
            <div>
              <h2>Quick Create</h2>
              <span>Add a task, habit, or goal without leaving the dashboard</span>
            </div>
            <button type="button" className="secondary-btn" onClick={() => handleNavItemClick("/tasks")}>
              Open Full Manager
            </button>
          </div>
          <div className="dashboard-create-grid">
            <form className="dashboard-create-card" onSubmit={handleDashboardQuickTaskCreate}>
              <h3>{ICONS.tasks} Quick Task</h3>
              <input
                data-quick-create="task-title"
                placeholder="Task title"
                value={dashboardQuickTaskForm.title}
                onChange={(event) => setDashboardQuickTaskForm((prev) => ({ ...prev, title: event.target.value }))}
                required
                disabled={dashboardQuickBusy}
              />
              <div className="dashboard-create-inline task">
                <select
                  data-quick-create="task-type"
                  value={dashboardQuickTaskForm.task_type}
                  onChange={(event) => handleDashboardQuickTaskTypeChange(event.target.value)}
                  disabled={dashboardQuickBusy}
                >
                  <option value="task">Task</option>
                  <option value="habit">Habit</option>
                  <option value="quest">Quest</option>
                </select>
                <select
                  data-quick-create="task-priority"
                  value={dashboardQuickTaskForm.priority}
                  onChange={(event) => setDashboardQuickTaskForm((prev) => ({ ...prev, priority: event.target.value }))}
                  disabled={dashboardQuickBusy}
                >
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
                <input
                  data-quick-create="task-xp"
                  type="number"
                  min="1"
                  max="5000"
                  placeholder="XP"
                  value={dashboardQuickTaskForm.xp_reward}
                  onChange={(event) => setDashboardQuickTaskForm((prev) => ({ ...prev, xp_reward: event.target.value }))}
                  disabled={dashboardQuickBusy}
                />
                <input
                  data-quick-create="task-due-on"
                  type="date"
                  value={dashboardQuickTaskForm.due_on}
                  onChange={(event) => setDashboardQuickTaskForm((prev) => ({ ...prev, due_on: event.target.value }))}
                  disabled={dashboardQuickBusy}
                />
              </div>
              <div className="dashboard-create-chip-row">
                <button
                  type="button"
                  className="dashboard-create-chip-btn"
                  data-quick-create-due-preset="today"
                  onClick={() => handleDashboardQuickTaskDuePreset("today")}
                  disabled={dashboardQuickBusy}
                >
                  Due Today
                </button>
                <button
                  type="button"
                  className="dashboard-create-chip-btn"
                  data-quick-create-due-preset="tomorrow"
                  onClick={() => handleDashboardQuickTaskDuePreset("tomorrow")}
                  disabled={dashboardQuickBusy}
                >
                  Due Tomorrow
                </button>
                <button
                  type="button"
                  className="dashboard-create-chip-btn"
                  data-quick-create-due-preset="clear"
                  onClick={() => handleDashboardQuickTaskDuePreset("clear")}
                  disabled={dashboardQuickBusy}
                >
                  Clear Due Date
                </button>
              </div>
              <small className="dashboard-create-meta">
                Preset XP: Task {DASHBOARD_QUICK_TASK_XP_PRESETS.task}, Habit {DASHBOARD_QUICK_TASK_XP_PRESETS.habit},
                Quest {DASHBOARD_QUICK_TASK_XP_PRESETS.quest}
                {dashboardQuickTaskForm.due_on ? ` | Due ${formatDateLabel(dashboardQuickTaskForm.due_on)}` : ""}
              </small>
              <button
                type="submit"
                className="secondary-btn"
                data-quick-create-submit="task"
                disabled={dashboardQuickBusy}
              >
                {dashboardQuickBusyKey === "task-create" ? "Adding..." : "Add Task"}
              </button>
            </form>

            <form className="dashboard-create-card" onSubmit={handleDashboardQuickHabitCreate}>
              <h3>{ICONS.fire} Quick Habit</h3>
              <input
                data-quick-create="habit-name"
                placeholder="Habit name"
                value={dashboardQuickHabitForm.name}
                onChange={(event) => setDashboardQuickHabitForm({ name: event.target.value })}
                required
                disabled={dashboardQuickBusy}
              />
              <button
                type="submit"
                className="secondary-btn"
                data-quick-create-submit="habit"
                disabled={dashboardQuickBusy}
              >
                {dashboardQuickBusyKey === "habit-create" ? "Adding..." : "Add Habit"}
              </button>
            </form>

            <form className="dashboard-create-card" onSubmit={handleDashboardQuickGoalCreate}>
              <h3>{ICONS.compass} Quick Goal</h3>
              <input
                data-quick-create="goal-title"
                placeholder="Goal title"
                value={dashboardQuickGoalForm.title}
                onChange={(event) => setDashboardQuickGoalForm((prev) => ({ ...prev, title: event.target.value }))}
                required
                disabled={dashboardQuickBusy}
              />
              <div className="dashboard-create-inline goal">
                <input
                  data-quick-create="goal-target"
                  type="number"
                  min="1"
                  max="1000000"
                  placeholder="Target"
                  value={dashboardQuickGoalForm.target_value}
                  onChange={(event) => setDashboardQuickGoalForm((prev) => ({ ...prev, target_value: event.target.value }))}
                  required
                  disabled={dashboardQuickBusy}
                />
                <input
                  data-quick-create="goal-deadline"
                  type="date"
                  value={dashboardQuickGoalForm.deadline}
                  onChange={(event) => setDashboardQuickGoalForm((prev) => ({ ...prev, deadline: event.target.value }))}
                  disabled={dashboardQuickBusy}
                />
              </div>
              <button
                type="submit"
                className="secondary-btn"
                data-quick-create-submit="goal"
                disabled={dashboardQuickBusy}
              >
                {dashboardQuickBusyKey === "goal-create" ? "Adding..." : "Add Goal"}
              </button>
            </form>
          </div>
        </section>

        {dashboardLoading ? <p className="notice">Refreshing dashboard...</p> : null}
        {notice ? <p className="notice success">{notice}</p> : null}
        {error ? <p className="notice error">{error}</p> : null}

        <section className="panel reminder-panel" hidden={activeView !== "dashboard"}>
          <div className="reminder-header">
            <h2>{ICONS.bell} Reminders</h2>
            <span>{notificationCounts.total} active</span>
          </div>
          <div className="reminder-chip-row">
            <span className="chip">Overdue: {notificationCounts.overdue_tasks || 0}</span>
            <span className="chip">Streak Risk: {notificationCounts.streak_risk_habits || 0}</span>
            <span className="chip">Goal Deadlines: {notificationCounts.goals_due_soon || 0}</span>
            <span className="chip">Shared Queue: {notificationCounts.space_updates || 0}</span>
            <span className="chip">Invite Expiring: {notificationCounts.space_invites_expiring || 0}</span>
          </div>
          {notificationsLoading ? <p className="notice">Refreshing reminders...</p> : null}
          <ul className="reminder-list">
            {notificationItems.length === 0 ? <li className="empty-state">No active reminders. You are on track.</li> : null}
            {notificationItems.map((item) => (
              <li key={item.id} className={`reminder-item severity-${item.severity}`}>
                <div>
                  <p className="reminder-title">{item.title}</p>
                  <p className="reminder-message">{item.message}</p>
                </div>
                <button type="button" className="secondary-btn" onClick={() => handleNotificationClick(item)}>
                  Open
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="stats-shell" hidden={activeView !== "stats"}>
          <section className="panel stats-toolbar">
            <div>
              <h2>Stats & History</h2>
              <p>
                {statsData?.range ? `${statsData.range.start} to ${statsData.range.end}` : "Select a time window"}
              </p>
            </div>
            <div className="stats-range-switch">
              {STATS_RANGE_OPTIONS.map((days) => (
                <button
                  key={days}
                  type="button"
                  className={`range-btn ${statsRangeDays === days ? "active" : ""}`}
                  onClick={() => handleStatsRangeChange(days)}
                  disabled={statsLoading && statsRangeDays === days}
                >
                  {days}d
                </button>
              ))}
            </div>
          </section>

          {statsLoading ? <p className="notice">Refreshing stats...</p> : null}

          <section className="stats-summary-grid">
            <article className="panel stats-summary-card">
              <h3>Total XP</h3>
              <p>{prettyNumber(statsSummary?.xp_total)}</p>
              <small>
                Level {statsSummary?.level ?? dashboard.user.level} | {prettyNumber(statsSummary?.xp_into_level)} /{" "}
                {prettyNumber(statsSummary?.xp_for_next_level)} XP
              </small>
            </article>
            <article className="panel stats-summary-card">
              <h3>XP ({statsRangeDays}d)</h3>
              <p>{prettyNumber(statsSummary?.xp_in_range)}</p>
              <small>Last 7d: {prettyNumber(statsSummary?.xp_last_7_days)}</small>
            </article>
            <article className="panel stats-summary-card">
              <h3>Coins ({statsRangeDays}d)</h3>
              <p>{prettyNumber(statsSummary?.coins_earned_in_range)}</p>
              <small>
                Spent: {prettyNumber(statsSummary?.coins_spent_in_range)} | Balance:{" "}
                {prettyNumber(statsSummary?.coins_balance ?? coinBalance)}
              </small>
            </article>
            <article className="panel stats-summary-card">
              <h3>Completions</h3>
              <p>{prettyNumber((statsSummary?.tasks_completed_in_range || 0) + (statsSummary?.habit_checks_in_range || 0))}</p>
              <small>
                Tasks: {prettyNumber(statsSummary?.tasks_completed_in_range)} | Habits:{" "}
                {prettyNumber(statsSummary?.habit_checks_in_range)}
              </small>
            </article>
            <article className="panel stats-summary-card">
              <h3>Activity Rate</h3>
              <p>{statsSummary?.activity_rate ?? 0}%</p>
              <small>{prettyNumber(statsSummary?.active_days_in_range)} active days in range</small>
            </article>
            <article className="panel stats-summary-card">
              <h3>Goal Completion</h3>
              <p>{statsGoalStatus?.completion_rate ?? 0}%</p>
              <small>
                {prettyNumber(statsGoalStatus?.completed)} / {prettyNumber(statsGoalStatus?.total)} goals complete
              </small>
            </article>
            <article className="panel stats-summary-card">
              <h3>Best XP Day</h3>
              <p>{statsSummary?.top_xp_day ? prettyNumber(statsSummary.top_xp_day.xp) : 0} XP</p>
              <small>{statsSummary?.top_xp_day?.date || "No XP days yet"}</small>
            </article>
          </section>

          <section className="stats-chart-grid">
            <article className="panel stats-chart-card">
              <div className="stats-card-header">
                <h3>Daily XP</h3>
                <span>{prettyNumber(statsSummary?.xp_in_range)} XP in range</span>
              </div>
              <DailyXpChart rows={statsXpRows} />
            </article>
            <article className="panel stats-chart-card">
              <div className="stats-card-header">
                <h3>Daily Completions</h3>
                <span>{prettyNumber(statsSummary?.tasks_completed_in_range)} task completions</span>
              </div>
              <DailyCompletionChart rows={statsCompletionRows} />
              <p className="stats-legend">
                <span className="legend-dot task" />
                Tasks
                <span className="legend-dot habit" />
                Habits
              </p>
            </article>
          </section>

          <section className="stats-detail-grid">
            <article className="panel stats-detail-card">
              <div className="stats-card-header">
                <h3>Completed Task Mix</h3>
                <span>
                  {prettyNumber(statsTaskTypeRows.reduce((total, row) => total + (row.count || 0), 0))} total
                </span>
              </div>
              <ul className="type-breakdown-list">
                {statsTaskTypeRows.length === 0 ? (
                  <li className="chart-empty">No completed tasks in this range.</li>
                ) : (
                  statsTaskTypeRows.map((row) => (
                    <li key={row.task_type} className="type-breakdown-item">
                      <div className="type-breakdown-top">
                        <span>{row.label}</span>
                        <span>
                          {prettyNumber(row.count)} ({row.percentage}%)
                        </span>
                      </div>
                      <div className="type-breakdown-track">
                        <span
                          className="type-breakdown-fill"
                          style={{
                            width: `${Math.max((row.count / maxTaskTypeCount) * 100, row.count > 0 ? 8 : 0)}%`,
                            background: TASK_TYPE_THEME[row.task_type] || "var(--accent)"
                          }}
                        />
                      </div>
                    </li>
                  ))
                )}
              </ul>
            </article>
            <article className="panel stats-detail-card">
              <div className="stats-card-header">
                <h3>Top XP Sources</h3>
                <span>{statsRangeDays} day window</span>
              </div>
              <table className="history-table stats-table">
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>XP</th>
                  </tr>
                </thead>
                <tbody>
                  {statsXpSourceRows.length === 0 ? (
                    <tr>
                      <td colSpan={2}>No XP records in this range.</td>
                    </tr>
                  ) : (
                    statsXpSourceRows.map((row) => (
                      <tr key={row.source}>
                        <td>{row.source}</td>
                        <td>{prettyNumber(row.points)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </article>
          </section>
        </section>

        <section className="quests-shell" hidden={activeView !== "quests"}>
          <section className="panel quests-toolbar">
            <h2>Quest Board</h2>
            <span>{openQuestRows.length} open quests</span>
          </section>
          <section className="quests-grid">
            <article className="panel tasks-panel">
              <div className="panel-title-row">
                <h2>Active Quests</h2>
                <span>{questRows.length} total</span>
              </div>
              <ul className="task-list">
                {questRows.length === 0 ? <li className="empty-state">No quests yet. Create one in Tasks.</li> : null}
                {questRows.map((quest) => (
                  <li key={quest.id} className="task-item">
                    <div className="task-main">
                      <span className="task-icon">{TASK_TYPE_ICON.quest}</span>
                      <div>
                        <p className="task-title">{quest.title}</p>
                        <p className="task-meta">
                          {quest.status === "done" ? "Completed" : "Open"} | {quest.xp_effective ?? quest.xp_reward} XP |{" "}
                          {quest.priority}
                        </p>
                      </div>
                    </div>
                    {quest.status === "done" ? (
                      <button className="secondary-btn" type="button" disabled>
                        Complete
                      </button>
                    ) : (
                      <button
                        className="complete-btn"
                        type="button"
                        disabled={completingTaskId === quest.id}
                        onClick={() => handleCompleteTask(quest.id)}
                      >
                        {completingTaskId === quest.id ? "Working..." : "Complete"}
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            </article>
            <aside className="side-panels">
              <article className="panel goal-card">
                <h2>Goal Progress</h2>
                <ul className="goal-list">{dashboard.goals.map((goal) => <GoalItem key={goal.id} goal={goal} />)}</ul>
              </article>
              <article className="panel streak-card">
                <h2>Quest Metrics</h2>
                <p className="streak-big">{dashboard.stats.open_quests}</p>
                <p>Open quests in your queue.</p>
              </article>
            </aside>
          </section>
        </section>

        <section className="shop-shell" hidden={activeView !== "shop"}>
          <section className="panel shop-toolbar">
            <h2>LifeOS Shop</h2>
            <div className="shop-toolbar-meta">
              <span>{shopLoading ? "Refreshing..." : `${prettyNumber(coinBalance)} coins available`}</span>
              <small>{seasonPassPremiumEnabled ? "Premium track active" : "Premium track locked"}</small>
              <small>
                {shopRotation ? `Rotation resets in ${shopResetLabel}` : "Daily rotation active"}
              </small>
            </div>
          </section>

          <section className="panel shop-filter-toolbar">
            <div className="shop-filter-meta">
              Showing {prettyNumber(filteredShopItems.length)} of {prettyNumber(shopItems.length)} shop items
            </div>
            {shopHighlightSetKey ? (
              <div className="shop-focus-banner">
                <span>
                  {ICONS.spark} Focused from Avatar Studio: {shopHighlightSetLabel || humanizeKey(shopHighlightSetKey)}{" "}
                  {shopHighlightMode === "parts" ? "(parts)" : shopHighlightMode === "bundle" ? "(bundle)" : ""}
                </span>
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={() => {
                    setShopHighlightSetKey("");
                    setShopHighlightMode("");
                  }}
                >
                  Clear Focus
                </button>
              </div>
            ) : null}
            <div className="shop-filter-grid">
              <input
                placeholder="Search item, set, rarity..."
                value={shopSearchQuery}
                onChange={(event) => setShopSearchQuery(event.target.value)}
              />
              <select value={shopCategoryFilter} onChange={(event) => setShopCategoryFilter(event.target.value)}>
                {SHOP_CATEGORY_FILTER_OPTIONS.map((option) => (
                  <option key={`shop-category-filter-${option.key}`} value={option.key}>
                    {option.label}
                  </option>
                ))}
              </select>
              <select value={shopOwnershipFilter} onChange={(event) => setShopOwnershipFilter(event.target.value)}>
                {SHOP_OWNERSHIP_FILTER_OPTIONS.map((option) => (
                  <option key={`shop-ownership-filter-${option.key}`} value={option.key}>
                    {option.label}
                  </option>
                ))}
              </select>
              <select value={shopAvatarViewFilter} onChange={(event) => setShopAvatarViewFilter(event.target.value)}>
                {SHOP_AVATAR_VIEW_OPTIONS.map((option) => (
                  <option key={`shop-avatar-view-filter-${option.key}`} value={option.key}>
                    {option.label}
                  </option>
                ))}
              </select>
              <select value={shopAvatarSetFilter} onChange={(event) => setShopAvatarSetFilter(event.target.value)}>
                {shopAvatarSetOptions.map((option) => (
                  <option key={`shop-avatar-set-filter-${option.key}`} value={option.key}>
                    {option.label}
                  </option>
                ))}
              </select>
              {shopFilterActive ? (
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={() => {
                    setShopSearchQuery("");
                    setShopCategoryFilter("all");
                    setShopOwnershipFilter("all");
                    setShopAvatarViewFilter("all");
                    setShopAvatarSetFilter("all");
                    setShopHighlightSetKey("");
                    setShopHighlightMode("");
                  }}
                >
                  Clear Filters
                </button>
              ) : null}
            </div>
          </section>

          <section className="shop-grid">
            {shopCategoryRows.length === 0 ? (
              <article className="panel shop-category-card">
                <p className="empty-state">Shop catalog is empty right now.</p>
              </article>
            ) : (
              shopCategoryRows.map((category) => (
                <article key={category.key} className="panel shop-category-card">
                  <div className="shop-category-header">
                    <h3>{category.label}</h3>
                    <span>
                      {category.items.filter((item) => item?.available_today !== false).length}/{category.items.length} live today
                    </span>
                  </div>
                  <ul className="shop-item-list">
                    {category.items.map((item) => {
                      const buyBusy = shopBusyKey === `shop-buy-${item.item_key}`;
                      const canPurchaseToday = item?.can_purchase_today !== false;
                      const coinAffordable = item?.coin_affordable !== false;
                      const ownedOnce = Boolean(item.owned) && !Boolean(item.repeatable);
                      const unavailableReason = String(item?.availability_reason || "").trim();
                      const unavailable = !canPurchaseToday && !ownedOnce;
                      const cannotAffordCoins = !coinAffordable;
                      const disabled = buyBusy || ownedOnce || unavailable || cannotAffordCoins;
                      const stockLabel = item?.daily_stock
                        ? `${prettyNumber(item?.daily_remaining)} / ${prettyNumber(item?.daily_stock)} left today`
                        : "Unlimited daily stock";
                      const personalLimitLabel = item?.user_daily_limit
                        ? `${prettyNumber(item?.user_daily_remaining)} personal buys left`
                        : "";
                      const itemRewardType = String(item?.reward_type || "").trim().toLowerCase();
                      const itemSetKey = String(item?.set_key || item?.unlock_set_key || "").trim().toLowerCase();
                      const itemSetLabel = String(item?.set_label || (itemSetKey ? humanizeKey(itemSetKey) : "")).trim();
                      const bundleSavings =
                        itemRewardType === "avatar_set_unlock" && itemSetKey
                          ? Math.max(Number(shopAvatarSetPartTotals[itemSetKey] || 0) - Number(item?.price_coins || 0), 0)
                          : 0;
                      const rewardTypeLabel =
                        itemRewardType === "season_pass_premium_unlock"
                          ? "Season Pass Unlock"
                          : itemRewardType === "avatar_set_unlock"
                            ? "Avatar Set Bundle"
                          : itemRewardType === "avatar_unlock"
                            ? "Avatar Unlock"
                            : itemRewardType === "self_reward"
                              ? "Self Reward"
                              : "";
                      const avatarItemTypeLabel =
                        itemRewardType === "avatar_set_unlock"
                          ? "Full Set Bundle"
                          : itemRewardType === "avatar_unlock" && itemSetKey
                            ? "Set Part"
                            : itemRewardType === "avatar_unlock"
                              ? "Single Piece"
                              : "";
                      const shopItemHighlighted = Boolean(
                        shopHighlightSetKey &&
                          itemSetKey === shopHighlightSetKey &&
                          (!shopHighlightMode ||
                            (shopHighlightMode === "bundle" && itemRewardType === "avatar_set_unlock") ||
                            (shopHighlightMode === "parts" && itemRewardType === "avatar_unlock" && Boolean(itemSetKey)))
                      );
                      const rarityClass = `rarity-${String(item?.rarity || "common").toLowerCase()}`;
                      const buttonLabel = buyBusy
                        ? "Buying..."
                        : ownedOnce
                        ? "Owned"
                        : unavailable
                        ? unavailableReason || "Unavailable today"
                        : cannotAffordCoins
                        ? "Need more coins"
                        : "Buy";
                      return (
                        <li key={item.item_key} className={`shop-item ${item.owned ? "owned" : ""} ${shopItemHighlighted ? "highlight" : ""}`}>
                          <div className="shop-item-main">
                            <p className="shop-item-title">{item.title}</p>
                            <p className="shop-item-desc">{item.description}</p>
                            <p className="shop-item-meta">
                              {ICONS.coins} {prettyNumber(item.price_coins)} coins
                              {item.owned && !item.repeatable ? " | Owned" : ""}
                            </p>
                            <div className="shop-item-tags">
                              <span className={`rarity-badge ${rarityClass}`}>{item?.rarity_label || "Common"}</span>
                              {rewardTypeLabel ? <span>{rewardTypeLabel}</span> : null}
                              {avatarItemTypeLabel ? <span>{avatarItemTypeLabel}</span> : null}
                              {itemSetLabel ? <span>{itemSetLabel}</span> : null}
                              {bundleSavings > 0 ? <span>Save {prettyNumber(bundleSavings)} coins vs parts</span> : null}
                              {shopItemHighlighted ? <span className="shop-focus-tag">From Avatar Studio</span> : null}
                              <span>{stockLabel}</span>
                              {personalLimitLabel ? <span>{personalLimitLabel}</span> : null}
                              {unavailable ? <span className="shop-unavailable">{unavailableReason || "Unavailable today"}</span> : null}
                            </div>
                          </div>
                          <button
                            type="button"
                            className="secondary-btn"
                            disabled={disabled}
                            onClick={() => handleShopPurchase(item.item_key)}
                          >
                            {buttonLabel}
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </article>
              ))
            )}
          </section>

          <article className="panel shop-history-card">
            <div className="shop-category-header">
              <h3>Recent Purchases</h3>
              <span>{Array.isArray(shopData?.recent_purchases) ? shopData.recent_purchases.length : 0} recent</span>
            </div>
            <table className="history-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Coins</th>
                  <th>Purchased</th>
                </tr>
              </thead>
              <tbody>
                {!Array.isArray(shopData?.recent_purchases) || shopData.recent_purchases.length === 0 ? (
                  <tr>
                    <td colSpan={3}>No purchases yet.</td>
                  </tr>
                ) : (
                  shopData.recent_purchases.map((row) => (
                    <tr key={row.id}>
                      <td>{row.title}</td>
                      <td>{prettyNumber(row.price_coins)}</td>
                      <td>{String(row.purchased_at || "").replace("T", " ").slice(0, 19)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </article>
        </section>

        <section className="inventory-shell" hidden={activeView !== "inventory"}>
          <section className="panel inventory-toolbar">
            <h2>Inventory</h2>
            <span>{inventoryLoading ? "Refreshing..." : `${prettyNumber(inventorySummary?.total_purchases || 0)} purchases logged`}</span>
          </section>

          <section className="inventory-summary-grid">
            <article className="panel inventory-summary-card">
              <h3>Total Coins Spent</h3>
              <p>{prettyNumber(inventorySummary?.total_coins_spent || 0)}</p>
            </article>
            <article className="panel inventory-summary-card">
              <h3>Avatar Unlocks Owned</h3>
              <p>{prettyNumber(inventorySummary?.avatar_unlocks_owned || 0)}</p>
            </article>
            <article className="panel inventory-summary-card">
              <h3>Self Rewards Claimed</h3>
              <p>{prettyNumber(inventorySummary?.self_rewards_claimed || 0)}</p>
              <small>{prettyNumber(inventorySummary?.self_rewards_unclaimed || 0)} pending</small>
            </article>
            <article className="panel inventory-summary-card">
              <h3>Wallet Balance</h3>
              <p>{prettyNumber(coinBalance)}</p>
            </article>
          </section>

          <section className="inventory-grid">
            <article className="panel inventory-card">
              <div className="inventory-card-header">
                <h3>Owned Avatar Unlocks</h3>
                <span>{inventoryAvatarUnlockRows.length} unlocked</span>
              </div>
              <ul className="inventory-list">
                {inventoryAvatarUnlockRows.length === 0 ? (
                  <li className="empty-state">No avatar unlocks purchased yet.</li>
                ) : (
                  inventoryAvatarUnlockRows.map((row) => (
                    <li key={row.item_key} className="inventory-item">
                      <div>
                        <p className="inventory-item-title">{row.title}</p>
                        <p className="inventory-item-meta">
                          {row.rarity_label} | {humanizeKey(row.unlock_slot || "slot")} | {humanizeKey(row.unlock_value || "option")}
                        </p>
                      </div>
                      <small>{String(row.purchased_at || "").replace("T", " ").slice(0, 19)}</small>
                    </li>
                  ))
                )}
              </ul>
            </article>

            <article className="panel inventory-card">
              <div className="inventory-card-header">
                <h3>Reward Redemptions</h3>
                <span>{inventoryRewardRows.length} entries</span>
              </div>
              <ul className="inventory-list">
                {inventoryRewardRows.length === 0 ? (
                  <li className="empty-state">No self-reward redemptions yet.</li>
                ) : (
                  inventoryRewardRows.slice(0, 24).map((row) => (
                    <li key={row.id} className="inventory-item">
                      <div>
                        <p className="inventory-item-title">{row.title}</p>
                        <p className="inventory-item-meta">
                          {ICONS.coins} {prettyNumber(row.price_coins)} coins
                        </p>
                        <p className="inventory-item-meta">
                          {row.is_claimed ? `Claimed: ${formatDateTime(row.claimed_at)}` : "Not claimed yet"}
                        </p>
                      </div>
                      <div className="inventory-item-actions">
                        <small>{formatDateTime(row.purchased_at)}</small>
                        {!row.is_claimed ? (
                          <button
                            type="button"
                            className="secondary-btn"
                            disabled={inventoryRedeemBusyKey === `inventory-redeem-${row.id}`}
                            onClick={() => handleInventoryRewardRedeem(row.id)}
                          >
                            {inventoryRedeemBusyKey === `inventory-redeem-${row.id}` ? "Claiming..." : "Claim reward"}
                          </button>
                        ) : (
                          <span className="inventory-claimed-pill">Claimed</span>
                        )}
                      </div>
                    </li>
                  ))
                )}
              </ul>
            </article>
          </section>

          <article className="panel inventory-history-card">
            <div className="inventory-history-header">
              <h3>Purchase History</h3>
              <div className="inventory-filters">
                <label>
                  Category
                  <select value={inventoryCategoryFilter} onChange={(event) => setInventoryCategoryFilter(event.target.value)}>
                    {inventoryCategoryOptions.map((option) => (
                      <option key={option.key} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Type
                  <select value={inventoryTypeFilter} onChange={(event) => setInventoryTypeFilter(event.target.value)}>
                    {inventoryTypeOptions.map((option) => (
                      <option key={option.key} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>
            <table className="history-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Type</th>
                  <th>Coins</th>
                  <th>Purchased</th>
                </tr>
              </thead>
              <tbody>
                {filteredInventoryRows.length === 0 ? (
                  <tr>
                    <td colSpan={4}>No purchases match this filter.</td>
                  </tr>
                ) : (
                  filteredInventoryRows.map((row) => (
                    <tr key={row.id}>
                      <td>{row.title}</td>
                      <td>{humanizeKey(row.reward_type || "self_reward")}</td>
                      <td>{prettyNumber(row.price_coins)}</td>
                      <td>{String(row.purchased_at || "").replace("T", " ").slice(0, 19)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </article>

          <article className="panel inventory-spending-card">
            <div className="inventory-card-header">
              <h3>Last 14 Days Spend</h3>
              <span>{inventorySpendingRows.length} days</span>
            </div>
            <ul className="inventory-spending-list">
              {inventorySpendingRows.length === 0 ? (
                <li className="empty-state">No spending history available.</li>
              ) : (
                inventorySpendingRows.map((row) => (
                  <li key={row.date} className="inventory-spending-row">
                    <span>{row.label}</span>
                    <span>{prettyNumber(row.purchase_count)} purchases</span>
                    <span>{ICONS.coins} {prettyNumber(row.coins_spent)}</span>
                  </li>
                ))
              )}
            </ul>
          </article>
        </section>

        <section className="achievements-shell" hidden={activeView !== "achievements"}>
          <section className="panel achievements-toolbar">
            <h2>Achievements</h2>
            <span>{achievementsLoading ? "Refreshing..." : `${prettyNumber(achievementsSummary.unlocked)} unlocked`}</span>
          </section>

          <section className="achievements-summary-grid">
            <article className="panel achievements-summary-card">
              <h3>Unlocked</h3>
              <p>
                {prettyNumber(achievementsSummary.unlocked)} / {prettyNumber(achievementsSummary.total)}
              </p>
            </article>
            <article className="panel achievements-summary-card">
              <h3>Completion</h3>
              <p>{formatPercent(achievementsSummary.completion_rate)}</p>
            </article>
            <article className="panel achievements-summary-card">
              <h3>Locked</h3>
              <p>{prettyNumber(achievementsSummary.locked)}</p>
            </article>
            <article className="panel achievements-summary-card">
              <h3>New This Refresh</h3>
              <p>{prettyNumber(achievementsSummary.newly_unlocked)}</p>
            </article>
          </section>

          {achievementsLoading ? <p className="notice">Refreshing achievements...</p> : null}

          <section className="achievements-grid">
            <article className="panel achievements-list-card">
              <div className="inventory-card-header">
                <h3>All Achievements</h3>
                <span>{achievementRows.length} total</span>
              </div>
              <ul className="achievements-list">
                {achievementRows.length === 0 ? (
                  <li className="empty-state">No achievements configured.</li>
                ) : (
                  achievementRows.map((row) => (
                    <li key={row.key} className={`achievement-item ${row.unlocked ? "unlocked" : ""}`}>
                      <div className="achievement-main">
                        <p className="achievement-title">
                          <span>{row.icon || ICONS.achievements}</span> {row.title}
                        </p>
                        <p className="achievement-desc">{row.description}</p>
                        <p className="achievement-meta">
                          {row.rarity_label} | Reward: +{prettyNumber(row.reward_xp)} XP, +{prettyNumber(row.reward_coins)} coins
                        </p>
                      </div>
                      <div className="achievement-progress-box">
                        <div className="achievement-progress-top">
                          <span>
                            {prettyNumber(row.progress_value)} / {prettyNumber(row.target_value)}
                          </span>
                          <span>{formatPercent(row.progress_percent)}</span>
                        </div>
                        <div className="achievement-progress-track">
                          <span style={{ width: `${Math.max(0, Math.min(Number(row.progress_percent) || 0, 100))}%` }} />
                        </div>
                        <small>{row.unlocked ? `Unlocked ${formatDateTime(row.unlocked_at)}` : "Locked"}</small>
                      </div>
                    </li>
                  ))
                )}
              </ul>
            </article>

            <article className="panel achievements-recent-card">
              <div className="inventory-card-header">
                <h3>Recent Unlocks</h3>
                <span>{recentAchievementUnlocks.length}</span>
              </div>
              <ul className="inventory-list">
                {recentAchievementUnlocks.length === 0 ? (
                  <li className="empty-state">No new unlocks this session.</li>
                ) : (
                  recentAchievementUnlocks.map((row) => (
                    <li key={row.key} className="inventory-item">
                      <div>
                        <p className="inventory-item-title">
                          {row.icon || ICONS.achievements} {row.title}
                        </p>
                        <p className="inventory-item-meta">
                          +{prettyNumber(row.reward_xp)} XP | +{prettyNumber(row.reward_coins)} coins
                        </p>
                      </div>
                    </li>
                  ))
                )}
              </ul>
            </article>
          </section>
        </section>

        <section className="challenges-shell" hidden={activeView !== "challenges"}>
          <section className="panel challenges-toolbar">
            <h2>Challenges</h2>
            <span>{challengesLoading ? "Refreshing..." : `${prettyNumber(challengeSummary.claimable)} claimable`}</span>
          </section>

          <section className="challenges-summary-grid">
            <article className="panel challenges-summary-card">
              <h3>Total Active</h3>
              <p>{prettyNumber(challengeSummary.total)}</p>
            </article>
            <article className="panel challenges-summary-card">
              <h3>Completed</h3>
              <p>{prettyNumber(challengeSummary.completed)}</p>
            </article>
            <article className="panel challenges-summary-card">
              <h3>Claimable</h3>
              <p>{prettyNumber(challengeSummary.claimable)}</p>
            </article>
          </section>

          {challengesLoading ? <p className="notice">Refreshing challenges...</p> : null}

          <section className="challenges-window-grid">
            {challengeWindows.length === 0 ? (
              <article className="panel challenges-window-card">
                <p className="empty-state">No active challenges available.</p>
              </article>
            ) : (
              challengeWindows.map((windowRow) => {
                const windowKey = String(windowRow.window_type || "daily");
                const rows = Array.isArray(windowRow.challenges) ? windowRow.challenges : [];
                const summary = windowRow.summary || {};
                return (
                  <article key={windowKey} className="panel challenges-window-card">
                    <div className="challenges-window-header">
                      <div>
                        <h3>{humanizeKey(windowRow.window_type || "daily")} Challenges</h3>
                        <p>{windowRow.label || "-"}</p>
                      </div>
                      <small>Reset in {formatCountdownLabel(windowRow.seconds_until_reset)}</small>
                    </div>
                    <p className="challenges-window-meta">
                      Completed {prettyNumber(summary.completed || 0)} / {prettyNumber(summary.total || 0)} | Claimed{" "}
                      {prettyNumber(summary.claimed || 0)}
                    </p>
                    <ul className="challenges-list">
                      {rows.length === 0 ? (
                        <li className="empty-state">No challenges in this window.</li>
                      ) : (
                        rows.map((challenge) => {
                          const progressPercent = Math.max(0, Math.min(Number(challenge.progress_percent) || 0, 100));
                          const claimBusy = challengeBusyKey === `challenge-claim-${windowKey}-${challenge.key}`;
                          const canClaim = Boolean(challenge.claimable);
                          return (
                            <li key={`${windowKey}-${challenge.key}`} className={`challenge-item ${challenge.completed ? "done" : ""}`}>
                              <div className="challenge-main">
                                <p className="challenge-title">{challenge.title}</p>
                                <p className="challenge-desc">{challenge.description}</p>
                                <p className="challenge-reward">
                                  Reward: +{prettyNumber(challenge.reward_xp)} XP, +{prettyNumber(challenge.reward_coins)} coins
                                </p>
                                <div className="challenge-progress-track">
                                  <span style={{ width: `${progressPercent}%` }} />
                                </div>
                                <p className="challenge-progress-meta">
                                  {prettyNumber(challenge.progress_value)} / {prettyNumber(challenge.target_value)} ({formatPercent(challenge.progress_percent)})
                                </p>
                              </div>
                              <div className="challenge-actions">
                                <button
                                  type="button"
                                  className="secondary-btn"
                                  disabled={!canClaim || claimBusy}
                                  onClick={() => handleChallengeClaim(windowKey, challenge.key)}
                                >
                                  {claimBusy ? "Claiming..." : canClaim ? "Claim" : challenge.claimed ? "Claimed" : "In progress"}
                                </button>
                                {challenge.claimed_at ? <small>{formatDateTime(challenge.claimed_at)}</small> : null}
                              </div>
                            </li>
                          );
                        })
                      )}
                    </ul>
                  </article>
                );
              })
            )}
          </section>
        </section>

        <section className="timeline-shell" hidden={activeView !== "timeline"}>
          <section className="panel timeline-toolbar">
            <div>
              <h2>Activity Timeline</h2>
              <p>
                {timelineRange ? `${timelineRange.start} to ${timelineRange.end}` : "Choose a time range"}
              </p>
            </div>
            <div className="stats-range-switch">
              {TIMELINE_RANGE_OPTIONS.map((days) => (
                <button
                  key={`timeline-${days}`}
                  type="button"
                  className={`range-btn ${timelineRangeDays === days ? "active" : ""}`}
                  onClick={() => handleTimelineRangeChange(days)}
                  disabled={timelineLoading && timelineRangeDays === days}
                >
                  {days}d
                </button>
              ))}
            </div>
          </section>

          {timelineLoading ? <p className="notice">Refreshing timeline...</p> : null}

          <section className="timeline-summary-grid">
            <article className="panel timeline-summary-card">
              <h3>Events</h3>
              <p>{prettyNumber(timelineSummary.event_count || 0)}</p>
            </article>
            <article className="panel timeline-summary-card">
              <h3>Active Days</h3>
              <p>{prettyNumber(timelineSummary.active_days || 0)}</p>
            </article>
            <article className="panel timeline-summary-card">
              <h3>Range</h3>
              <p>{prettyNumber(timelineRange?.days || timelineRangeDays)} days</p>
            </article>
          </section>

          <section className="timeline-grid">
            <article className="panel timeline-day-card">
              <div className="inventory-card-header">
                <h3>By Day</h3>
                <span>{timelineDayBuckets.length} days</span>
              </div>
              <ul className="inventory-list">
                {timelineDayBuckets.length === 0 ? (
                  <li className="empty-state">No timeline activity in this range.</li>
                ) : (
                  timelineDayBuckets.map((row) => (
                    <li key={row.date} className="inventory-item">
                      <p className="inventory-item-title">{row.label}</p>
                      <p className="inventory-item-meta">{prettyNumber(row.count)} events</p>
                    </li>
                  ))
                )}
              </ul>
            </article>

            <article className="panel timeline-events-card">
              <div className="inventory-card-header">
                <h3>Event Feed</h3>
                <span>{timelineEvents.length} entries</span>
              </div>
              <ul className="timeline-events-list">
                {timelineEvents.length === 0 ? (
                  <li className="empty-state">No events found.</li>
                ) : (
                  timelineEvents.slice(0, 320).map((eventRow) => (
                    <li key={eventRow.id} className={`timeline-event event-${eventRow.event_type}`}>
                      <div>
                        <p className="timeline-event-title">{eventRow.title}</p>
                        <p className="timeline-event-meta">
                          {humanizeKey(eventRow.source || "timeline")} | {eventRow.detail || "Update"}
                        </p>
                      </div>
                      <small>{formatDateTime(eventRow.timestamp)}</small>
                    </li>
                  ))
                )}
              </ul>
            </article>
          </section>
        </section>

        <section className="leaderboard-shell" hidden={activeView !== "leaderboard"}>
          <section className="panel leaderboard-toolbar">
            <h2>Leaderboard</h2>
            <div className="leaderboard-toolbar-actions">
              <label>
                Show
                <select
                  value={leaderboardLimit}
                  onChange={(event) => handleLeaderboardLimitChange(Number(event.target.value))}
                  disabled={leaderboardLoading}
                >
                  {LEADERBOARD_LIMIT_OPTIONS.map((option) => (
                    <option key={`leaderboard-limit-${option}`} value={option}>
                      Top {option}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Scope
                <select
                  value={leaderboardScope}
                  onChange={(event) => handleLeaderboardScopeChange(event.target.value)}
                  disabled={leaderboardLoading}
                >
                  {LEADERBOARD_SCOPE_OPTIONS.map((option) => (
                    <option key={`leaderboard-scope-${option.key}`} value={option.key}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <span>
                {leaderboardLoading
                  ? "Refreshing..."
                  : `${activeLeaderboardEntries.length} entries loaded | ${leaderboardScopeLabel} (${prettyNumber(leaderboardScopeUserCount)} users)`}
              </span>
            </div>
          </section>

          <section className="leaderboard-summary-grid">
            <article className="panel leaderboard-summary-card">
              <h3>Board</h3>
              <p>{activeLeaderboardBoard?.label || "-"}</p>
            </article>
            <article className="panel leaderboard-summary-card">
              <h3>Your Rank</h3>
              <p>{prettyNumber(activeLeaderboardBoard?.viewer_rank || 0)}</p>
            </article>
            <article className="panel leaderboard-summary-card">
              <h3>Your Score</h3>
              <p>{prettyNumber(activeLeaderboardBoard?.viewer_score || 0)}</p>
            </article>
          </section>

          <section className="panel leaderboard-board-card">
            <div className="leaderboard-board-tabs">
              {leaderboardBoards.length === 0 ? (
                <span className="empty-state">No leaderboard data.</span>
              ) : (
                leaderboardBoards.map((board) => (
                  <button
                    key={board.key}
                    type="button"
                    className={`range-btn ${board.key === activeLeaderboardBoard?.key ? "active" : ""}`}
                    onClick={() => setLeaderboardBoardKey(board.key)}
                  >
                    {board.label}
                  </button>
                ))
              )}
            </div>

            <table className="history-table leaderboard-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Player</th>
                  <th>Level</th>
                  <th>Score</th>
                  <th>Coins</th>
                </tr>
              </thead>
              <tbody>
                {activeLeaderboardEntries.length === 0 ? (
                  <tr>
                    <td colSpan={5}>No entries for this board yet.</td>
                  </tr>
                ) : (
                  activeLeaderboardEntries.map((entry) => (
                    <tr key={`${activeLeaderboardBoard?.key || "board"}-${entry.user_id}`} className={entry.is_viewer ? "leaderboard-row-you" : ""}>
                      <td>#{prettyNumber(entry.rank)}</td>
                      <td>
                        {entry.display_name}
                        <small className="leaderboard-username"> @{entry.username}</small>
                      </td>
                      <td>{prettyNumber(entry.level)}</td>
                      <td>{prettyNumber(entry.score)}</td>
                      <td>{prettyNumber(entry.coins_balance)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </section>
        </section>

        <section className="season-pass-shell" hidden={activeView !== "season_pass"}>
          <section className="panel season-pass-toolbar">
            <h2>Season Pass</h2>
            <div className="season-pass-toolbar-actions">
              <div className="season-pass-toolbar-meta">
                <span>{seasonPassSeason?.label || "Current Season"}</span>
                <small>Resets in {formatCountdownLabel(seasonPassSeason?.seconds_until_reset)}</small>
              </div>
              {!seasonPassPremiumEnabled ? (
                <button type="button" className="secondary-btn" onClick={() => handleNavItemClick("/shop")}>
                  Buy Premium In Shop
                </button>
              ) : null}
            </div>
          </section>

          <section className="season-pass-summary-grid">
            <article className="panel season-pass-summary-card">
              <h3>Current Tier</h3>
              <p>{prettyNumber(seasonPassSummary.current_tier || 1)}</p>
            </article>
            <article className="panel season-pass-summary-card">
              <h3>Season XP</h3>
              <p>{prettyNumber(seasonPassSummary.xp_earned || 0)}</p>
            </article>
            <article className="panel season-pass-summary-card">
              <h3>Claimable</h3>
              <p>{prettyNumber(seasonPassSummary.claimable || 0)}</p>
              <small>
                Free: {prettyNumber(seasonPassSummary.claimable_free || 0)} | Premium:{" "}
                {prettyNumber(seasonPassSummary.claimable_premium || 0)}
              </small>
            </article>
            <article className="panel season-pass-summary-card">
              <h3>Premium Track</h3>
              <p>{seasonPassPremiumEnabled ? "Enabled" : "Disabled"}</p>
              <small>
                {seasonPassPremiumEnabled
                  ? `${prettyNumber(seasonPassSummary.claimable_premium || 0)} premium rewards claimable`
                  : "Buy the premium track unlock in Shop to enable bonus rewards"}
              </small>
            </article>
          </section>

          <article className="panel season-pass-progress-card">
            <div className="season-pass-progress-top">
              <span>Tier progress</span>
              <span>{formatPercent(seasonPassSummary.progress_percent)}</span>
            </div>
            <div className="season-pass-progress-track">
              <span style={{ width: `${Math.max(0, Math.min(Number(seasonPassSummary.progress_percent) || 0, 100))}%` }} />
            </div>
            <small>
              {prettyNumber(seasonPassSummary.xp_into_tier || 0)} / {prettyNumber(seasonPassSummary.xp_per_tier || 300)} XP in current tier
            </small>
            <small>{prettyNumber(seasonPassSummary.xp_needed_for_next_tier || 0)} XP needed for next tier</small>
          </article>

          {seasonPassLoading ? <p className="notice">Refreshing season pass...</p> : null}

          <section className="panel season-pass-tiers-card">
            <div className="inventory-card-header">
              <h3>Rewards</h3>
              <span>{seasonPassVisibleTiers.length} visible tiers</span>
            </div>
            <ul className="season-pass-tier-list">
              {seasonPassVisibleTiers.length === 0 ? (
                <li className="empty-state">No tiers available.</li>
              ) : (
                seasonPassVisibleTiers.map((tierRow) => {
                  const freeTrack = tierRow?.free && typeof tierRow.free === "object" ? tierRow.free : {};
                  const premiumTrack = tierRow?.premium && typeof tierRow.premium === "object" ? tierRow.premium : {};
                  const freeClaimBusy = seasonPassBusyKey === `season-pass-claim-${tierRow.tier}-free`;
                  const premiumClaimBusy = seasonPassBusyKey === `season-pass-claim-${tierRow.tier}-premium`;
                  const tierClaimable = Boolean(freeTrack.claimable || premiumTrack.claimable);
                  const tierClaimed = Boolean(freeTrack.claimed) && (!seasonPassPremiumEnabled || Boolean(premiumTrack.claimed));
                  return (
                    <li key={`season-tier-${tierRow.tier}`} className={`season-pass-tier-item ${tierClaimed ? "claimed" : tierClaimable ? "claimable" : ""}`}>
                      <div className="season-pass-tier-main">
                        <p className="season-pass-tier-title">Tier {tierRow.tier}</p>
                        <p className="season-pass-tier-meta">Unlock at {prettyNumber(tierRow.required_xp)} XP</p>
                        <div className="season-pass-track-grid">
                          <article
                            className={`season-pass-track-row track-free ${freeTrack.claimed ? "claimed" : freeTrack.claimable ? "claimable" : ""}`}
                          >
                            <div className="season-pass-track-main">
                              <p className="season-pass-track-label">Free Track</p>
                              <p className="season-pass-track-title">{freeTrack.reward_title || `Tier ${tierRow.tier} Free Reward`}</p>
                              <p className="season-pass-track-meta">{formatSeasonPassTrackReward(freeTrack, "No free reward.")}</p>
                            </div>
                            <div className="season-pass-tier-actions">
                              <button
                                type="button"
                                className="secondary-btn"
                                disabled={!freeTrack.claimable || freeClaimBusy}
                                onClick={() => handleSeasonPassTierClaim(tierRow.tier, "free")}
                              >
                                {freeClaimBusy ? "Claiming..." : freeTrack.claimable ? "Claim" : freeTrack.claimed ? "Claimed" : "Locked"}
                              </button>
                              {freeTrack.claimed_at ? <small>{formatDateTime(freeTrack.claimed_at)}</small> : null}
                            </div>
                          </article>
                          <article
                            className={`season-pass-track-row track-premium ${
                              !seasonPassPremiumEnabled ? "premium-disabled" : premiumTrack.claimed ? "claimed" : premiumTrack.claimable ? "claimable" : ""
                            }`}
                          >
                            <div className="season-pass-track-main">
                              <p className="season-pass-track-label">Premium Track</p>
                              <p className="season-pass-track-title">{premiumTrack.reward_title || `Tier ${tierRow.tier} Premium Reward`}</p>
                              <p className="season-pass-track-meta">
                                {formatSeasonPassTrackReward(premiumTrack, "Buy premium in Shop to unlock bonus rewards.")}
                              </p>
                            </div>
                            <div className="season-pass-tier-actions">
                              {!seasonPassPremiumEnabled ? (
                                <button type="button" className="secondary-btn" onClick={() => handleNavItemClick("/shop")}>
                                  Open Shop
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  className="secondary-btn"
                                  disabled={!premiumTrack.claimable || premiumClaimBusy}
                                  onClick={() => handleSeasonPassTierClaim(tierRow.tier, "premium")}
                                >
                                  {premiumClaimBusy
                                    ? "Claiming..."
                                    : premiumTrack.claimable
                                      ? "Claim"
                                      : premiumTrack.claimed
                                        ? "Claimed"
                                        : "Locked"}
                                </button>
                              )}
                              {premiumTrack.claimed_at ? <small>{formatDateTime(premiumTrack.claimed_at)}</small> : null}
                            </div>
                          </article>
                        </div>
                      </div>
                    </li>
                  );
                })
              )}
            </ul>
          </section>
        </section>

        <section className="avatar-shell" hidden={activeView !== "avatar"}>
          <section className="panel avatar-toolbar">
            <h2>Avatar Studio</h2>
            <span>
              {ICONS.coins} {prettyNumber(coinBalance)} coins
            </span>
          </section>

          <section className="avatar-grid">
            <article className="panel avatar-preview-card">
              <h3>Current Avatar</h3>
              {!avatarProfile ? (
                <p className="empty-state">{avatarLoading ? "Loading avatar..." : "No avatar profile available."}</p>
              ) : (
                <>
                  <div className={`avatar-preview palette-${avatarPreviewProfile?.palette || avatarProfile.palette || "cool"}`}>
                    <div className="avatar-figure" aria-label={`Avatar preview: ${avatarPreviewSummary}`}>
                      <p className="avatar-layer avatar-layer-body-type">{avatarVisual?.bodyTypeIcon || "\u26A7"}</p>
                      <p className="avatar-layer avatar-layer-head">{avatarVisual?.headIcon || ICONS.avatar}</p>
                      <p className="avatar-layer avatar-layer-top">{avatarVisual?.topIcon || "\u{1F455}"}</p>
                      <p className="avatar-layer avatar-layer-bottom">{avatarVisual?.bottomIcon || "\u{1F456}"}</p>
                      {avatarVisual?.accessoryIcon ? (
                        <p className="avatar-layer avatar-layer-accessory">{avatarVisual.accessoryIcon}</p>
                      ) : null}
                    </div>
                    <p className="avatar-preview-summary">{avatarPreviewSummary}</p>
                    <small>
                      {avatarVisual?.bodyTypeLabel || "Avatar"} body | {avatarVisual?.paletteLabel || "Cool Blue"} palette
                    </small>
                    <p className="avatar-active-set-label">
                      {avatarActiveSet?.label ? `${ICONS.spark} Active Set: ${avatarActiveSet.label}` : "Custom Mix"}
                    </p>
                    {avatarPreviewingSet && avatarPreviewSet?.label ? (
                      <p className="avatar-preview-mode-label">
                        {ICONS.spark} Previewing: {avatarPreviewSet.label} (not equipped)
                      </p>
                    ) : null}
                  </div>
                  <div className="avatar-current-chips">
                    {avatarProfileRows.map((row) => (
                      <span key={`avatar-current-${row.slot}`} className="avatar-current-chip">
                        <strong>{row.slotLabel}:</strong> {row.valueLabel}
                      </span>
                    ))}
                  </div>
                  {avatarPreviewingSet ? (
                    <button
                      type="button"
                      className="secondary-btn avatar-preview-reset-btn"
                      onClick={() => setAvatarPreviewSetKey("")}
                    >
                      Back to Equipped Avatar
                    </button>
                  ) : null}
                </>
              )}
            </article>

            <article className="panel avatar-editor-card">
              <h3>Customize</h3>
              <p className="avatar-editor-note">
                Choose your head type, outfit, and palette. Locked items can be unlocked from Shop.
              </p>
              <section className="avatar-set-panel">
                <div className="avatar-set-panel-header">
                  <h4>Theme Sets</h4>
                  <span>
                    {avatarUnlockedSetCount}/{avatarSetRows.length} unlocked
                  </span>
                </div>
                <div className="avatar-set-toolbar">
                  <select value={avatarSetFilter} onChange={(event) => setAvatarSetFilter(event.target.value)}>
                    {AVATAR_SET_FILTER_OPTIONS.map((option) => (
                      <option key={`avatar-set-filter-${option.key}`} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <select value={avatarSetSort} onChange={(event) => setAvatarSetSort(event.target.value)}>
                    {AVATAR_SET_SORT_OPTIONS.map((option) => (
                      <option key={`avatar-set-sort-${option.key}`} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {avatarSetFilterActive ? (
                    <button
                      type="button"
                      className="secondary-btn"
                      onClick={() => {
                        setAvatarSetFilter("all");
                        setAvatarSetSort("completion_desc");
                      }}
                    >
                      Reset
                    </button>
                  ) : null}
                </div>
                <p className="avatar-set-toolbar-meta">Showing {avatarVisibleSetRows.length} set(s)</p>
                {avatarSetPresets.length === 0 ? (
                  <p className="empty-state">No avatar sets available.</p>
                ) : avatarVisibleSetRows.length === 0 ? (
                  <p className="empty-state">No sets match your current filters.</p>
                ) : (
                  <div className="avatar-set-grid">
                    {avatarVisibleSetRows.map((setRow) => {
                      const {
                        preset,
                        presetIndex,
                        presetKey,
                        locked,
                        missingSlotCount,
                        totalSlotCount,
                        unlockedSlotCount,
                        completionPercent,
                        previewing,
                        equipped,
                        setBundleItem,
                        bundlePrice,
                        bundleSavings,
                        nextMissingPart,
                        nextPartSlotLabel,
                        bundleQuickBuyReady,
                        nextPartQuickBuyReady
                      } = setRow;
                      const busy = avatarBusyKey === `avatar-set-${presetKey}`;
                      const bundleBusy = Boolean(setBundleItem?.item_key) && shopBusyKey === `shop-buy-${setBundleItem?.item_key}`;
                      const partBusy = Boolean(nextMissingPart?.item_key) && shopBusyKey === `shop-buy-${nextMissingPart?.item_key}`;
                      return (
                        <article
                          key={`avatar-set-${presetKey || preset?.label || presetIndex}`}
                          className={`avatar-set-card ${equipped ? "active" : ""} ${locked ? "locked" : ""} ${previewing ? "previewing" : ""}`}
                        >
                          <span className="avatar-set-icon">{preset?.icon || ICONS.spark}</span>
                          <span className="avatar-set-title">{preset?.label || "Avatar Set"}</span>
                          <small>{preset?.description || "Full style preset"}</small>
                          <div className="avatar-set-progress-meta">
                            <span>
                              {prettyNumber(unlockedSlotCount)}/{prettyNumber(totalSlotCount)} parts
                            </span>
                            <span>{prettyNumber(completionPercent)}%</span>
                          </div>
                          <div className="avatar-set-progress-track">
                            <span style={{ width: `${Math.max(0, Math.min(completionPercent, 100))}%` }} />
                          </div>
                          <small>
                            {locked
                              ? missingSlotCount > 0
                                ? `${missingSlotCount} part${missingSlotCount === 1 ? "" : "s"} still locked`
                                : "Unlock in Shop"
                              : equipped
                                ? "Equipped"
                                : busy
                                  ? "Equipping..."
                                  : "Equip set"}
                          </small>
                          <small>
                            {setBundleItem
                              ? `${ICONS.coins} Bundle ${prettyNumber(bundlePrice)} coins${
                                  bundleSavings > 0 ? ` | Save ${prettyNumber(bundleSavings)}` : ""
                                }`
                              : "Bundle item unavailable"}
                          </small>
                          <small>
                            {nextMissingPart
                              ? `Next part: ${nextPartSlotLabel} (${prettyNumber(nextMissingPart.price_coins)} coins)`
                              : locked
                                ? "Shop parts to finish this set"
                                : "All set parts unlocked"}
                          </small>
                          <div className="avatar-set-actions">
                            <button
                              type="button"
                              className="secondary-btn"
                              onClick={() => handleAvatarSetPreview(presetKey)}
                            >
                              {previewing ? "Previewing" : "Preview"}
                            </button>
                            <button
                              type="button"
                              className="secondary-btn"
                              disabled={bundleBusy || Boolean(setBundleItem?.owned)}
                              onClick={() => {
                                if (bundleQuickBuyReady && setBundleItem?.item_key) {
                                  void handleAvatarSetQuickPurchase(setBundleItem.item_key, presetKey, "bundle");
                                  return;
                                }
                                handleAvatarSetShopOpen(presetKey, "bundle");
                              }}
                            >
                              {bundleBusy
                                ? "Buying..."
                                : setBundleItem?.owned
                                  ? "Bundle Owned"
                                  : bundleQuickBuyReady
                                    ? `Buy Bundle (${prettyNumber(bundlePrice)})`
                                    : "Shop Bundle"}
                            </button>
                            <button
                              type="button"
                              className="secondary-btn"
                              disabled={partBusy || !locked}
                              onClick={() => {
                                if (nextPartQuickBuyReady && nextMissingPart?.item_key) {
                                  void handleAvatarSetQuickPurchase(nextMissingPart.item_key, presetKey, "parts");
                                  return;
                                }
                                handleAvatarSetShopOpen(presetKey, "parts");
                              }}
                            >
                              {partBusy
                                ? "Buying..."
                                : !locked
                                  ? "All Parts Owned"
                                  : nextPartQuickBuyReady
                                    ? `Buy Next Part (${prettyNumber(nextMissingPart?.price_coins || 0)})`
                                    : "Shop Parts"}
                            </button>
                            <button
                              type="button"
                              className="secondary-btn"
                              disabled={busy || locked || equipped}
                              onClick={() => handleAvatarSetApply(preset)}
                            >
                              {busy ? "Equipping..." : equipped ? "Equipped" : "Equip"}
                            </button>
                          </div>
                        </article>
                      );
                    })}
                  </div>
                )}
              </section>
              {avatarOptionSlots.length === 0 ? (
                <p className="empty-state">No avatar options available.</p>
              ) : (
                avatarOptionSlots.map(([slot, options]) => (
                  <div key={slot} className="avatar-slot-group">
                    <div className="avatar-slot-header">
                      <h4>{AVATAR_SLOT_LABELS[slot] || humanizeKey(slot)}</h4>
                      <span>
                        {avatarSelectedLabelBySlot[slot] || "Not selected"} |{" "}
                        {Array.isArray(options) ? options.filter((option) => option?.unlocked).length : 0}/
                        {Array.isArray(options) ? options.length : 0} unlocked
                      </span>
                    </div>
                    <div className="avatar-options-row">
                      {Array.isArray(options) && options.length > 0 ? (
                        options.map((option) => {
                          const optionBusy = avatarBusyKey === `avatar-${slot}-${option.key}`;
                          const locked = !option.unlocked;
                          const isActive = avatarProfile?.[slot] === option.key;
                          return (
                            <button
                              key={`${slot}-${option.key}`}
                              type="button"
                              className={`avatar-option-btn ${isActive ? "active" : ""} ${locked ? "locked" : ""}`}
                              disabled={optionBusy || locked}
                              onClick={() => handleAvatarOptionSelect(slot, option.key)}
                            >
                              <span className="avatar-option-icon">{option.icon || "*"}</span>
                              <span>{option.label}</span>
                              {locked ? <small>Unlock in Shop</small> : isActive ? <small>Selected</small> : <small>Tap to equip</small>}
                            </button>
                          );
                        })
                      ) : (
                        <p className="empty-state">No options.</p>
                      )}
                    </div>
                  </div>
                ))
              )}
            </article>
          </section>
        </section>

        <section className="spaces-shell" hidden={activeView !== "spaces"}>
          <section className="panel spaces-toolbar">
            <h2>Shared Spaces</h2>
            <span>{spacesLoading ? "Syncing..." : `${spaceRows.length} spaces`}</span>
          </section>

          <section className="spaces-grid">
            <article className="panel spaces-list-card">
              <div className="spaces-list-header">
                <h3>Your Spaces</h3>
              </div>
              <form className="spaces-create-form" onSubmit={handleSpaceCreate}>
                <input
                  placeholder="Create new space"
                  value={spaceForm.name}
                  onChange={(event) => setSpaceForm({ name: event.target.value })}
                  required
                />
                <button type="submit" className="secondary-btn" disabled={spacesBusyKey === "space-create"}>
                  {spacesBusyKey === "space-create" ? "Creating..." : "Create"}
                </button>
              </form>

              <form className="spaces-join-form" onSubmit={handleSpaceInviteAccept}>
                <input
                  placeholder="Paste invite token"
                  value={spaceJoinForm.token}
                  onChange={(event) => setSpaceJoinForm({ token: event.target.value })}
                  required
                />
                <button type="submit" className="secondary-btn" disabled={spacesBusyKey === "space-invite-accept"}>
                  {spacesBusyKey === "space-invite-accept" ? "Joining..." : "Join Space"}
                </button>
              </form>

              <ul className="spaces-list">
                {spaceRows.length === 0 ? <li className="empty-state">No spaces yet. Create your first shared space.</li> : null}
                {spaceRows.map((space) => (
                  <li key={space.id}>
                    <button
                      type="button"
                      className={`space-list-item ${selectedSpaceId === space.id ? "active" : ""}`}
                      onClick={() => handleSpaceSelect(space.id)}
                    >
                      <div>
                        <p>{space.name}</p>
                        <small>
                          {space.member_count || 0} members | Role: {space.current_role}
                        </small>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </article>

            <article className="panel spaces-detail-card">
              {!selectedSpace ? (
                <p className="empty-state">Select a space to view members and permissions.</p>
              ) : (
                <>
                  <div className="spaces-detail-header">
                    <h3>{selectedSpace.name}</h3>
                    <span>{selectedSpace.member_count || selectedSpaceMembers.length} members</span>
                  </div>

                  <form className="spaces-rename-form" onSubmit={handleSpaceRename}>
                    <input
                      value={spaceRenameForm.name}
                      onChange={(event) => setSpaceRenameForm({ name: event.target.value })}
                      required
                      disabled={!selectedSpacePermissions.can_manage_space}
                    />
                    <button
                      type="submit"
                      className="secondary-btn"
                      disabled={!selectedSpacePermissions.can_manage_space || spacesBusyKey === "space-rename"}
                    >
                      {spacesBusyKey === "space-rename" ? "Saving..." : "Rename"}
                    </button>
                    {selectedSpacePermissions.can_delete_space ? (
                      <button
                        type="button"
                        className="secondary-btn danger"
                        disabled={spacesBusyKey === "space-delete"}
                        onClick={handleSpaceDelete}
                      >
                        {spacesBusyKey === "space-delete" ? "Deleting..." : "Delete Space"}
                      </button>
                    ) : null}
                  </form>

                  <section className="spaces-notification-preferences">
                    <div className="spaces-notification-header">
                      <h4>Space Reminder Mode</h4>
                      <span>{selectedSpaceNotificationPreference.label}</span>
                    </div>
                    <form className="spaces-notification-form" onSubmit={handleSpaceNotificationPreferenceSave}>
                      <select
                        value={spaceNotificationPreferenceMode}
                        onChange={(event) => setSpaceNotificationPreferenceMode(event.target.value)}
                        disabled={Boolean(spacesBusyKey)}
                      >
                        {SPACE_NOTIFICATION_MODE_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      <button
                        type="submit"
                        className="secondary-btn"
                        disabled={spacesBusyKey === "space-notification-preference-save"}
                      >
                        {spacesBusyKey === "space-notification-preference-save" ? "Saving..." : "Save Mode"}
                      </button>
                    </form>
                    <p className="settings-note">{selectedSpaceNotificationModeDescription}</p>

                    <div className="spaces-notification-header">
                      <h4>New Member Default</h4>
                      <span>{selectedSpaceNotificationDefault.label}</span>
                    </div>
                    <form className="spaces-notification-form" onSubmit={handleSpaceNotificationDefaultSave}>
                      <select
                        value={spaceNotificationDefaultMode}
                        onChange={(event) => setSpaceNotificationDefaultMode(event.target.value)}
                        disabled={!canManageSpaceNotificationDefault || Boolean(spacesBusyKey)}
                      >
                        {SPACE_NOTIFICATION_MODE_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      <button
                        type="submit"
                        className="secondary-btn"
                        disabled={!canManageSpaceNotificationDefault || spacesBusyKey === "space-notification-default-save"}
                      >
                        {spacesBusyKey === "space-notification-default-save" ? "Saving..." : "Save Default"}
                      </button>
                    </form>
                    {canManageSpaceNotificationDefault ? (
                      <>
                        <div className="spaces-notification-actions">
                          <button
                            type="button"
                            className="secondary-btn"
                            disabled={spacesBusyKey === "space-notification-default-apply"}
                            onClick={handleSpaceNotificationDefaultApplyToMembers}
                          >
                            {spacesBusyKey === "space-notification-default-apply"
                              ? "Applying..."
                              : "Apply To Existing Members"}
                          </button>
                        </div>
                        <p className="settings-note">{selectedSpaceNotificationDefaultDescription}</p>
                      </>
                    ) : (
                      <p className="settings-note">Only the space owner can change the new-member reminder default.</p>
                    )}

                    <div className="spaces-notification-header">
                      <h4>Quiet Hours (UTC)</h4>
                      <span>
                        {selectedSpaceNotificationQuietHours.enabled
                          ? `${selectedSpaceNotificationQuietHours.window_label}${
                              selectedSpaceNotificationQuietHours.is_active_now ? " (active now)" : ""
                            }`
                          : "Disabled"}
                      </span>
                    </div>
                    <form className="spaces-quiet-hours-form" onSubmit={handleSpaceNotificationQuietHoursSave}>
                      <label className="spaces-quiet-hours-toggle">
                        <input
                          type="checkbox"
                          checked={Boolean(spaceNotificationQuietHoursForm.enabled)}
                          onChange={(event) =>
                            setSpaceNotificationQuietHoursForm((prev) => ({
                              ...prev,
                              enabled: Boolean(event.target.checked)
                            }))
                          }
                          disabled={!canManageSpaceQuietHours || Boolean(spacesBusyKey)}
                        />
                        Enable
                      </label>
                      <label className="spaces-quiet-hours-field">
                        Start
                        <select
                          value={normalizeQuietHour(
                            spaceNotificationQuietHoursForm.start_hour_utc,
                            Number(DEFAULT_SPACE_QUIET_HOURS.start_hour_utc)
                          )}
                          onChange={(event) =>
                            setSpaceNotificationQuietHoursForm((prev) => ({
                              ...prev,
                              start_hour_utc: normalizeQuietHour(
                                event.target.value,
                                Number(DEFAULT_SPACE_QUIET_HOURS.start_hour_utc)
                              )
                            }))
                          }
                          disabled={!canManageSpaceQuietHours || Boolean(spacesBusyKey)}
                        >
                          {SPACE_QUIET_HOUR_OPTIONS.map((option) => (
                            <option key={`space-quiet-start-${option.value}`} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className="spaces-quiet-hours-field">
                        End
                        <select
                          value={normalizeQuietHour(
                            spaceNotificationQuietHoursForm.end_hour_utc,
                            Number(DEFAULT_SPACE_QUIET_HOURS.end_hour_utc)
                          )}
                          onChange={(event) =>
                            setSpaceNotificationQuietHoursForm((prev) => ({
                              ...prev,
                              end_hour_utc: normalizeQuietHour(
                                event.target.value,
                                Number(DEFAULT_SPACE_QUIET_HOURS.end_hour_utc)
                              )
                            }))
                          }
                          disabled={!canManageSpaceQuietHours || Boolean(spacesBusyKey)}
                        >
                          {SPACE_QUIET_HOUR_OPTIONS.map((option) => (
                            <option key={`space-quiet-end-${option.value}`} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </label>
                      <button
                        type="submit"
                        className="secondary-btn"
                        disabled={!canManageSpaceQuietHours || spacesBusyKey === "space-notification-quiet-hours-save"}
                      >
                        {spacesBusyKey === "space-notification-quiet-hours-save" ? "Saving..." : "Save Quiet Hours"}
                      </button>
                    </form>
                    <p className="settings-note">
                      Quiet hours suppress shared queue and invite-expiry reminders during the selected UTC window.
                    </p>
                  </section>

                  <section className="spaces-transfer">
                    <div className="spaces-transfer-header">
                      <h4>Space Snapshot</h4>
                      <span>Export/import members, queue, templates, and reminder modes</span>
                    </div>
                    <div className="spaces-transfer-actions">
                      <button
                        type="button"
                        className="secondary-btn"
                        disabled={!canManageSpace || spacesBusyKey === "space-export"}
                        onClick={handleSpaceExportSnapshot}
                      >
                        {spacesBusyKey === "space-export" ? "Preparing..." : "Download Snapshot"}
                      </button>
                    </div>
                    {!canManageSpace ? (
                      <p className="settings-note">You need space management access to export this snapshot.</p>
                    ) : null}
                    {canImportSpaceSnapshot ? (
                      <form className="spaces-transfer-form" onSubmit={handleSpaceImportSnapshot}>
                        <label>
                          Import mode
                          <select
                            value={spaceImportForm.mode}
                            onChange={(event) => {
                              const nextMode = event.target.value;
                              setSpaceImportForm((prev) => ({
                                ...prev,
                                mode: nextMode,
                                confirmation_phrase: ""
                              }));
                              setSpaceImportPreview(null);
                              setSpaceReplaceConfirmOpen(false);
                            }}
                            disabled={spacesBusyKey === "space-import" || spacesBusyKey === "space-import-preview"}
                          >
                            <option value="merge">Merge into current space</option>
                            <option value="replace">Replace current space data</option>
                          </select>
                        </label>
                        <label>
                          Snapshot JSON
                          <textarea
                            value={spaceImportForm.snapshot_text}
                            onChange={(event) => {
                              const nextText = event.target.value;
                              setSpaceImportForm((prev) => ({ ...prev, snapshot_text: nextText }));
                              setSpaceImportPreview(null);
                              setSpaceReplaceConfirmOpen(false);
                            }}
                            placeholder="Paste a LifeOS space snapshot JSON export"
                            rows={8}
                            required
                            disabled={spacesBusyKey === "space-import" || spacesBusyKey === "space-import-preview"}
                          />
                        </label>
                        {spaceImportForm.mode === "replace" ? (
                          <label>
                            Replace confirmation phrase
                            <input
                              type="text"
                              value={spaceImportForm.confirmation_phrase}
                              onChange={(event) =>
                                setSpaceImportForm((prev) => ({
                                  ...prev,
                                  confirmation_phrase: event.target.value
                                }))
                              }
                              placeholder={spaceImportRequiredPhrase || "REPLACE SPACE <space_id>"}
                              autoComplete="off"
                              required
                              disabled={spacesBusyKey === "space-import" || spacesBusyKey === "space-import-preview"}
                            />
                            <small className="spaces-transfer-confirmation-note">
                              Type exactly: <code>{spaceImportRequiredPhrase || "REPLACE SPACE <space_id>"}</code>
                            </small>
                          </label>
                        ) : null}
                        <div className="spaces-transfer-actions">
                          <button
                            type="button"
                            className="secondary-btn"
                            onClick={handleSpaceImportPreview}
                            disabled={spacesBusyKey === "space-import" || spacesBusyKey === "space-import-preview"}
                          >
                            {spacesBusyKey === "space-import-preview" ? "Checking..." : "Preview Import"}
                          </button>
                          <button
                            type="submit"
                            className="secondary-btn"
                            disabled={
                              spacesBusyKey === "space-import" ||
                              spacesBusyKey === "space-import-preview" ||
                              (spaceImportForm.mode === "replace" && !spaceReplacePreviewReady) ||
                              (spaceImportForm.mode === "replace" && !spaceImportConfirmationMatches)
                            }
                          >
                            {spacesBusyKey === "space-import" ? "Importing..." : "Import Snapshot"}
                          </button>
                        </div>
                        {spaceImportForm.mode === "replace" && !spaceReplacePreviewReady ? (
                          <p className="settings-note">Run Preview Import first. Replace imports require a fresh preview.</p>
                        ) : null}
                        {spaceImportForm.mode === "replace" &&
                        spaceImportForm.confirmation_phrase &&
                        !spaceImportConfirmationMatches ? (
                          <p className="spaces-transfer-confirmation-error">
                            Phrase must exactly match the required replace confirmation.
                          </p>
                        ) : null}
                        {spaceImportPreview ? (
                          <div className="spaces-transfer-preview">
                            <p className="spaces-transfer-preview-title">
                              Preview ({spaceImportPreview.mode === "replace" ? "replace" : "merge"} mode)
                            </p>
                            <ul className="spaces-transfer-preview-grid">
                              {spaceImportPreviewRows.map((row) => (
                                <li key={row.key} className="spaces-transfer-preview-item">
                                  <p>{row.label}</p>
                                  <small>
                                    Current {prettyNumber(row.current)} | After {prettyNumber(row.projected)} (
                                    {formatSignedNumber(row.diff)})
                                  </small>
                                  <small>
                                    Import {prettyNumber(row.imported)} | Skip {prettyNumber(row.skipped)}
                                  </small>
                                </li>
                              ))}
                            </ul>
                            {spaceImportPreviewWarnings.length > 0 ? (
                              <ul className="spaces-transfer-warning-list">
                                {spaceImportPreviewWarnings.map((warning, index) => (
                                  <li key={`${index}-${warning}`}>{warning}</li>
                                ))}
                              </ul>
                            ) : (
                              <p className="settings-note">No warnings found in this snapshot preview.</p>
                            )}
                            {spaceImportPreviewDetailRows.length > 0 ? (
                              <div className="spaces-transfer-reasons">
                                <p className="spaces-transfer-reasons-title">
                                  Skip reasons
                                  {spaceImportPreviewDetailLimit > 0
                                    ? ` (showing up to ${spaceImportPreviewDetailLimit} per section)`
                                    : ""}
                                </p>
                                <ul className="spaces-transfer-reason-list">
                                  {spaceImportPreviewDetailRows.map((row) => (
                                    <li key={row.id} className="spaces-transfer-reason-item">
                                      <p>
                                        <strong>{row.label}</strong>: {row.reason}
                                      </p>
                                      {row.itemSummary ? <small>{row.itemSummary}</small> : null}
                                    </li>
                                  ))}
                                </ul>
                                {spaceImportPreviewTruncatedTotal > 0 ? (
                                  <p className="settings-note">
                                    {prettyNumber(spaceImportPreviewTruncatedTotal)} additional skipped item detail(s) are
                                    not shown.
                                  </p>
                                ) : null}
                              </div>
                            ) : null}
                          </div>
                        ) : null}
                      </form>
                    ) : (
                      <p className="settings-note">Only the current space owner can import a space snapshot.</p>
                    )}
                  </section>

                  <section className="spaces-roles">
                    <div className="spaces-roles-header">
                      <h4>Role Templates</h4>
                      <span>Customize admin/member permissions per space</span>
                    </div>
                    <ul className="spaces-role-list">
                      {selectedSpaceRoleTemplates.length === 0 ? <li className="empty-state">No role templates found.</li> : null}
                      {selectedSpaceRoleTemplates.map((template) => {
                        const busyKey = `space-template-save-${template.role}`;
                        const edit = getSpaceTemplateEdit(template);
                        const editable = canManageRoleTemplates && template.editable;
                        return (
                          <li key={template.role} className="spaces-role-item">
                            <div className="spaces-role-top">
                              <p>{template.role}</p>
                              <span className={`member-pill role-${template.role}`}>{template.display_name}</span>
                            </div>

                            <div className="spaces-role-grid">
                              <label>
                                Display name
                                <input
                                  value={edit.display_name || ""}
                                  onChange={(event) =>
                                    handleSpaceTemplateEditChange(template.role, "display_name", event.target.value)
                                  }
                                  disabled={!editable || Boolean(spacesBusyKey)}
                                />
                              </label>
                              <label className="spaces-role-toggle">
                                <input
                                  type="checkbox"
                                  checked={Boolean(edit.can_manage_space)}
                                  onChange={(event) =>
                                    handleSpaceTemplateEditChange(template.role, "can_manage_space", event.target.checked)
                                  }
                                  disabled={!editable || Boolean(spacesBusyKey)}
                                />
                                Manage space
                              </label>
                              <label className="spaces-role-toggle">
                                <input
                                  type="checkbox"
                                  checked={Boolean(edit.can_manage_members)}
                                  onChange={(event) =>
                                    handleSpaceTemplateEditChange(template.role, "can_manage_members", event.target.checked)
                                  }
                                  disabled={!editable || Boolean(spacesBusyKey)}
                                />
                                Manage members
                              </label>
                              <label className="spaces-role-toggle">
                                <input
                                  type="checkbox"
                                  checked={Boolean(edit.can_assign_admin)}
                                  onChange={(event) =>
                                    handleSpaceTemplateEditChange(template.role, "can_assign_admin", event.target.checked)
                                  }
                                  disabled={!editable || Boolean(spacesBusyKey)}
                                />
                                Assign admin
                              </label>
                              <label className="spaces-role-toggle">
                                <input
                                  type="checkbox"
                                  checked={Boolean(edit.can_delete_space)}
                                  onChange={(event) =>
                                    handleSpaceTemplateEditChange(template.role, "can_delete_space", event.target.checked)
                                  }
                                  disabled={!editable || Boolean(spacesBusyKey)}
                                />
                                Delete space
                              </label>
                              <label className="spaces-role-toggle">
                                <input
                                  type="checkbox"
                                  checked={Boolean(edit.can_manage_invites)}
                                  onChange={(event) =>
                                    handleSpaceTemplateEditChange(template.role, "can_manage_invites", event.target.checked)
                                  }
                                  disabled={!editable || Boolean(spacesBusyKey)}
                                />
                                Manage invites
                              </label>
                              <label className="spaces-role-toggle">
                                <input
                                  type="checkbox"
                                  checked={Boolean(edit.can_manage_tasks)}
                                  onChange={(event) =>
                                    handleSpaceTemplateEditChange(template.role, "can_manage_tasks", event.target.checked)
                                  }
                                  disabled={!editable || Boolean(spacesBusyKey)}
                                />
                                Manage all tasks
                              </label>
                              <label className="spaces-role-toggle">
                                <input
                                  type="checkbox"
                                  checked={Boolean(edit.can_create_tasks)}
                                  onChange={(event) =>
                                    handleSpaceTemplateEditChange(template.role, "can_create_tasks", event.target.checked)
                                  }
                                  disabled={!editable || Boolean(spacesBusyKey)}
                                />
                                Create tasks
                              </label>
                              <label className="spaces-role-toggle">
                                <input
                                  type="checkbox"
                                  checked={Boolean(edit.can_complete_tasks)}
                                  onChange={(event) =>
                                    handleSpaceTemplateEditChange(template.role, "can_complete_tasks", event.target.checked)
                                  }
                                  disabled={!editable || Boolean(spacesBusyKey)}
                                />
                                Complete tasks
                              </label>
                            </div>

                            {editable ? (
                              <div className="spaces-role-actions">
                                <button
                                  type="button"
                                  className="secondary-btn"
                                  disabled={spacesBusyKey === busyKey}
                                  onClick={() => handleSpaceTemplateSave(template.role)}
                                >
                                  {spacesBusyKey === busyKey ? "Saving..." : "Save Template"}
                                </button>
                              </div>
                            ) : (
                              <p className="settings-note">
                                {template.role === "owner" ? "Owner permissions are always full access." : "Only owner can edit templates."}
                              </p>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  </section>

                  <section className="spaces-audit">
                    <div className="spaces-audit-header">
                      <h4>Audit Trail</h4>
                      <span>{selectedSpaceAuditSummary.total} recent events</span>
                    </div>
                    <form className="spaces-audit-filter-form" onSubmit={handleSpaceAuditFilterApply}>
                      <select
                        value={spaceAuditForm.event_type}
                        onChange={(event) =>
                          setSpaceAuditForm((prev) => ({ ...prev, event_type: event.target.value }))
                        }
                        disabled={spaceAuditLoading}
                      >
                        <option value="all">All event types</option>
                        {selectedSpaceAuditEventTypeOptions.map((eventType) => (
                          <option key={eventType} value={eventType}>
                            {humanizeKey(eventType)}
                          </option>
                        ))}
                      </select>
                      <select
                        value={spaceAuditForm.days}
                        onChange={(event) => setSpaceAuditForm((prev) => ({ ...prev, days: event.target.value }))}
                        disabled={spaceAuditLoading}
                      >
                        {SPACE_AUDIT_LOOKBACK_OPTIONS.map((option) => (
                          <option key={option.value || "all"} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      <input
                        value={spaceAuditForm.query}
                        onChange={(event) => setSpaceAuditForm((prev) => ({ ...prev, query: event.target.value }))}
                        placeholder="Search summary/details"
                        maxLength={120}
                        disabled={spaceAuditLoading}
                      />
                      <button type="submit" className="secondary-btn" disabled={spaceAuditLoading}>
                        {spaceAuditLoading ? "Filtering..." : "Apply"}
                      </button>
                      <button
                        type="button"
                        className="secondary-btn"
                        onClick={handleSpaceAuditFilterReset}
                        disabled={spaceAuditLoading}
                      >
                        Reset
                      </button>
                    </form>
                    <ul className="spaces-audit-list">
                      {selectedSpaceAuditEvents.length === 0 ? (
                        <li className="empty-state">No audit events yet for this space.</li>
                      ) : null}
                      {selectedSpaceAuditEvents.map((event) => {
                        const permissionEntries = Object.entries(event?.details?.permissions || {});
                        const displayNameChange = event?.details?.display_name || null;
                        const importTotals = event?.details?.totals || null;
                        const importMode = String(event?.details?.mode || "").trim();
                        const importSourceSpace = event?.details?.source_space || null;
                        const importSnapshotMeta = event?.details?.snapshot_meta || null;
                        const importImportedEntries = Object.entries(event?.details?.imported || {}).filter(
                          ([, value]) => Number(value || 0) > 0
                        );
                        const importSkippedEntries = Object.entries(event?.details?.skipped || {}).filter(
                          ([, value]) => Number(value || 0) > 0
                        );
                        return (
                          <li key={event.id} className="spaces-audit-item">
                            <div className="spaces-audit-top">
                              <p>{event.summary}</p>
                              <time dateTime={event.created_at || undefined}>
                                {event.created_at ? new Date(event.created_at).toLocaleString() : ""}
                              </time>
                            </div>
                            <p className="spaces-audit-meta">
                              {event.actor_display_name || "System"} | {humanizeKey(event.event_type)}
                            </p>
                            {displayNameChange ? (
                              <p className="spaces-audit-change">
                                Display Name: {displayNameChange.before || "(none)"} {"->"} {displayNameChange.after || "(none)"}
                              </p>
                            ) : null}
                            {event.event_type === "space_snapshot_imported" ? (
                              <>
                                <p className="spaces-audit-change">
                                  Mode: {importMode || "merge"} | Imported: {prettyNumber(importTotals?.imported)} | Skipped:{" "}
                                  {prettyNumber(importTotals?.skipped)}
                                </p>
                                {importSourceSpace?.name || importSourceSpace?.id ? (
                                  <p className="spaces-audit-change">
                                    Source Snapshot: {importSourceSpace?.name || "Space"}{" "}
                                    {importSourceSpace?.id ? `(ID ${importSourceSpace.id})` : ""}
                                  </p>
                                ) : null}
                                {importSnapshotMeta?.exported_at ? (
                                  <p className="spaces-audit-change">
                                    Snapshot Exported: {new Date(importSnapshotMeta.exported_at).toLocaleString()}
                                  </p>
                                ) : null}
                                {importImportedEntries.length > 0 ? (
                                  <p className="spaces-audit-change">
                                    Imported Buckets:{" "}
                                    {importImportedEntries
                                      .map(([key, value]) => `${humanizeKey(key)} ${prettyNumber(value)}`)
                                      .join(" | ")}
                                  </p>
                                ) : null}
                                {importSkippedEntries.length > 0 ? (
                                  <p className="spaces-audit-change">
                                    Skipped Buckets:{" "}
                                    {importSkippedEntries
                                      .map(([key, value]) => `${humanizeKey(key)} ${prettyNumber(value)}`)
                                      .join(" | ")}
                                  </p>
                                ) : null}
                              </>
                            ) : null}
                            {permissionEntries.length > 0 ? (
                              <div className="spaces-audit-chips">
                                {permissionEntries.map(([permissionKey, change]) => {
                                  const enabled = Boolean(change?.after);
                                  return (
                                    <span
                                      key={`${event.id}-${permissionKey}`}
                                      className={`audit-change-chip ${enabled ? "enabled" : "disabled"}`}
                                    >
                                      {humanizeKey(permissionKey)}: {enabled ? "On" : "Off"}
                                    </span>
                                  );
                                })}
                              </div>
                            ) : null}
                          </li>
                        );
                      })}
                    </ul>
                  </section>

                  <section className="spaces-invites">
                    <div className="spaces-invites-header">
                      <h4>Invite Links</h4>
                      <span>
                        {selectedSpaceInviteSummary.active} active / {selectedSpaceInviteSummary.total} total
                      </span>
                    </div>

                    {canManageSpaceInvites ? (
                      <div className="spaces-invite-analytics-grid">
                        <article className="spaces-invite-analytics-card">
                          <h5>{ICONS.stats} Lifetime</h5>
                          <p className="spaces-invite-analytics-rate">
                            {formatPercent(selectedSpaceInviteLifetime.conversion_rate_percent)} conversion
                          </p>
                          <p className="spaces-invite-analytics-line">
                            {prettyNumber(selectedSpaceInviteLifetime.created)} created
                          </p>
                          <p className="spaces-invite-analytics-line">
                            {prettyNumber(selectedSpaceInviteLifetime.accepted)} accepted |{" "}
                            {prettyNumber(selectedSpaceInviteLifetime.revoked)} revoked
                          </p>
                        </article>
                        <article className="spaces-invite-analytics-card">
                          <h5>{ICONS.bell} Last 7 Days</h5>
                          <p className="spaces-invite-analytics-rate">
                            {formatPercent(selectedSpaceInviteLast7Days.conversion_rate_percent)} conversion
                          </p>
                          <p className="spaces-invite-analytics-line">
                            {prettyNumber(selectedSpaceInviteLast7Days.created)} created
                          </p>
                          <p className="spaces-invite-analytics-line">
                            {prettyNumber(selectedSpaceInviteLast7Days.accepted_events)} accepts |{" "}
                            {prettyNumber(selectedSpaceInviteLast7Days.revoked_events)} revokes
                          </p>
                        </article>
                        <article className="spaces-invite-analytics-card">
                          <h5>{ICONS.compass} Last 30 Days</h5>
                          <p className="spaces-invite-analytics-rate">
                            {formatPercent(selectedSpaceInviteLast30Days.conversion_rate_percent)} conversion
                          </p>
                          <p className="spaces-invite-analytics-line">
                            {prettyNumber(selectedSpaceInviteLast30Days.created)} created
                          </p>
                          <p className="spaces-invite-analytics-line">
                            {prettyNumber(selectedSpaceInviteLast30Days.accepted_events)} accepts |{" "}
                            {prettyNumber(selectedSpaceInviteLast30Days.revoked_events)} revokes
                          </p>
                        </article>
                      </div>
                    ) : null}

                    {canManageSpaceInvites ? (
                      <div className="spaces-invite-role-grid">
                        {selectedSpaceInviteRoleKeys.map((roleKey) => {
                          const lifetimeRole = selectedSpaceInviteLifetimeByRole?.[roleKey] || defaultInviteRoleBreakdown[roleKey];
                          const last7Role = selectedSpaceInviteLast7DaysByRole?.[roleKey] || defaultInviteRoleBreakdown[roleKey];
                          const last30Role = selectedSpaceInviteLast30DaysByRole?.[roleKey] || defaultInviteRoleBreakdown[roleKey];
                          return (
                            <article key={roleKey} className="spaces-invite-role-card">
                              <h5>{selectedSpaceInviteRoleLabels?.[roleKey] || `${humanizeKey(roleKey)} links`}</h5>
                              <p className="spaces-invite-role-rate">
                                {formatPercent(lifetimeRole.conversion_rate_percent)} lifetime conversion
                              </p>
                              <p className="spaces-invite-role-line">
                                Lifetime: {prettyNumber(lifetimeRole.created)} created | {prettyNumber(lifetimeRole.accepted)} accepted
                              </p>
                              <p className="spaces-invite-role-line">
                                30d: {prettyNumber(last30Role.created)} created | {prettyNumber(last30Role.accepted_events)} accepts
                              </p>
                              <p className="spaces-invite-role-line">
                                7d: {prettyNumber(last7Role.created)} created | {prettyNumber(last7Role.accepted_events)} accepts
                              </p>
                            </article>
                          );
                        })}
                      </div>
                    ) : null}

                    {canManageSpaceInvites ? (
                      <form className="spaces-invite-create-form" onSubmit={handleSpaceInviteCreate}>
                        <select
                          value={spaceInviteForm.role}
                          onChange={(event) => setSpaceInviteForm((prev) => ({ ...prev, role: event.target.value }))}
                          disabled={Boolean(spacesBusyKey)}
                        >
                          <option value="member">Member</option>
                          {selectedSpacePermissions.can_assign_admin ? <option value="admin">Admin</option> : null}
                        </select>
                        <input
                          type="number"
                          min="1"
                          max="720"
                          step="1"
                          value={spaceInviteForm.expires_in_hours}
                          onChange={(event) =>
                            setSpaceInviteForm((prev) => ({ ...prev, expires_in_hours: event.target.value }))
                          }
                          disabled={Boolean(spacesBusyKey)}
                        />
                        <button type="submit" className="secondary-btn" disabled={spacesBusyKey === "space-invite-create"}>
                          {spacesBusyKey === "space-invite-create" ? "Creating..." : "Create Invite"}
                        </button>
                      </form>
                    ) : (
                      <p className="settings-note">Your current role template cannot manage invite links.</p>
                    )}

                    {canManageSpaceInvites ? (
                      <ul className="spaces-invite-list">
                        {selectedSpaceInvites.length === 0 ? <li className="empty-state">No invites created yet.</li> : null}
                        {selectedSpaceInvites.map((invite) => {
                          const revokeBusyKey = `space-invite-revoke-${invite.id}`;
                          const canRevokeInvite = invite.status === "active";
                          return (
                            <li key={invite.id} className={`spaces-invite-item status-${invite.status}`}>
                              <div className="spaces-invite-top">
                                <p>{invite.role} invite</p>
                                <span className={`invite-status-pill status-${invite.status}`}>{invite.status}</span>
                              </div>
                              <p className="spaces-invite-meta">
                                Created by {invite.created_by_display_name || `User ${invite.created_by_user_id}`}
                                {invite.expires_at ? ` | expires ${new Date(invite.expires_at).toLocaleString()}` : ""}
                              </p>
                              {invite.accepted_by_display_name ? (
                                <p className="spaces-invite-meta secondary">Accepted by {invite.accepted_by_display_name}</p>
                              ) : null}
                              <div className="spaces-invite-token-row">
                                <code>{invite.invite_token || ""}</code>
                              </div>
                              <div className="spaces-invite-actions">
                                <button
                                  type="button"
                                  className="secondary-btn"
                                  onClick={() => handleSpaceInviteCopy(invite.invite_token)}
                                >
                                  Copy Token
                                </button>
                                {canRevokeInvite ? (
                                  <button
                                    type="button"
                                    className="secondary-btn danger"
                                    disabled={spacesBusyKey === revokeBusyKey}
                                    onClick={() => handleSpaceInviteRevoke(invite.id)}
                                  >
                                    {spacesBusyKey === revokeBusyKey ? "Revoking..." : "Revoke"}
                                  </button>
                                ) : null}
                              </div>
                            </li>
                          );
                        })}
                      </ul>
                    ) : null}
                  </section>

                  <section className="spaces-tasks">
                    <div className="spaces-tasks-header">
                      <h4>Shared Queue</h4>
                      <span>
                        {selectedSpaceTaskSummary.todo} open / {selectedSpaceTaskSummary.done} done / {selectedSpaceTaskSummary.total} total
                      </span>
                    </div>

                    {canCreateSpaceTasks ? (
                      <form className="spaces-task-create-form" onSubmit={handleSpaceTaskCreate}>
                        <input
                          placeholder="Add shared task or quest"
                          value={spaceTaskForm.title}
                          onChange={(event) => setSpaceTaskForm((prev) => ({ ...prev, title: event.target.value }))}
                          required
                          disabled={Boolean(spacesBusyKey)}
                        />
                        <select
                          value={spaceTaskForm.task_type}
                          onChange={(event) => setSpaceTaskForm((prev) => ({ ...prev, task_type: event.target.value }))}
                          disabled={Boolean(spacesBusyKey)}
                        >
                          <option value="task">Task</option>
                          <option value="quest">Quest</option>
                        </select>
                        <select
                          value={spaceTaskForm.priority}
                          onChange={(event) => setSpaceTaskForm((prev) => ({ ...prev, priority: event.target.value }))}
                          disabled={Boolean(spacesBusyKey)}
                        >
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                        </select>
                        <input
                          type="number"
                          min="1"
                          step="1"
                          value={spaceTaskForm.xp_reward}
                          onChange={(event) => setSpaceTaskForm((prev) => ({ ...prev, xp_reward: event.target.value }))}
                          disabled={Boolean(spacesBusyKey)}
                        />
                        <input
                          type="date"
                          value={spaceTaskForm.due_on}
                          onChange={(event) => setSpaceTaskForm((prev) => ({ ...prev, due_on: event.target.value }))}
                          disabled={Boolean(spacesBusyKey)}
                        />
                        <button type="submit" className="secondary-btn" disabled={spacesBusyKey === "space-task-create"}>
                          {spacesBusyKey === "space-task-create" ? "Adding..." : "Add Task"}
                        </button>
                      </form>
                    ) : (
                      <p className="settings-note">You can view shared tasks but cannot create them in this space.</p>
                    )}

                    <ul className="spaces-task-list">
                      {selectedSpaceTasks.length === 0 ? <li className="empty-state">No shared tasks yet.</li> : null}
                      {selectedSpaceTasks.map((task) => {
                        const saveBusyKey = `space-task-save-${task.id}`;
                        const deleteBusyKey = `space-task-delete-${task.id}`;
                        const completeBusyKey = `space-task-complete-${task.id}`;
                        const canManageTask = canManageAnySpaceTask || Number(task.created_by_user_id) === Number(authUser?.id);
                        const edit = getSpaceTaskEdit(task);

                        return (
                          <li key={task.id} className={`spaces-task-item ${task.status === "done" ? "is-done" : ""}`}>
                            <div className="spaces-task-title-row">
                              <p>
                                {TASK_TYPE_ICON[task.task_type] || ICONS.tasks} {task.title}
                              </p>
                              <span className={`task-status-pill ${task.status === "done" ? "status-done" : "status-todo"}`}>
                                {task.status}
                              </span>
                            </div>
                            <p className="spaces-task-meta">
                              {task.task_type_label} | {task.priority} priority | {task.xp_reward} XP
                              {task.due_on ? ` | due ${task.due_on}` : ""}
                            </p>
                            <p className="spaces-task-meta secondary">
                              Created by {task.created_by_display_name || `User ${task.created_by_user_id}`}
                              {task.completed_by_display_name ? ` | Completed by ${task.completed_by_display_name}` : ""}
                            </p>

                            {canManageTask ? (
                              <div className="spaces-task-edit-grid">
                                <input
                                  value={edit.title}
                                  onChange={(event) => handleSpaceTaskEditChange(task.id, "title", event.target.value)}
                                  disabled={Boolean(spacesBusyKey)}
                                />
                                <select
                                  value={edit.task_type}
                                  onChange={(event) => handleSpaceTaskEditChange(task.id, "task_type", event.target.value)}
                                  disabled={Boolean(spacesBusyKey)}
                                >
                                  <option value="task">Task</option>
                                  <option value="quest">Quest</option>
                                </select>
                                <select
                                  value={edit.priority}
                                  onChange={(event) => handleSpaceTaskEditChange(task.id, "priority", event.target.value)}
                                  disabled={Boolean(spacesBusyKey)}
                                >
                                  <option value="low">Low</option>
                                  <option value="medium">Medium</option>
                                  <option value="high">High</option>
                                </select>
                                <input
                                  type="number"
                                  min="1"
                                  step="1"
                                  value={edit.xp_reward}
                                  onChange={(event) => handleSpaceTaskEditChange(task.id, "xp_reward", event.target.value)}
                                  disabled={Boolean(spacesBusyKey)}
                                />
                                <input
                                  type="date"
                                  value={edit.due_on || ""}
                                  onChange={(event) => handleSpaceTaskEditChange(task.id, "due_on", event.target.value)}
                                  disabled={Boolean(spacesBusyKey)}
                                />
                                <select
                                  value={edit.status}
                                  onChange={(event) => handleSpaceTaskEditChange(task.id, "status", event.target.value)}
                                  disabled={Boolean(spacesBusyKey)}
                                >
                                  <option value="todo">Todo</option>
                                  <option value="done">Done</option>
                                </select>
                              </div>
                            ) : null}

                            <div className="spaces-task-actions">
                              {task.status !== "done" && canCompleteSpaceTasks ? (
                                <button
                                  type="button"
                                  className="secondary-btn"
                                  disabled={spacesBusyKey === completeBusyKey}
                                  onClick={() => handleSpaceTaskComplete(task.id)}
                                >
                                  {spacesBusyKey === completeBusyKey ? "Working..." : "Complete"}
                                </button>
                              ) : null}
                              {canManageTask ? (
                                <button
                                  type="button"
                                  className="secondary-btn"
                                  disabled={spacesBusyKey === saveBusyKey}
                                  onClick={() => handleSpaceTaskSave(task.id)}
                                >
                                  {spacesBusyKey === saveBusyKey ? "Saving..." : "Save"}
                                </button>
                              ) : null}
                              {canManageTask ? (
                                <button
                                  type="button"
                                  className="secondary-btn danger"
                                  disabled={spacesBusyKey === deleteBusyKey}
                                  onClick={() => handleSpaceTaskDelete(task.id)}
                                >
                                  {spacesBusyKey === deleteBusyKey ? "Deleting..." : "Delete"}
                                </button>
                              ) : null}
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  </section>

                  <section className="spaces-members">
                    <div className="spaces-members-header">
                      <h4>Members</h4>
                      <span>{selectedSpace.current_role ? `You are ${selectedSpace.current_role}` : ""}</span>
                    </div>

                    {selectedSpacePermissions.can_manage_members ? (
                      <form className="spaces-member-add-form" onSubmit={handleSpaceMemberAdd}>
                        <input
                          placeholder="Username or email"
                          value={spaceMemberForm.identifier}
                          onChange={(event) =>
                            setSpaceMemberForm((prev) => ({ ...prev, identifier: event.target.value }))
                          }
                          required
                        />
                        <select
                          value={spaceMemberForm.role}
                          onChange={(event) => setSpaceMemberForm((prev) => ({ ...prev, role: event.target.value }))}
                        >
                          <option value="member">Member</option>
                          {selectedSpacePermissions.can_assign_admin ? <option value="admin">Admin</option> : null}
                        </select>
                        <button
                          type="submit"
                          className="secondary-btn"
                          disabled={spacesBusyKey === "space-member-add"}
                        >
                          {spacesBusyKey === "space-member-add" ? "Adding..." : "Add Member"}
                        </button>
                      </form>
                    ) : (
                      <p className="settings-note">You can view members but cannot manage them in this space.</p>
                    )}

                    <ul className="spaces-member-list">
                      {selectedSpaceMembers.map((member) => {
                        const roleBusyKey = `space-member-role-${member.user_id}`;
                        const removeBusyKey = `space-member-remove-${member.user_id}`;
                        const canManageRole = selectedSpacePermissions.can_assign_admin && !member.is_owner;
                        const canRemoveMember =
                          (selectedSpacePermissions.can_manage_members && !member.is_owner) || member.is_self;

                        return (
                          <li key={member.user_id} className="spaces-member-item">
                            <div className="spaces-member-meta">
                              <p>
                                {member.display_name}{" "}
                                {member.is_self ? <span className="member-pill role-member">You</span> : null}
                              </p>
                              <small>@{member.username || `user${member.user_id}`}</small>
                            </div>
                            <div className="spaces-member-actions">
                              {member.is_owner ? (
                                <span className="member-pill role-owner">Owner</span>
                              ) : (
                                <select
                                  value={member.role}
                                  disabled={!canManageRole || spacesBusyKey === roleBusyKey}
                                  onChange={(event) => handleSpaceMemberRoleChange(member.user_id, event.target.value)}
                                >
                                  <option value="member">Member</option>
                                  <option value="admin">Admin</option>
                                </select>
                              )}
                              {canRemoveMember ? (
                                <button
                                  type="button"
                                  className="secondary-btn danger"
                                  disabled={spacesBusyKey === removeBusyKey}
                                  onClick={() => handleSpaceMemberRemove(member.user_id)}
                                >
                                  {spacesBusyKey === removeBusyKey ? "Working..." : member.is_self ? "Leave" : "Remove"}
                                </button>
                              ) : null}
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  </section>
                </>
              )}
            </article>
          </section>
        </section>

        <section className="settings-shell" hidden={activeView !== "settings"}>
          <article className="panel settings-card">
            <h2>Profile</h2>
            <form className="settings-form" onSubmit={handleProfileUpdate}>
              <label>
                Display name
                <input
                  value={profileForm.display_name}
                  onChange={(event) => setProfileForm((prev) => ({ ...prev, display_name: event.target.value }))}
                  required
                />
              </label>
              <label>
                Username
                <input
                  value={profileForm.username}
                  onChange={(event) => setProfileForm((prev) => ({ ...prev, username: event.target.value }))}
                  required
                />
              </label>
              <label>
                Email
                <input
                  type="email"
                  value={profileForm.email}
                  onChange={(event) => setProfileForm((prev) => ({ ...prev, email: event.target.value }))}
                  required
                />
              </label>
              <button type="submit" className="secondary-btn" disabled={settingsBusyKey === "profile"}>
                {settingsBusyKey === "profile" ? "Saving..." : "Save Profile"}
              </button>
            </form>
          </article>

          <article className="panel settings-card">
            <h2>Password</h2>
            <form className="settings-form" onSubmit={handlePasswordUpdate}>
              <label>
                Current password
                <input
                  type="password"
                  value={passwordForm.current_password}
                  onChange={(event) => setPasswordForm((prev) => ({ ...prev, current_password: event.target.value }))}
                  required
                />
              </label>
              <label>
                New password
                <input
                  type="password"
                  value={passwordForm.new_password}
                  onChange={(event) => setPasswordForm((prev) => ({ ...prev, new_password: event.target.value }))}
                  required
                />
              </label>
              <label>
                Confirm new password
                <input
                  type="password"
                  value={passwordForm.confirm_new_password}
                  onChange={(event) => setPasswordForm((prev) => ({ ...prev, confirm_new_password: event.target.value }))}
                  required
                />
              </label>
              <button type="submit" className="secondary-btn" disabled={settingsBusyKey === "password"}>
                {settingsBusyKey === "password" ? "Updating..." : "Update Password"}
              </button>
            </form>
            <p className="settings-note">
              Forgot your password? Use the recovery forms on the login screen to generate and apply a reset token.
            </p>
          </article>

          <article className="panel settings-card">
            <h2>Reminder Channels</h2>
            <p className="settings-note">
              Configure optional digest delivery by email and SMS. Providers: email <strong>{reminderProviders.email}</strong>,
              sms <strong>{reminderProviders.sms}</strong>.
            </p>
            <form className="settings-form" onSubmit={handleReminderSettingsSave}>
              <label className="settings-check">
                <input
                  type="checkbox"
                  checked={Boolean(reminderSettingsForm.in_app_enabled)}
                  onChange={(event) =>
                    setReminderSettingsForm((prev) => ({ ...prev, in_app_enabled: event.target.checked }))
                  }
                />
                Enable in-app reminder center
              </label>
              <label className="settings-check">
                <input
                  type="checkbox"
                  checked={Boolean(reminderSettingsForm.email_enabled)}
                  onChange={(event) =>
                    setReminderSettingsForm((prev) => ({ ...prev, email_enabled: event.target.checked }))
                  }
                />
                Enable email reminders
              </label>
              <label>
                Reminder email address
                <input
                  type="email"
                  value={reminderSettingsForm.email_address}
                  onChange={(event) =>
                    setReminderSettingsForm((prev) => ({ ...prev, email_address: event.target.value }))
                  }
                />
              </label>
              <label className="settings-check">
                <input
                  type="checkbox"
                  checked={Boolean(reminderSettingsForm.sms_enabled)}
                  onChange={(event) =>
                    setReminderSettingsForm((prev) => ({ ...prev, sms_enabled: event.target.checked }))
                  }
                />
                Enable SMS reminders
              </label>
              <label>
                Reminder phone number
                <input
                  value={reminderSettingsForm.phone_number}
                  onChange={(event) =>
                    setReminderSettingsForm((prev) => ({ ...prev, phone_number: event.target.value }))
                  }
                  placeholder="+15551234567"
                />
              </label>
              <label>
                Digest hour (UTC)
                <input
                  type="number"
                  min="0"
                  max="23"
                  value={reminderSettingsForm.digest_hour_utc}
                  onChange={(event) =>
                    setReminderSettingsForm((prev) => ({ ...prev, digest_hour_utc: event.target.value }))
                  }
                />
              </label>
              <button type="submit" className="secondary-btn" disabled={settingsBusyKey === "reminders-save"}>
                {settingsBusyKey === "reminders-save" ? "Saving..." : "Save Reminder Settings"}
              </button>
            </form>

            <form className="settings-form reminder-test-form" onSubmit={handleReminderTestSend}>
              <label>
                Test channel
                <select
                  value={reminderTestForm.channel}
                  onChange={(event) => setReminderTestForm((prev) => ({ ...prev, channel: event.target.value }))}
                >
                  <option value="all">All enabled channels</option>
                  <option value="email">Email only</option>
                  <option value="sms">SMS only</option>
                </select>
              </label>
              <label>
                Test message (optional)
                <input
                  value={reminderTestForm.message}
                  onChange={(event) => setReminderTestForm((prev) => ({ ...prev, message: event.target.value }))}
                  placeholder="This is a test reminder from LifeOS."
                />
              </label>
              <div className="settings-inline-actions">
                <button type="submit" className="secondary-btn" disabled={settingsBusyKey === "reminders-test"}>
                  {settingsBusyKey === "reminders-test" ? "Sending..." : "Send Test Reminder"}
                </button>
                <button type="button" className="secondary-btn" disabled={settingsBusyKey === "reminders-run"} onClick={handleReminderRunNow}>
                  {settingsBusyKey === "reminders-run" ? "Running..." : "Run Digest Now"}
                </button>
                <button type="button" className="secondary-btn" disabled={settingsBusyKey === "reminders-logs"} onClick={handleReminderRefreshLogs}>
                  {settingsBusyKey === "reminders-logs" ? "Refreshing..." : "Refresh Delivery Log"}
                </button>
              </div>
            </form>

            {reminderSettingsLoading ? <p className="notice">Loading reminder channel settings...</p> : null}
            <div className="reminder-delivery-block">
              <h3>Recent Deliveries</h3>
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Time (UTC)</th>
                    <th>Channel</th>
                    <th>Status</th>
                    <th>Recipient</th>
                  </tr>
                </thead>
                <tbody>
                  {reminderDeliveries.length === 0 ? (
                    <tr>
                      <td colSpan={4}>No reminder deliveries yet.</td>
                    </tr>
                  ) : (
                    reminderDeliveries.map((row) => (
                      <tr key={row.id}>
                        <td>{String(row.created_at || "").replace("T", " ").slice(0, 19)}</td>
                        <td>{row.channel}</td>
                        <td>{row.status}</td>
                        <td>{row.recipient}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </article>

          <article className="panel settings-card">
            <h2>Export Snapshot</h2>
            <p className="settings-note">
              Download your current tasks, habits, goals, and XP history as JSON.
            </p>
            <button type="button" className="secondary-btn" disabled={settingsBusyKey === "export"} onClick={handleExportSnapshot}>
              {settingsBusyKey === "export" ? "Preparing..." : "Download Snapshot"}
            </button>
          </article>

          <article className="panel settings-card">
            <h2>Import Snapshot</h2>
            <form className="settings-form" onSubmit={handleImportSnapshot}>
              <label>
                Import mode
                <select
                  value={importForm.mode}
                  onChange={(event) => setImportForm((prev) => ({ ...prev, mode: event.target.value }))}
                >
                  <option value="merge">Merge into current data</option>
                  <option value="replace">Replace current data</option>
                </select>
              </label>
              <label className="settings-check">
                <input
                  type="checkbox"
                  checked={importForm.apply_profile}
                  onChange={(event) => setImportForm((prev) => ({ ...prev, apply_profile: event.target.checked }))}
                />
                Apply display name from snapshot
              </label>
              <label>
                Snapshot JSON
                <textarea
                  value={importForm.snapshot_text}
                  onChange={(event) => setImportForm((prev) => ({ ...prev, snapshot_text: event.target.value }))}
                  placeholder='Paste JSON from a LifeOS snapshot export here'
                  rows={10}
                  required
                />
              </label>
              <button type="submit" className="secondary-btn" disabled={settingsBusyKey === "import"}>
                {settingsBusyKey === "import" ? "Importing..." : "Import Snapshot"}
              </button>
            </form>
          </article>

          <article className="xp-rules-panel">
            <div className="xp-rules-header">
              <h3>XP Rules Engine</h3>
              <span>{xpRuleEntries.length} rules</span>
            </div>
            <ul className="xp-rules-list">
              {xpRuleEntries.map(([ruleKey, points]) => (
                <li key={ruleKey} className="xp-rule-item">
                  <span className="xp-rule-key">{formatXpRuleKey(ruleKey)}</span>
                  <strong>{points} XP</strong>
                </li>
              ))}
            </ul>
          </article>
        </section>

        <section className="content-grid" hidden={activeView !== "dashboard"}>
          <article className="panel tasks-panel">
            <div className="panel-title-row">
              <h2>Today's Tasks</h2>
              <span>{dashboard.today_label}</span>
            </div>
            <ul className="task-list">
              {dashboard.today_tasks.length === 0 ? <li className="empty-state">No tasks queued for today.</li> : null}
              {dashboard.today_tasks.map((task) => (
                <li key={task.id} className="task-item">
                  <div className="task-main">
                    <span className="task-icon">{TASK_TYPE_ICON[task.task_type] || TASK_TYPE_ICON.task}</span>
                    <div>
                      <p className="task-title">{task.title}</p>
                      <p className="task-meta">{task.task_type_label} | {task.xp_effective ?? task.xp_reward} XP</p>
                    </div>
                  </div>
                  <button className="complete-btn" type="button" disabled={completingTaskId === task.id} onClick={() => handleCompleteTask(task.id)}>
                    {completingTaskId === task.id ? "Working..." : "Complete"}
                  </button>
                </li>
              ))}
            </ul>
            <div className="history-block">
              <h3>Recent Completions</h3>
              <table className="history-table">
                <thead>
                  <tr><th>Task</th><th>XP Earned</th><th>Completed</th></tr>
                </thead>
                <tbody>
                  {dashboard.recent_completions.length === 0 ? (
                    <tr><td colSpan={3}>No completed tasks yet.</td></tr>
                  ) : (
                    dashboard.recent_completions.map((entry) => (
                      <tr key={entry.id}><td>{entry.title}</td><td>{entry.xp_earned} XP</td><td>{entry.completed_label}</td></tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </article>

          <aside className="side-panels">
            <article className="panel streak-card">
              <h2>Streak Status</h2>
              <p className="streak-big">{ICONS.fire} {dashboard.stats.current_streak} Days</p>
              <p>Keep it up.</p>
            </article>
            <article className="panel quote-card">
              <h2>Motivational Quote</h2>
              <blockquote>"{dashboard.quote.text}"</blockquote>
              <p className="quote-author">- {dashboard.quote.author}</p>
            </article>
            <article className="panel goal-card">
              <h2>Goal Progress</h2>
              <ul className="goal-list">{dashboard.goals.map((goal) => <GoalItem key={goal.id} goal={goal} />)}</ul>
            </article>
          </aside>
        </section>

        <section className="panel crud-panel" hidden={activeView !== "tasks"}>
          <div className="crud-header">
            <h2>Manage Tasks, Habits, Goals</h2>
            <span>{crudLoading ? "Syncing..." : "Synced"}</span>
          </div>

          <div className="crud-grid">
            <article className="crud-column">
              <h3>Tasks</h3>
              <section className="crud-task-toolbar">
                <div className="crud-filter-meta">
                  Showing {prettyNumber(filteredTaskRows.length)} of {prettyNumber(taskRows.length)} tasks
                </div>
                <div className="crud-filter-grid">
                  <input
                    placeholder="Search title, type, priority, due date..."
                    value={taskSearchQuery}
                    onChange={(event) => setTaskSearchQuery(event.target.value)}
                  />
                  <select value={taskStatusFilter} onChange={(event) => setTaskStatusFilter(event.target.value)}>
                    {TASK_FILTER_STATUS_OPTIONS.map((option) => (
                      <option key={`task-status-filter-${option.key}`} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <select value={taskTypeFilter} onChange={(event) => setTaskTypeFilter(event.target.value)}>
                    {TASK_FILTER_TYPE_OPTIONS.map((option) => (
                      <option key={`task-type-filter-${option.key}`} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <select value={taskPriorityFilter} onChange={(event) => setTaskPriorityFilter(event.target.value)}>
                    {TASK_FILTER_PRIORITY_OPTIONS.map((option) => (
                      <option key={`task-priority-filter-${option.key}`} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <select value={taskSortMode} onChange={(event) => setTaskSortMode(event.target.value)}>
                    {TASK_SORT_OPTIONS.map((option) => (
                      <option key={`task-sort-${option.key}`} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {taskFilterActive ? (
                    <button
                      type="button"
                      className="secondary-btn"
                      onClick={() => {
                        setTaskSearchQuery("");
                        setTaskStatusFilter("all");
                        setTaskTypeFilter("all");
                        setTaskPriorityFilter("all");
                        setTaskSortMode("due_asc");
                      }}
                    >
                      Clear Filters
                    </button>
                  ) : null}
                </div>
              </section>
              <form className="crud-create-form" onSubmit={handleTaskCreate}>
                <input
                  placeholder="Task title"
                  value={taskForm.title}
                  onChange={(event) => setTaskForm((prev) => ({ ...prev, title: event.target.value }))}
                  required
                />
                <div className="crud-inline-fields">
                  <select
                    value={taskForm.task_type}
                    onChange={(event) => setTaskForm((prev) => ({ ...prev, task_type: event.target.value }))}
                  >
                    <option value="task">Task</option>
                    <option value="habit">Habit</option>
                    <option value="quest">Quest</option>
                  </select>
                  <select
                    value={taskForm.priority}
                    onChange={(event) => setTaskForm((prev) => ({ ...prev, priority: event.target.value }))}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                  <input
                    type="number"
                    min="1"
                    value={taskForm.xp_reward}
                    onChange={(event) => setTaskForm((prev) => ({ ...prev, xp_reward: event.target.value }))}
                    placeholder="XP"
                  />
                </div>
                <input
                  type="date"
                  value={taskForm.due_on}
                  onChange={(event) => setTaskForm((prev) => ({ ...prev, due_on: event.target.value }))}
                />
                <button type="submit" className="secondary-btn" disabled={crudBusyKey === "task-create"}>
                  {crudBusyKey === "task-create" ? "Adding..." : "Add Task"}
                </button>
              </form>

              <ul className="crud-list">
                {filteredTaskRows.length === 0 ? <li className="empty-state">No tasks match current filters.</li> : null}
                {filteredTaskRows.map((task) => {
                  const edit = getTaskEdit(task);
                  const taskStatusValue = String(edit.status || "todo").trim().toLowerCase();
                  const taskPriorityValue = String(edit.priority || task.priority || "medium").trim().toLowerCase();
                  const taskDueStart = parseDateOnlyStart(edit.due_on);
                  const hasTaskDueDate = Number.isFinite(taskDueStart);
                  const taskDone = taskStatusValue === "done";
                  const taskOverdue = !taskDone && hasTaskDueDate && taskDueStart < todayStartTimestamp;
                  const taskDueToday = !taskDone && hasTaskDueDate && taskDueStart === todayStartTimestamp;
                  const taskStatusTone = taskDone ? "success" : taskOverdue ? "danger" : taskDueToday ? "warning" : "info";
                  const taskStatusLabel = taskDone
                    ? "Done"
                    : taskOverdue
                      ? "Overdue"
                      : taskDueToday
                        ? "Due today"
                        : "Open";
                  const taskPriorityTone =
                    taskPriorityValue === "high" ? "danger" : taskPriorityValue === "low" ? "muted" : "warning";
                  const taskDueTone = !hasTaskDueDate ? "muted" : taskOverdue ? "danger" : taskDueToday ? "warning" : "info";
                  const taskDueLabel = hasTaskDueDate
                    ? taskDueToday
                      ? "Due today"
                      : `Due ${formatDateLabel(edit.due_on)}`
                    : "No due date";
                  const taskXpValue = Math.max(Number(edit.xp_reward || 0), 0);
                  return (
                    <li key={task.id} className="crud-item">
                      <input
                        value={edit.title}
                        onChange={(event) =>
                          setTaskEdits((prev) => ({
                            ...prev,
                            [task.id]: { ...edit, title: event.target.value }
                          }))
                        }
                      />
                      <div className="crud-chip-row">
                        <span className={`crud-chip ${taskStatusTone}`}>{taskStatusLabel}</span>
                        <span className="crud-chip info">{humanizeKey(task.task_type || "task")}</span>
                        <span className={`crud-chip ${taskPriorityTone}`}>{humanizeKey(taskPriorityValue)} priority</span>
                        <span className="crud-chip muted">Reward {prettyNumber(taskXpValue)} XP</span>
                        <span className={`crud-chip ${taskDueTone}`}>{taskDueLabel}</span>
                      </div>
                      <div className="crud-inline-fields">
                        <select
                          value={edit.status}
                          onChange={(event) =>
                            setTaskEdits((prev) => ({
                              ...prev,
                              [task.id]: { ...edit, status: event.target.value }
                            }))
                          }
                        >
                          <option value="todo">Todo</option>
                          <option value="done">Done</option>
                        </select>
                        <select
                          value={edit.priority}
                          onChange={(event) =>
                            setTaskEdits((prev) => ({
                              ...prev,
                              [task.id]: { ...edit, priority: event.target.value }
                            }))
                          }
                        >
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                        </select>
                      </div>
                      <div className="crud-inline-fields">
                        <input
                          type="number"
                          min="1"
                          value={edit.xp_reward}
                          onChange={(event) =>
                            setTaskEdits((prev) => ({
                              ...prev,
                              [task.id]: { ...edit, xp_reward: event.target.value }
                            }))
                          }
                        />
                        <input
                          type="date"
                          value={edit.due_on || ""}
                          onChange={(event) =>
                            setTaskEdits((prev) => ({
                              ...prev,
                              [task.id]: { ...edit, due_on: event.target.value }
                            }))
                          }
                        />
                      </div>
                      <div className="crud-actions">
                        <button
                          type="button"
                          className="secondary-btn"
                          disabled={crudBusyKey === `task-save-${task.id}`}
                          onClick={() => handleTaskSave(task.id)}
                        >
                          {crudBusyKey === `task-save-${task.id}` ? "Saving..." : "Save"}
                        </button>
                        <button
                          type="button"
                          className="secondary-btn danger"
                          disabled={crudBusyKey === `task-delete-${task.id}`}
                          onClick={() => handleTaskDelete(task.id)}
                        >
                          {crudBusyKey === `task-delete-${task.id}` ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </article>

            <article className="crud-column">
              <h3>Habits</h3>
              <section className="crud-task-toolbar">
                <div className="crud-filter-meta">
                  Showing {prettyNumber(filteredHabitRows.length)} of {prettyNumber(habitRows.length)} habits
                </div>
                <div className="crud-filter-grid">
                  <input
                    placeholder="Search name, streak, date..."
                    value={habitSearchQuery}
                    onChange={(event) => setHabitSearchQuery(event.target.value)}
                  />
                  <select value={habitStreakFilter} onChange={(event) => setHabitStreakFilter(event.target.value)}>
                    {HABIT_FILTER_STREAK_OPTIONS.map((option) => (
                      <option key={`habit-streak-filter-${option.key}`} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <select value={habitSortMode} onChange={(event) => setHabitSortMode(event.target.value)}>
                    {HABIT_SORT_OPTIONS.map((option) => (
                      <option key={`habit-sort-${option.key}`} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {habitFilterActive ? (
                    <button
                      type="button"
                      className="secondary-btn"
                      onClick={() => {
                        setHabitSearchQuery("");
                        setHabitStreakFilter("all");
                        setHabitSortMode("created_desc");
                      }}
                    >
                      Clear Filters
                    </button>
                  ) : null}
                </div>
              </section>
              <form className="crud-create-form" onSubmit={handleHabitCreate}>
                <input
                  placeholder="Habit name"
                  value={habitForm.name}
                  onChange={(event) => setHabitForm({ name: event.target.value })}
                  required
                />
                <button type="submit" className="secondary-btn" disabled={crudBusyKey === "habit-create"}>
                  {crudBusyKey === "habit-create" ? "Adding..." : "Add Habit"}
                </button>
              </form>

              <ul className="crud-list">
                {filteredHabitRows.length === 0 ? <li className="empty-state">No habits match current filters.</li> : null}
                {filteredHabitRows.map((habit) => {
                  const edit = getHabitEdit(habit);
                  const currentStreak = Math.max(Number(edit.current_streak || 0), 0);
                  const longestStreak = Math.max(Number(edit.longest_streak || 0), 0);
                  const lastCompletedStart = parseDateOnlyStart(edit.last_completed_on);
                  const hasLastCompleted = Number.isFinite(lastCompletedStart);
                  const checkedToday = hasLastCompleted && lastCompletedStart === todayStartTimestamp;
                  const needsCheckIn = currentStreak > 0 && hasLastCompleted && lastCompletedStart < todayStartTimestamp;
                  const streakTone = currentStreak >= 7 ? "success" : currentStreak > 0 ? "info" : "muted";
                  const streakLabel = currentStreak >= 7
                    ? `Hot streak ${prettyNumber(currentStreak)}`
                    : currentStreak > 0
                      ? `Active streak ${prettyNumber(currentStreak)}`
                      : "No streak yet";
                  const lastCompletedLabel = hasLastCompleted
                    ? checkedToday
                      ? "Checked in today"
                      : `Last check ${formatDateLabel(edit.last_completed_on)}`
                    : "Never completed";
                  const lastCompletedTone = checkedToday ? "success" : needsCheckIn ? "warning" : hasLastCompleted ? "info" : "muted";
                  return (
                    <li key={habit.id} className="crud-item">
                      <input
                        value={edit.name}
                        onChange={(event) =>
                          setHabitEdits((prev) => ({
                            ...prev,
                            [habit.id]: { ...edit, name: event.target.value }
                          }))
                        }
                      />
                      <div className="crud-chip-row">
                        <span className={`crud-chip ${streakTone}`}>{streakLabel}</span>
                        <span className="crud-chip info">Longest {prettyNumber(longestStreak)}</span>
                        <span className={`crud-chip ${lastCompletedTone}`}>{lastCompletedLabel}</span>
                        {needsCheckIn ? <span className="crud-chip warning">Check in today</span> : null}
                      </div>
                      <div className="crud-inline-fields">
                        <input
                          type="number"
                          min="0"
                          value={edit.current_streak}
                          onChange={(event) =>
                            setHabitEdits((prev) => ({
                              ...prev,
                              [habit.id]: { ...edit, current_streak: event.target.value }
                            }))
                          }
                        />
                        <input
                          type="number"
                          min="0"
                          value={edit.longest_streak}
                          onChange={(event) =>
                            setHabitEdits((prev) => ({
                              ...prev,
                              [habit.id]: { ...edit, longest_streak: event.target.value }
                            }))
                          }
                        />
                      </div>
                      <input
                        type="date"
                        value={edit.last_completed_on || ""}
                        onChange={(event) =>
                          setHabitEdits((prev) => ({
                            ...prev,
                            [habit.id]: { ...edit, last_completed_on: event.target.value }
                          }))
                        }
                      />
                      <div className="crud-actions">
                        <button
                          type="button"
                          className="secondary-btn"
                          disabled={crudBusyKey === `habit-save-${habit.id}`}
                          onClick={() => handleHabitSave(habit.id)}
                        >
                          {crudBusyKey === `habit-save-${habit.id}` ? "Saving..." : "Save"}
                        </button>
                        <button
                          type="button"
                          className="secondary-btn"
                          disabled={crudBusyKey === `habit-complete-${habit.id}`}
                          onClick={() => handleHabitComplete(habit.id)}
                        >
                          {crudBusyKey === `habit-complete-${habit.id}` ? "Working..." : "Complete"}
                        </button>
                        <button
                          type="button"
                          className="secondary-btn danger"
                          disabled={crudBusyKey === `habit-delete-${habit.id}`}
                          onClick={() => handleHabitDelete(habit.id)}
                        >
                          {crudBusyKey === `habit-delete-${habit.id}` ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </article>

            <article className="crud-column">
              <h3>Goals</h3>
              <section className="crud-task-toolbar">
                <div className="crud-filter-meta">
                  Showing {prettyNumber(filteredGoalRows.length)} of {prettyNumber(goalRows.length)} goals
                </div>
                <div className="crud-filter-grid">
                  <input
                    placeholder="Search title, progress, deadline..."
                    value={goalSearchQuery}
                    onChange={(event) => setGoalSearchQuery(event.target.value)}
                  />
                  <select value={goalStatusFilter} onChange={(event) => setGoalStatusFilter(event.target.value)}>
                    {GOAL_FILTER_STATUS_OPTIONS.map((option) => (
                      <option key={`goal-status-filter-${option.key}`} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <select value={goalSortMode} onChange={(event) => setGoalSortMode(event.target.value)}>
                    {GOAL_SORT_OPTIONS.map((option) => (
                      <option key={`goal-sort-${option.key}`} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  {goalFilterActive ? (
                    <button
                      type="button"
                      className="secondary-btn"
                      onClick={() => {
                        setGoalSearchQuery("");
                        setGoalStatusFilter("all");
                        setGoalSortMode("created_desc");
                      }}
                    >
                      Clear Filters
                    </button>
                  ) : null}
                </div>
              </section>
              <form className="crud-create-form" onSubmit={handleGoalCreate}>
                <input
                  placeholder="Goal title"
                  value={goalForm.title}
                  onChange={(event) => setGoalForm((prev) => ({ ...prev, title: event.target.value }))}
                  required
                />
                <div className="crud-inline-fields">
                  <input
                    type="number"
                    min="1"
                    value={goalForm.target_value}
                    onChange={(event) => setGoalForm((prev) => ({ ...prev, target_value: event.target.value }))}
                    placeholder="Target"
                  />
                  <input
                    type="date"
                    value={goalForm.deadline}
                    onChange={(event) => setGoalForm((prev) => ({ ...prev, deadline: event.target.value }))}
                  />
                </div>
                <button type="submit" className="secondary-btn" disabled={crudBusyKey === "goal-create"}>
                  {crudBusyKey === "goal-create" ? "Adding..." : "Add Goal"}
                </button>
              </form>

              <ul className="crud-list">
                {filteredGoalRows.length === 0 ? <li className="empty-state">No goals match current filters.</li> : null}
                {filteredGoalRows.map((goal) => {
                  const edit = getGoalEdit(goal);
                  const currentValue = Math.max(Number(edit.current_value || 0), 0);
                  const targetValue = Math.max(Number(edit.target_value || 0), 1);
                  const progressPercent = Math.max(0, Math.min(100, Math.round((currentValue / targetValue) * 100)));
                  const deadlineStart = parseDateOnlyStart(edit.deadline);
                  const hasDeadline = Number.isFinite(deadlineStart);
                  const daysUntilDeadline = hasDeadline
                    ? Math.round((deadlineStart - todayStartTimestamp) / 86400000)
                    : Number.NaN;
                  const goalCompleted = currentValue >= targetValue;
                  const goalOverdue = !goalCompleted && hasDeadline && daysUntilDeadline < 0;
                  const goalDueToday = !goalCompleted && hasDeadline && daysUntilDeadline === 0;
                  const goalDueSoon = !goalCompleted && hasDeadline && daysUntilDeadline > 0 && daysUntilDeadline <= 3;
                  const goalStatusTone = goalCompleted
                    ? "success"
                    : goalOverdue
                      ? "danger"
                      : goalDueToday || goalDueSoon
                        ? "warning"
                        : "info";
                  const goalStatusLabel = goalCompleted
                    ? "Completed"
                    : goalOverdue
                      ? "Overdue"
                      : goalDueToday
                        ? "Due today"
                        : goalDueSoon
                          ? `Due in ${daysUntilDeadline}d`
                          : "In progress";
                  const goalDeadlineLabel = hasDeadline
                    ? goalDueToday
                      ? "Deadline today"
                      : `Deadline ${formatDateLabel(edit.deadline)}`
                    : "No deadline";
                  const goalDeadlineTone = !hasDeadline ? "muted" : goalOverdue ? "danger" : goalDueToday || goalDueSoon ? "warning" : "info";
                  return (
                    <li key={goal.id} className="crud-item">
                      <input
                        value={edit.title}
                        onChange={(event) =>
                          setGoalEdits((prev) => ({
                            ...prev,
                            [goal.id]: { ...edit, title: event.target.value }
                          }))
                        }
                      />
                      <div className="crud-chip-row">
                        <span className={`crud-chip ${goalStatusTone}`}>{goalStatusLabel}</span>
                        <span className="crud-chip info">
                          Progress {prettyNumber(currentValue)}/{prettyNumber(targetValue)} ({progressPercent}%)
                        </span>
                        <span className={`crud-chip ${goalDeadlineTone}`}>{goalDeadlineLabel}</span>
                      </div>
                      <div className="crud-inline-fields">
                        <input
                          type="number"
                          min="0"
                          value={edit.current_value}
                          onChange={(event) =>
                            setGoalEdits((prev) => ({
                              ...prev,
                              [goal.id]: { ...edit, current_value: event.target.value }
                            }))
                          }
                        />
                        <input
                          type="number"
                          min="1"
                          value={edit.target_value}
                          onChange={(event) =>
                            setGoalEdits((prev) => ({
                              ...prev,
                              [goal.id]: { ...edit, target_value: event.target.value }
                            }))
                          }
                        />
                      </div>
                      <input
                        type="date"
                        value={edit.deadline || ""}
                        onChange={(event) =>
                          setGoalEdits((prev) => ({
                            ...prev,
                            [goal.id]: { ...edit, deadline: event.target.value }
                          }))
                        }
                      />
                      <div className="crud-actions">
                        <button
                          type="button"
                          className="secondary-btn"
                          disabled={crudBusyKey === `goal-save-${goal.id}`}
                          onClick={() => handleGoalSave(goal.id)}
                        >
                          {crudBusyKey === `goal-save-${goal.id}` ? "Saving..." : "Save"}
                        </button>
                        <button
                          type="button"
                          className="secondary-btn danger"
                          disabled={crudBusyKey === `goal-delete-${goal.id}`}
                          onClick={() => handleGoalDelete(goal.id)}
                        >
                          {crudBusyKey === `goal-delete-${goal.id}` ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </article>
          </div>

          <article className="panel recurring-panel">
            <div className="recurring-header">
              <h3>Recurring Jobs</h3>
              <div className="recurring-header-actions">
                <input
                  type="number"
                  min="1"
                  max="7"
                  value={recurringRunBackfill}
                  onChange={(event) => setRecurringRunBackfill(event.target.value)}
                />
                <button
                  type="button"
                  className="secondary-btn"
                  disabled={recurringBusyKey === "recurring-run"}
                  onClick={handleRecurringRunNow}
                >
                  {recurringBusyKey === "recurring-run" ? "Running..." : "Run Generator"}
                </button>
              </div>
            </div>

            <form className="recurring-create-form" onSubmit={handleRecurringCreate}>
              <input
                placeholder="Rule title"
                value={recurringForm.title}
                onChange={(event) => setRecurringForm((prev) => ({ ...prev, title: event.target.value }))}
                required
              />
              <div className="recurring-create-grid">
                <select
                  value={recurringForm.task_type}
                  onChange={(event) => setRecurringForm((prev) => ({ ...prev, task_type: event.target.value }))}
                >
                  <option value="task">Task</option>
                  <option value="habit">Habit</option>
                </select>
                <select
                  value={recurringForm.priority}
                  onChange={(event) => setRecurringForm((prev) => ({ ...prev, priority: event.target.value }))}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={recurringForm.xp_reward}
                  onChange={(event) => setRecurringForm((prev) => ({ ...prev, xp_reward: event.target.value }))}
                  placeholder="XP"
                />
                <select
                  value={recurringForm.frequency}
                  onChange={(event) => setRecurringForm((prev) => ({ ...prev, frequency: event.target.value }))}
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={recurringForm.interval}
                  onChange={(event) => setRecurringForm((prev) => ({ ...prev, interval: event.target.value }))}
                  placeholder="Interval"
                />
              </div>
              {recurringForm.frequency === "weekly" ? (
                <div className="weekday-picker">
                  {WEEKDAY_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      className={`weekday-chip ${recurringForm.days_of_week.includes(option.value) ? "active" : ""}`}
                      onClick={() => handleRecurringWeekdayToggle(option.value)}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              ) : null}
              <button type="submit" className="secondary-btn" disabled={recurringBusyKey === "recurring-create"}>
                {recurringBusyKey === "recurring-create" ? "Creating..." : "Add Recurring Rule"}
              </button>
            </form>

            {recurringLoading ? <p className="notice">Refreshing recurring rules...</p> : null}
            <ul className="recurring-list">
              {recurringRows.length === 0 ? <li className="empty-state">No recurring rules yet.</li> : null}
              {recurringRows.map((rule) => (
                <li key={rule.id} className="recurring-item">
                  <div>
                    <p className="recurring-title">{rule.title}</p>
                    <p className="recurring-meta">
                      {rule.task_type} | {rule.schedule_label} | {rule.xp_reward} XP | {rule.active ? "active" : "paused"}
                    </p>
                  </div>
                  <div className="recurring-actions">
                    <button
                      type="button"
                      className="secondary-btn"
                      disabled={recurringBusyKey === `recurring-toggle-${rule.id}`}
                      onClick={() => handleRecurringActiveToggle(rule)}
                    >
                      {rule.active ? "Pause" : "Activate"}
                    </button>
                    <button
                      type="button"
                      className="secondary-btn danger"
                      disabled={recurringBusyKey === `recurring-delete-${rule.id}`}
                      onClick={() => handleRecurringDelete(rule.id)}
                    >
                      {recurringBusyKey === `recurring-delete-${rule.id}` ? "Deleting..." : "Delete"}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </article>

          <article className="xp-rules-panel">
            <div className="xp-rules-header">
              <h3>XP Rules Engine</h3>
              <span>{xpRuleEntries.length} rules</span>
            </div>
            <ul className="xp-rules-list">
              {xpRuleEntries.map(([ruleKey, points]) => (
                <li key={ruleKey} className="xp-rule-item">
                  <span className="xp-rule-key">{formatXpRuleKey(ruleKey)}</span>
                  <strong>{points} XP</strong>
                </li>
              ))}
            </ul>
          </article>
        </section>
      </div>
      {spaceReplaceConfirmOpen ? (
        <div
          className="confirm-modal-backdrop"
          role="presentation"
          onClick={(event) => {
            if (event.target === event.currentTarget && spacesBusyKey !== "space-import") {
              setSpaceReplaceConfirmOpen(false);
            }
          }}
        >
          <section className="confirm-modal panel" role="dialog" aria-modal="true" aria-labelledby="replace-space-modal-title">
            <h3 id="replace-space-modal-title">Confirm Replace Import</h3>
            <p>
              This will overwrite shared tasks, role templates, non-owner members, and notification preferences for{" "}
              <strong>{selectedSpace?.name || "this space"}</strong>.
            </p>
            <p className="confirm-modal-note">
              Space ID: <code>{selectedSpaceId || "unknown"}</code>
            </p>
            <p className="confirm-modal-note">
              Required phrase: <code>{spaceImportRequiredPhrase || "REPLACE SPACE <space_id>"}</code>
            </p>
            {spaceReplacePreviewRows.length > 0 ? (
              <ul className="confirm-modal-list">
                {spaceReplacePreviewRows.map((row) => (
                  <li key={row.key}>
                    <strong>{row.label}</strong>: current {prettyNumber(row.current)}, after {prettyNumber(row.projected)} (
                    {formatSignedNumber(row.diff)})
                  </li>
                ))}
              </ul>
            ) : (
              <p className="confirm-modal-note">Run "Preview Import" to inspect projected changes before replacing.</p>
            )}
            <div className="confirm-modal-actions">
              <button
                type="button"
                className="secondary-btn"
                onClick={() => setSpaceReplaceConfirmOpen(false)}
                disabled={spacesBusyKey === "space-import"}
              >
                Cancel
              </button>
              <button
                type="button"
                className="secondary-btn danger"
                onClick={handleSpaceImportReplaceConfirm}
                disabled={spacesBusyKey === "space-import" || !spaceReplacePreviewReady || !spaceImportConfirmationMatches}
              >
                {spacesBusyKey === "space-import" ? "Importing..." : "Yes, Replace Space Data"}
              </button>
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}

