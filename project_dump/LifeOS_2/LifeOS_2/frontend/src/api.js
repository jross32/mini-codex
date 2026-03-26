const RAW_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";
const API_BASE_URL = String(RAW_API_BASE_URL || "")
  .trim()
  .replace(/\s+/g, "")
  .replace(/\/+$/, "") || "http://127.0.0.1:5000";
const AUTH_TOKEN_KEY = "lifeos_auth_token";

function readToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY) || "";
}

function writeToken(token) {
  if (token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  }
}

export function clearAuthToken() {
  writeToken("");
}

async function requestJson(path, options = {}, { auth = true } = {}) {
  const headers = new Headers(options.headers || {});
  const hasBody = Object.prototype.hasOwnProperty.call(options, "body");
  if (hasBody && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (auth) {
    const token = readToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const safePath = String(path || "").trim();
  const response = await fetch(`${API_BASE_URL}${safePath}`, { ...options, headers });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload.error || payload.message || `Request failed (${response.status})`;
    throw new Error(message);
  }
  return payload;
}

export async function registerUser({ username, email, display_name, password }) {
  const data = await requestJson(
    "/api/auth/register",
    {
      method: "POST",
      body: JSON.stringify({ username, email, display_name, password })
    },
    { auth: false }
  );
  writeToken(data.token || "");
  return data;
}

export async function loginUser({ identifier, password }) {
  const data = await requestJson(
    "/api/auth/login",
    {
      method: "POST",
      body: JSON.stringify({ identifier, password })
    },
    { auth: false }
  );
  writeToken(data.token || "");
  return data;
}

export async function fetchMe() {
  return requestJson("/api/auth/me");
}

export async function exportAccountSnapshot() {
  const data = await requestJson("/api/account/export");
  return data.snapshot || data;
}

export async function importAccountSnapshot(payload) {
  return requestJson("/api/account/import", {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function updateAccountProfile(payload) {
  return requestJson("/api/account/profile", {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
}

export async function updateAccountPassword(payload) {
  return requestJson("/api/account/password", {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function fetchReminderChannels() {
  return requestJson("/api/account/reminder-channels");
}

export async function updateReminderChannels(payload) {
  return requestJson("/api/account/reminder-channels", {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
}

export async function sendReminderChannelTest(payload) {
  return requestJson("/api/account/reminder-channels/test", {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function runReminderChannelDelivery(payload) {
  return requestJson("/api/account/reminder-channels/run", {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function fetchReminderDeliveries(limit = 20) {
  const safeLimit = Number.isFinite(Number(limit)) ? Math.max(1, Math.min(Number(limit), 100)) : 20;
  const data = await requestJson(`/api/account/reminder-deliveries?limit=${encodeURIComponent(safeLimit)}`);
  return data.deliveries || [];
}

export async function requestPasswordRecovery(payload) {
  return requestJson(
    "/api/account/recovery/request",
    {
      method: "POST",
      body: JSON.stringify(payload || {})
    },
    { auth: false }
  );
}

export async function confirmPasswordRecovery(payload) {
  return requestJson(
    "/api/account/recovery/confirm",
    {
      method: "POST",
      body: JSON.stringify(payload || {})
    },
    { auth: false }
  );
}

export async function logoutUser() {
  const token = readToken();
  if (!token) {
    return { message: "Logged out" };
  }
  const result = await requestJson("/api/auth/logout", { method: "POST" });
  writeToken("");
  return result;
}

export async function fetchDashboard() {
  return requestJson("/api/dashboard");
}

export async function fetchShop() {
  return requestJson("/api/shop");
}

export async function fetchInventory(limit = 240) {
  const safeLimit = Number.isFinite(Number(limit)) ? Math.max(24, Math.min(Number(limit), 500)) : 240;
  return requestJson(`/api/inventory?limit=${encodeURIComponent(safeLimit)}`);
}

export async function redeemInventoryPurchase(purchaseId, claimNote = "") {
  return requestJson(`/api/inventory/redeem/${purchaseId}`, {
    method: "POST",
    body: JSON.stringify({
      claim_note: String(claimNote || "")
    })
  });
}

export async function fetchAchievements(refresh = true) {
  const refreshFlag = refresh ? "1" : "0";
  return requestJson(`/api/achievements?refresh=${refreshFlag}`);
}

export async function fetchChallenges(windowType = "") {
  const safeWindow = String(windowType || "").trim().toLowerCase();
  const query = safeWindow ? `?window_type=${encodeURIComponent(safeWindow)}` : "";
  return requestJson(`/api/challenges${query}`);
}

export async function claimChallengeReward(payload) {
  return requestJson("/api/challenges/claim", {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function fetchTimeline(days = 30) {
  const safeDays = Number.isFinite(Number(days)) ? Math.max(7, Math.min(Number(days), 180)) : 30;
  return requestJson(`/api/timeline?days=${encodeURIComponent(safeDays)}`);
}

export async function fetchLeaderboard(limit = 15, scope = "global") {
  const safeLimit = Number.isFinite(Number(limit)) ? Math.max(3, Math.min(Number(limit), 50)) : 15;
  const safeScope = String(scope || "global").trim().toLowerCase() || "global";
  return requestJson(`/api/leaderboard?limit=${encodeURIComponent(safeLimit)}&scope=${encodeURIComponent(safeScope)}`);
}

export async function fetchSeasonPass() {
  return requestJson("/api/season-pass");
}

export async function fetchSeasonPassPremiumState() {
  return requestJson("/api/season-pass/premium");
}

export async function updateSeasonPassPremiumState(enabled) {
  return requestJson("/api/season-pass/premium", {
    method: "PATCH",
    body: JSON.stringify({ enabled: Boolean(enabled) })
  });
}

export async function claimSeasonPassTier(tier, track = "free") {
  const safeTrack = String(track || "free").trim().toLowerCase() || "free";
  return requestJson("/api/season-pass/claim", {
    method: "POST",
    body: JSON.stringify({ tier, track: safeTrack })
  });
}

export async function purchaseShopItem(itemKey) {
  return requestJson("/api/shop/purchase", {
    method: "POST",
    body: JSON.stringify({ item_key: itemKey })
  });
}

export async function fetchAvatar() {
  return requestJson("/api/avatar");
}

export async function updateAvatar(payload) {
  return requestJson("/api/avatar", {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
}

export async function fetchStats(days = 30) {
  const query = Number.isFinite(Number(days)) ? `?days=${encodeURIComponent(Number(days))}` : "";
  return requestJson(`/api/stats${query}`);
}

export async function fetchNotifications() {
  return requestJson("/api/notifications");
}

export async function fetchRecurringRules() {
  const data = await requestJson("/api/recurring-rules");
  return data.rules || [];
}

export async function createRecurringRule(payload) {
  return requestJson("/api/recurring-rules", {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function updateRecurringRule(ruleId, payload) {
  return requestJson(`/api/recurring-rules/${ruleId}`, {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
}

export async function deleteRecurringRule(ruleId) {
  return requestJson(`/api/recurring-rules/${ruleId}`, { method: "DELETE" });
}

export async function runRecurringRules(payload) {
  return requestJson("/api/recurring-rules/run", {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function fetchSpaces() {
  const data = await requestJson("/api/spaces");
  return data.spaces || [];
}

export async function createSpace(payload) {
  return requestJson("/api/spaces", {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function fetchSpaceDetail(spaceId) {
  return requestJson(`/api/spaces/${spaceId}`);
}

export async function exportSpaceSnapshot(spaceId) {
  const data = await requestJson(`/api/spaces/${spaceId}/export`);
  return data.snapshot || data;
}

export async function importSpaceSnapshot(spaceId, payload) {
  return requestJson(`/api/spaces/${spaceId}/import`, {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function previewSpaceSnapshotImport(spaceId, payload) {
  return requestJson(`/api/spaces/${spaceId}/import/preview`, {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function updateSpace(spaceId, payload) {
  return requestJson(`/api/spaces/${spaceId}`, {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
}

export async function deleteSpace(spaceId) {
  return requestJson(`/api/spaces/${spaceId}`, { method: "DELETE" });
}

export async function addSpaceMember(spaceId, payload) {
  return requestJson(`/api/spaces/${spaceId}/members`, {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function updateSpaceMemberRole(spaceId, userId, payload) {
  return requestJson(`/api/spaces/${spaceId}/members/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
}

export async function removeSpaceMember(spaceId, userId) {
  return requestJson(`/api/spaces/${spaceId}/members/${userId}`, { method: "DELETE" });
}

export async function fetchSpaceInvites(spaceId, includeInactive = true) {
  const query = includeInactive ? "?include_inactive=true" : "";
  return requestJson(`/api/spaces/${spaceId}/invites${query}`);
}

export async function fetchSpaceInviteAnalytics(spaceId) {
  return requestJson(`/api/spaces/${spaceId}/invite-analytics`);
}

export async function createSpaceInvite(spaceId, payload) {
  return requestJson(`/api/spaces/${spaceId}/invites`, {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function revokeSpaceInvite(spaceId, inviteId) {
  return requestJson(`/api/spaces/${spaceId}/invites/${inviteId}`, { method: "DELETE" });
}

export async function acceptSpaceInvite(payload) {
  return requestJson("/api/spaces/invites/accept", {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function fetchSpaceRoleTemplates(spaceId) {
  return requestJson(`/api/spaces/${spaceId}/role-templates`);
}

export async function fetchSpaceAuditEvents(spaceId, options = {}) {
  const normalizedOptions =
    options !== null && typeof options === "object" ? options : { limit: options };
  const safeLimit = Number.isFinite(Number(normalizedOptions.limit))
    ? Math.max(1, Math.min(Number(normalizedOptions.limit), 100))
    : 30;
  const params = new URLSearchParams();
  params.set("limit", String(safeLimit));

  const eventType = String(normalizedOptions.event_type || "all").trim().toLowerCase();
  if (eventType && eventType !== "all") {
    params.set("event_type", eventType);
  }

  const days = Number(normalizedOptions.days);
  if (Number.isFinite(days) && days >= 1) {
    params.set("days", String(Math.round(days)));
  }

  const query = String(normalizedOptions.query || "").trim();
  if (query) {
    params.set("query", query.slice(0, 120));
  }

  return requestJson(`/api/spaces/${spaceId}/audit-events?${params.toString()}`);
}

export async function updateSpaceNotificationPreference(spaceId, payload) {
  return requestJson(`/api/spaces/${spaceId}/notification-preference`, {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
}

export async function fetchSpaceNotificationDefault(spaceId) {
  return requestJson(`/api/spaces/${spaceId}/notification-default`);
}

export async function updateSpaceNotificationDefault(spaceId, payload) {
  return requestJson(`/api/spaces/${spaceId}/notification-default`, {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
}

export async function applySpaceNotificationDefaultToMembers(spaceId, payload) {
  return requestJson(`/api/spaces/${spaceId}/notification-default/apply`, {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function fetchSpaceNotificationQuietHours(spaceId) {
  return requestJson(`/api/spaces/${spaceId}/notification-quiet-hours`);
}

export async function updateSpaceNotificationQuietHours(spaceId, payload) {
  return requestJson(`/api/spaces/${spaceId}/notification-quiet-hours`, {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
}

export async function updateSpaceRoleTemplate(spaceId, roleName, payload) {
  return requestJson(`/api/spaces/${spaceId}/role-templates/${encodeURIComponent(roleName)}`, {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
}

export async function fetchSpaceTasks(spaceId, status = "") {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return requestJson(`/api/spaces/${spaceId}/tasks${query}`);
}

export async function createSpaceTask(spaceId, payload) {
  return requestJson(`/api/spaces/${spaceId}/tasks`, {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
}

export async function updateSpaceTask(spaceId, taskId, payload) {
  return requestJson(`/api/spaces/${spaceId}/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
}

export async function deleteSpaceTask(spaceId, taskId) {
  return requestJson(`/api/spaces/${spaceId}/tasks/${taskId}`, { method: "DELETE" });
}

export async function completeSpaceTask(spaceId, taskId) {
  return requestJson(`/api/spaces/${spaceId}/tasks/${taskId}/complete`, { method: "POST", body: JSON.stringify({}) });
}

export async function fetchXpRules() {
  const data = await requestJson("/api/xp/rules");
  return data.rules || {};
}

export async function completeTask(taskId) {
  return requestJson(`/api/tasks/${taskId}/complete`, { method: "POST", body: JSON.stringify({}) });
}

export async function fetchTasks() {
  const data = await requestJson("/api/tasks");
  return data.tasks || [];
}

export async function createTask(payload) {
  const data = await requestJson("/api/tasks", {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
  return data.task;
}

export async function updateTask(taskId, payload) {
  const data = await requestJson(`/api/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
  return data.task;
}

export async function deleteTask(taskId) {
  return requestJson(`/api/tasks/${taskId}`, { method: "DELETE" });
}

export async function fetchHabits() {
  const data = await requestJson("/api/habits");
  return data.habits || [];
}

export async function createHabit(payload) {
  const data = await requestJson("/api/habits", {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
  return data;
}

export async function updateHabit(habitId, payload) {
  const data = await requestJson(`/api/habits/${habitId}`, {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
  return data.habit;
}

export async function completeHabit(habitId, payload = {}) {
  const data = await requestJson(`/api/habits/${habitId}/complete`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
  return data;
}

export async function deleteHabit(habitId) {
  return requestJson(`/api/habits/${habitId}`, { method: "DELETE" });
}

export async function fetchGoals() {
  const data = await requestJson("/api/goals");
  return data.goals || [];
}

export async function createGoal(payload) {
  const data = await requestJson("/api/goals", {
    method: "POST",
    body: JSON.stringify(payload || {})
  });
  return data;
}

export async function updateGoal(goalId, payload) {
  const data = await requestJson(`/api/goals/${goalId}`, {
    method: "PATCH",
    body: JSON.stringify(payload || {})
  });
  return data.goal;
}

export async function deleteGoal(goalId) {
  return requestJson(`/api/goals/${goalId}`, { method: "DELETE" });
}
