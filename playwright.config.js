import { defineConfig } from "@playwright/test";

export default defineConfig({
    testDir: "./tests/e2e",
    timeout: 30000,
    expect: { timeout: 6000 },
    workers: 2,
    fullyParallel: false,
    reporter: [["list"], ["html", { open: "never" }]],
    use: {
        baseURL: "http://127.0.0.1:4321",
        channel: process.env.PLAYWRIGHT_BROWSER_CHANNEL || (process.platform === "win32" ? "chrome" : undefined),
        headless: true,
        locale: "es-PE",
        timezoneId: "America/Lima",
        screenshot: "only-on-failure",
        trace: "retain-on-failure"
    },
    projects: [
        { name: "computadora", use: { viewport: { width: 1440, height: 1000 } } },
        { name: "tablet", use: { viewport: { width: 768, height: 1024 }, isMobile: true, hasTouch: true } },
        { name: "celular", use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
        { name: "compacto", use: { viewport: { width: 320, height: 740 }, isMobile: true, hasTouch: true } }
    ],
    webServer: {
        command: "npm run dev -- --port 4321",
        url: "http://127.0.0.1:4321/",
        reuseExistingServer: true,
        timeout: 30000
    }
});
