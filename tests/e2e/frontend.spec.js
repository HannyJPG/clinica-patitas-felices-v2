import { test, expect } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { obtenerMomentoLima } from "../../src/scripts/validar-cita.js";

const capturas = "artifacts/frontend";

async function sinDesbordamiento(page) {
    const medidas = await page.evaluate(() => ({
        ancho: window.innerWidth,
        documento: document.documentElement.scrollWidth,
        cuerpo: document.body.scrollWidth
    }));
    expect(medidas.documento).toBeLessThanOrEqual(medidas.ancho + 1);
    expect(medidas.cuerpo).toBeLessThanOrEqual(medidas.ancho + 1);
}

async function rellenarSolicitud(page) {
    await page.locator("#propietario").fill("Prueba de interfaz");
    await page.locator("#telefono").fill("900000001");
    await page.locator("#mascota").fill("Luna de prueba");
    await page.locator("#servicio").selectOption("consulta-general");
    await page.locator("#fecha").fill(obtenerMomentoLima(new Date(Date.now() + 86400000)).fecha);
    await page.locator("#hora").fill("09:30");
    await page.locator("#motivo").fill("Revisión del formulario, sin envío de mensajes.");
}

test.beforeEach(async ({ page }) => {
    // Los enlaces se inspeccionan: las pruebas nunca envían datos a WhatsApp.
    await page.route(/^https:\/\/(?:wa\.me|[^/]*whatsapp\.com)(?:\/|$)/, route => route.abort());
});

test("portada, fotografías y composición sin desbordamientos", async ({ page }, testInfo) => {
    const errores = [];
    page.on("pageerror", error => errores.push(error.message));
    const response = await page.goto("/");
    expect(response.headers()["content-type"]).toContain("text/html");
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.locator("footer.site-footer")).toHaveCount(1);
    await expect(page.locator(".service-card")).toHaveCount(4);
    await expect(page.locator(".menu-toggle")).toHaveJSProperty("hidden", false);
    await page.evaluate(async () => { await document.fonts.ready; });
    await page.locator("img").evaluateAll(async imagenes => {
        await Promise.all(imagenes.map(imagen => { imagen.loading = "eager"; return imagen.decode(); }));
    });
    await sinDesbordamiento(page);
    expect(errores).toEqual([]);
    await mkdir(capturas, { recursive: true });
    await page.screenshot({ path: capturas + "/inicio-" + testInfo.project.name + ".png", animations: "disabled" });
    await page.screenshot({ path: capturas + "/pagina-" + testInfo.project.name + ".png", fullPage: true, animations: "disabled" });
    await page.keyboard.press("Tab");
    await expect(page.getByRole("link", { name: "Saltar al contenido", exact: true })).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.locator("main")).toBeFocused();
});

