/* Navegación y carruseles con Bootstrap, más registro de PWA (App instalable). */
(() => {
    if ("serviceWorker" in navigator) {
        window.addEventListener("load", () => {
            navigator.serviceWorker.register("/sw.js").catch(() => {});
        });
    }

    let eventoInstalacionPwa = null;
    window.addEventListener("beforeinstallprompt", evento => {
        evento.preventDefault();
        eventoInstalacionPwa = evento;
        document.querySelectorAll("[data-instalar-app]").forEach(btn => {
            btn.hidden = false;
        });
    });

    document.querySelectorAll("[data-instalar-app]").forEach(btn => {
        btn.addEventListener("click", async () => {
            if (eventoInstalacionPwa) {
                eventoInstalacionPwa.prompt();
                await eventoInstalacionPwa.userChoice;
                eventoInstalacionPwa = null;
            } else {
                window.open(window.location.origin, "PatitasFelicesApp", "width=430,height=820,menubar=no,toolbar=no,location=no,status=no");
            }
        });
    });

    const menu = document.querySelector("[data-main-menu]");
    const botonMenu = document.querySelector("[data-menu-toggle]");
    if (menu && botonMenu && window.bootstrap) {
        menu.classList.add("collapse");
        botonMenu.hidden = false;
        const plegable = window.bootstrap.Collapse.getOrCreateInstance(menu, { toggle: false });
        function cerrarMenu(alCerrar) {
            if (menu.classList.contains("collapsing")) {
                const evento = botonMenu.getAttribute("aria-expanded") === "true" ? "shown.bs.collapse" : "hidden.bs.collapse";
                menu.addEventListener(evento, () => cerrarMenu(alCerrar), { once: true });
                return;
            }
            if (!menu.classList.contains("show")) {
                alCerrar?.();
                return;
            }
            if (alCerrar) menu.addEventListener("hidden.bs.collapse", alCerrar, { once: true });
            plegable.hide();
        }
        menu.addEventListener("shown.bs.collapse", () => {
            botonMenu.setAttribute("aria-label", "Cerrar menú de navegación");
        });
        menu.addEventListener("hidden.bs.collapse", () => {
            botonMenu.setAttribute("aria-label", "Abrir menú de navegación");
        });
        menu.querySelectorAll("a").forEach(enlace => {
            enlace.addEventListener("click", evento => {
                if (!window.matchMedia("(max-width: 991.98px)").matches) return;
                const destino = new URL(enlace.href, window.location.href);
                if (destino.pathname === window.location.pathname && destino.hash) {
                    evento.preventDefault();
                    cerrarMenu(() => window.location.assign(destino.href));
                } else {
                    cerrarMenu();
                }
            });
        });
        menu.closest("nav").addEventListener("keydown", evento => {
            if (evento.key === "Escape" && botonMenu.getAttribute("aria-expanded") === "true") {
                evento.preventDefault();
                cerrarMenu();
                botonMenu.focus();
            }
        });
        window.matchMedia("(min-width: 992px)").addEventListener("change", evento => {
            if (evento.matches) cerrarMenu();
        });
    }

    if (window.bootstrap) {
        document.querySelectorAll("[data-manual-carousel]").forEach(carrusel => {
            window.bootstrap.Carousel.getOrCreateInstance(carrusel, { interval: false, ride: false });
        });
    }

    const video = document.querySelector("[data-hero-video]");
    const botonVideo = document.querySelector("[data-hero-video-toggle]");
    if (!video || !botonVideo) return;
    const movimientoReducido = window.matchMedia("(prefers-reduced-motion: reduce)");
    botonVideo.hidden = false;
    async function reproducirVideo() {
        botonVideo.disabled = true;
        try {
            video.hidden = false;
            await video.play();
        } catch {
            video.hidden = true;
        } finally {
            botonVideo.disabled = false;
        }
    }
    video.addEventListener("play", () => { botonVideo.textContent = "Pausar video de fondo"; });
    video.addEventListener("pause", () => { botonVideo.textContent = "Reproducir video de fondo"; });
    video.addEventListener("error", () => { video.hidden = true; botonVideo.hidden = true; });
    botonVideo.addEventListener("click", () => {
        if (video.paused) reproducirVideo();
        else video.pause();
    });
    movimientoReducido.addEventListener("change", evento => {
        if (evento.matches) video.pause();
    });
    if (!movimientoReducido.matches) reproducirVideo();
})();
