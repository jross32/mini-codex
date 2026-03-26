import { expect, test } from "@playwright/test";

const LOGIN_IDENTIFIER = "testuser1";
const LOGIN_PASSWORD = "testuser123";

const NAV_ITEMS = [
  { key: "dashboard", title: "Welcome back!" },
  { key: "tasks", title: "Tasks" },
  { key: "quests", title: "Quests" },
  { key: "shop", title: "Shop" },
  { key: "inventory", title: "Inventory" },
  { key: "achievements", title: "Achievements" },
  { key: "challenges", title: "Challenges" },
  { key: "timeline", title: "Timeline" },
  { key: "leaderboard", title: "Leaderboard" },
  { key: "season_pass", title: "Season Pass" },
  { key: "avatar", title: "Avatar" },
  { key: "spaces", title: "Spaces" },
  { key: "stats", title: "Stats" },
  { key: "settings", title: "Settings" }
];

const QUICK_ACTIONS = [
  { key: "tasks", title: "Tasks", pathPattern: /\/tasks$/ },
  { key: "quests", title: "Quests", pathPattern: /\/quests$/ },
  { key: "shop", title: "Shop", pathPattern: /\/shop$/ },
  { key: "avatar", title: "Avatar", pathPattern: /\/avatar$/ },
  { key: "spaces", title: "Spaces", pathPattern: /\/spaces$/ }
];

async function login(page) {
  await page.goto("/");

  const authPanel = page.locator(".auth-card");
  if (await authPanel.isVisible()) {
    await page.locator('input[name="identifier"]').fill(LOGIN_IDENTIFIER);
    await page.locator('input[name="password"]').fill(LOGIN_PASSWORD);
    await page.getByRole("button", { name: "Sign in" }).click();
  }

  await expect(page.locator(".topbar h1")).toHaveText("Welcome back!");
}

async function openMenuView(page, key, expectedTitle) {
  const navButton = page.locator(`.sidebar-nav .nav-item[data-nav-key="${key}"]`);
  await navButton.evaluate((element) => element.click());
  await expect(page.locator(".topbar h1")).toHaveText(expectedTitle);
}

test("menu navigation and key task/quest actions work", async ({ page }) => {
  await login(page);

  await expect(page.locator(".content-grid")).toBeVisible();
  await expect(page.locator(".crud-panel")).toHaveAttribute("hidden", "");
  await expect(page.locator(".dashboard-create-panel")).toBeVisible();

  for (const action of QUICK_ACTIONS) {
    await page.locator(`.dashboard-quick-actions [data-quick-nav="${action.key}"]`).click();
    await expect(page.locator(".topbar h1")).toHaveText(action.title);
    await expect(page).toHaveURL(action.pathPattern);
    await openMenuView(page, "dashboard", "Welcome back!");
  }

  const token = Date.now();
  const quickTaskTitle = `E2E Quick Task ${token}`;
  const quickHabitName = `E2E Quick Habit ${token}`;
  const quickGoalTitle = `E2E Quick Goal ${token}`;

  await page.locator('[data-quick-create="task-title"]').fill(quickTaskTitle);
  await page.locator('[data-quick-create="task-type"]').selectOption("quest");
  await expect(page.locator('[data-quick-create="task-xp"]')).toHaveValue("100");
  await page.locator('[data-quick-create="task-type"]').selectOption("task");
  await expect(page.locator('[data-quick-create="task-xp"]')).toHaveValue("20");
  await page.locator('[data-quick-create-due-preset="today"]').click();
  await expect(page.locator('[data-quick-create="task-due-on"]')).toHaveValue(/\d{4}-\d{2}-\d{2}/);
  await page.locator('[data-quick-create="task-priority"]').selectOption("high");
  await page.locator('[data-quick-create="task-xp"]').fill("27");
  await page.locator('[data-quick-create-submit="task"]').click();
  await expect(page.locator(".notice.success")).toContainText("Quick task created.");
  await expect(page.locator('[data-quick-create="task-due-on"]')).toHaveValue("");

  await page.locator('[data-quick-create="habit-name"]').fill(quickHabitName);
  await page.locator('[data-quick-create-submit="habit"]').click();
  await expect(page.locator(".notice.success")).toContainText(/earned|created/i);

  await page.locator('[data-quick-create="goal-title"]').fill(quickGoalTitle);
  await page.locator('[data-quick-create="goal-target"]').fill("15");
  await page.locator('[data-quick-create-submit="goal"]').click();
  await expect(page.locator(".notice.success")).toContainText(/earned|created/i);

  for (const item of NAV_ITEMS) {
    await openMenuView(page, item.key, item.title);
  }

  await openMenuView(page, "tasks", "Tasks");
  await expect(page.locator(".content-grid")).toHaveAttribute("hidden", "");
  await expect(page.locator(".xp-panel")).toHaveAttribute("hidden", "");
  await expect(page.locator(".reminder-panel")).toHaveAttribute("hidden", "");
  await expect(page.locator(".crud-panel")).toBeVisible();

  const taskColumn = page.locator(".crud-column").filter({
    has: page.getByRole("heading", { name: "Tasks" })
  });
  const habitColumn = page.locator(".crud-column").filter({
    has: page.getByRole("heading", { name: "Habits" })
  });
  const goalColumn = page.locator(".crud-column").filter({
    has: page.getByRole("heading", { name: "Goals" })
  });

  await expect(
    taskColumn.locator(".crud-item").filter({
      has: page.locator(`input[value="${quickTaskTitle}"]`)
    })
  ).toBeVisible();

  await expect(
    habitColumn.locator(".crud-item").filter({
      has: page.locator(`input[value="${quickHabitName}"]`)
    })
  ).toBeVisible();

  await expect(
    goalColumn.locator(".crud-item").filter({
      has: page.locator(`input[value="${quickGoalTitle}"]`)
    })
  ).toBeVisible();

  const questTitle = `E2E Quest ${Date.now()}`;
  const taskCreateForm = taskColumn.locator("form.crud-create-form").first();
  await taskCreateForm.getByPlaceholder("Task title").fill(questTitle);
  await taskCreateForm.locator("select").first().selectOption("quest");
  await taskCreateForm.getByRole("button", { name: "Add Task" }).click();

  await expect(
    taskColumn.locator(".crud-item").filter({
      has: page.locator(`input[value="${questTitle}"]`)
    })
  ).toBeVisible();

  await openMenuView(page, "quests", "Quests");
  const questRow = page.locator(".quests-shell .task-item").filter({ hasText: questTitle }).first();
  await expect(questRow).toBeVisible();
  await questRow.getByRole("button", { name: "Complete" }).click();
  await expect(questRow.locator(".task-meta")).toContainText("Completed");

  await openMenuView(page, "dashboard", "Welcome back!");
  const reminderOpenButton = page.locator(".reminder-panel .reminder-item .secondary-btn").first();
  if ((await reminderOpenButton.count()) > 0) {
    await reminderOpenButton.click();
    await expect(page).toHaveURL(/\/(dashboard|tasks|quests|spaces)/);
  } else {
    await openMenuView(page, "season_pass", "Season Pass");
    const openShopButton = page.getByRole("button", { name: "Open Shop" });
    if ((await openShopButton.count()) > 0) {
      await openShopButton.click();
    } else {
      await openMenuView(page, "shop", "Shop");
    }
    await expect(page.locator(".topbar h1")).toHaveText("Shop");
  }
});