test("menú, destinos de sección y cierre con Escape", async ({ page }) => {
    await page.goto("/");
    const boton = page.locator("[data-menu-toggle]");
    const menu = page.locator("#menu-principal");
    if (page.viewportSize().width >= 992) {
        await expect(boton).toBeHidden();
        await expect(menu.getByRole("link", { name: "Servicios", exact: true })).toBeVisible();
        await menu.getByRole("link", { name: "Servicios", exact: true }).click();
        await expect(page).toHaveURL(/\/#servicios$/);
    } else {
        await boton.click();
        await expect(boton).toHaveAttribute("aria-expanded", "true");
        await menu.getByRole("link", { name: "Servicios", exact: true }).click();
        await expect(page).toHaveURL(/\/#servicios$/);
        await expect(menu).not.toHaveClass(/\bshow\b/);
        await expect(menu).not.toHaveClass(/\bcollapsing\b/);
        await boton.click();
        await expect(boton).toHaveAttribute("aria-expanded", "true");
        await page.keyboard.press("Escape");
        await expect(boton).toHaveAttribute("aria-expanded", "false");
        await expect(menu).not.toHaveClass(/\bshow\b/);
        await expect(menu).not.toHaveClass(/\bcollapsing\b/);
        await expect(boton).toBeFocused();
    }
    await sinDesbordamiento(page);
});

test("carrusel con flechas, indicadores y teclado", async ({ page }, testInfo) => {
    await page.goto("/");
    const carrusel = page.locator("[data-manual-carousel]");
    await carrusel.scrollIntoViewIfNeeded();
    await expect(carrusel.locator(".carousel-item")).toHaveCount(2);
    await expect(carrusel.locator(".carousel-item.active")).toContainText("Todo empieza por escucharte");
    await carrusel.getByRole("button", { name: "Mostrar mensaje siguiente", exact: true }).click();
    await expect(carrusel.locator(".carousel-item.active")).toContainText("Su bienestar, tu tranquilidad");
    await carrusel.getByRole("button", { name: "Mostrar mensaje 1", exact: true }).click();
    await expect(carrusel.locator(".carousel-item.active")).toContainText("Todo empieza por escucharte");
    await page.keyboard.press("ArrowRight");
    await expect(carrusel.locator(".carousel-item.active")).toContainText("Su bienestar, tu tranquilidad");
    const foto = await carrusel.locator(".carousel-item.active .testimonial-photo").boundingBox();
    const texto = await carrusel.locator(".carousel-item.active .testimonial-copy").boundingBox();
    if (page.viewportSize().width >= 768) expect(texto.x).toBeGreaterThanOrEqual(foto.x + foto.width - 1);
    else expect(texto.y).toBeGreaterThanOrEqual(foto.y + foto.height - 1);
    await sinDesbordamiento(page);
    await mkdir(capturas, { recursive: true });
    await carrusel.screenshot({ path: capturas + "/carrusel-" + testInfo.project.name + ".png", animations: "disabled" });
});

test("cada tarjeta preselecciona su servicio en la página Astro", async ({ page }) => {
    const servicios = ["consulta-general", "vacunacion", "desparasitacion", "control"];
    for (const servicio of servicios) {
        await page.goto("/");
        await page.locator('.service-link[href="/agendar-cita?servicio=' + servicio + '"]').click();
        await expect(page.locator("#formulario-cita")).toBeVisible();
        await expect(page.locator("#propietario")).toBeEnabled();
        await expect(page.locator("#servicio")).toHaveValue(servicio);
        await expect(page.locator("#hora")).toHaveAttribute("step", "1800");
    }
});

test("validación, resumen y enlace de WhatsApp sin envío", async ({ page }, testInfo) => {
    const envios = [];
    page.on("request", request => { if (request.method() === "POST") envios.push(request.url()); });
    const response = await page.goto("/agendar-cita");
    expect(response.headers()["content-type"]).toContain("text/html");
    await expect(page.locator("#propietario")).toBeEnabled();
    await mkdir(capturas, { recursive: true });
    await page.screenshot({ path: capturas + "/formulario-" + testInfo.project.name + ".png", fullPage: true, animations: "disabled" });
    await page.getByRole("button", { name: "Preparar solicitud", exact: true }).click();
    await expect(page.locator("#errores-cita")).toBeVisible();
    await expect(page.locator("#propietario")).toBeFocused();
    await rellenarSolicitud(page);
    await page.locator("#telefono").fill("987abc321");
    await page.locator("#fecha").fill("2020-01-01");
    await page.locator("#hora").fill("09:15");
    await page.getByRole("button", { name: "Preparar solicitud", exact: true }).click();
    await expect(page.locator("#error-hora")).toContainText("30 minutos");
    await expect(page.locator("#error-telefono")).toContainText("9 a 15 dígitos");
    await expect(page.locator("#error-fecha")).toContainText("anterior a hoy");
    await expect(page.locator("#resultado-cita")).toBeHidden();
    await page.locator("#telefono").fill("900000001");
    await page.locator("#fecha").fill(obtenerMomentoLima(new Date(Date.now() + 86400000)).fecha);
    await page.locator("#hora").fill("09:30");
    await page.getByRole("button", { name: "Preparar solicitud", exact: true }).click();
    await expect(page.locator("#resultado-cita")).toBeVisible();
    await expect(page.locator("#resultado-cita")).toBeFocused();
    const url = new URL(await page.locator("#continuar-whatsapp").getAttribute("href"));
    expect(url.origin + url.pathname).toBe("https://wa.me/51990853697");
    expect(url.searchParams.get("text")).toContain("Luna de prueba");
    expect(url.searchParams.get("text")).toContain("30 minutos");
    expect(url.searchParams.get("text")).toContain("09:30 (Lima, Perú)");
    expect(envios).toEqual([]);
    await sinDesbordamiento(page);
});

test("editar y limpiar eliminan el resumen y el enlace anterior", async ({ page }) => {
    await page.goto("/agendar-cita?servicio=vacunacion");
    await expect(page.locator("#propietario")).toBeEnabled();
    await rellenarSolicitud(page);
    await page.getByRole("button", { name: "Preparar solicitud", exact: true }).click();
    await expect(page.locator("#resultado-cita")).toBeVisible();
    await page.locator("#mascota").fill("Otra mascota de prueba");
    await expect(page.locator("#resultado-cita")).toBeHidden();
    await expect(page.locator("#continuar-whatsapp")).not.toHaveAttribute("href");
    await page.getByRole("button", { name: "Preparar solicitud", exact: true }).click();
    await expect(page.locator('[data-resumen="mascota"]')).toHaveText("Otra mascota de prueba");
    await page.getByRole("button", { name: "Limpiar datos", exact: true }).click();
    for (const campo of ["propietario", "telefono", "mascota", "servicio", "fecha", "hora", "motivo"]) {
        await expect(page.locator("#" + campo)).toHaveValue("");
    }
    await expect(page.locator("#resultado-cita")).toBeHidden();
    await expect(page.locator("#continuar-whatsapp")).not.toHaveAttribute("href");
    await expect(page.locator("#errores-cita")).toBeHidden();
});

test("páginas interiores conservan identidad y acceso a las secciones", async ({ page }) => {
    for (const ruta of ["/login", "/soon"]) {
        const response = await page.goto(ruta);
        expect(response.headers()["content-type"]).toContain("text/html");
        await expect(page.locator("h1")).toHaveCount(1);
        await expect(page.locator("footer.site-footer")).toHaveCount(1);
        await expect(page.locator(".footer-phone")).toHaveAttribute("href", /^https:\/\/wa\.me\/51990853697\?text=/);
        await sinDesbordamiento(page);
    }
    const boton = page.locator("[data-menu-toggle]");
    if (page.viewportSize().width < 992) await boton.click();
    await page.locator("#menu-principal").getByRole("link", { name: "Nosotros", exact: true }).click();
    await expect(page).toHaveURL(/\/#nosotros$/);
    await expect(page.locator("#nosotros")).toBeVisible();
});

test.describe("sin JavaScript", () => {
    test.use({ javaScriptEnabled: false });
    test("la navegación permanece visible y existe contacto alternativo", async ({ page }) => {
        await page.goto("/agendar-cita");
        await expect(page.locator("#menu-principal").getByRole("link", { name: "Servicios", exact: true })).toBeVisible();
        await expect(page.locator("[data-menu-toggle]")).toBeHidden();
        await expect(page.locator("#propietario")).toBeDisabled();
        await expect(page.getByRole("button", { name: "Preparar solicitud", exact: true })).toBeDisabled();
        await expect(page.getByRole("link", { name: "escríbenos directamente por WhatsApp", exact: true })).toHaveAttribute("href", /^https:\/\/wa\.me\/51990853697\?text=/);
        await sinDesbordamiento(page);
    });
});
