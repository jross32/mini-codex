import { defineConfig, devices } from "@playwright/test";

const FRONTEND_PORT = 4173;
const BACKEND_PORT = 5100;
const FRONTEND_BASE_URL = `http://127.0.0.1:${FRONTEND_PORT}`;
const BACKEND_BASE_URL = `http://127.0.0.1:${BACKEND_PORT}`;

const BACKEND_COMMAND =
  process.platform === "win32" ? ".venv\\Scripts\\python.exe app.py" : ".venv/bin/python app.py";

export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  expect: {
    timeout: 10_000
  },
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: FRONTEND_BASE_URL,
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure"
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ],
  webServer: [
    {
      command: BACKEND_COMMAND,
      cwd: "..",
      url: `${BACKEND_BASE_URL}/api/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        LIFEOS_HOST: "127.0.0.1",
        LIFEOS_PORT: String(BACKEND_PORT),
        LIFEOS_DEBUG: "0",
        LIFEOS_RELOADER: "0"
      }
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${FRONTEND_PORT}`,
      cwd: ".",
      url: FRONTEND_BASE_URL,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        VITE_API_BASE_URL: BACKEND_BASE_URL
      }
    }
  ]
});
