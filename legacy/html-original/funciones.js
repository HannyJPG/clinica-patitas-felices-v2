/* Carrusel manual: admite botones, teclado y gestos, sin cambiar de foto solo. */
(() => {
    const carrusel = document.getElementById("carrusel-familias");
    if (carrusel && window.bootstrap) {
        bootstrap.Carousel.getOrCreateInstance(carrusel, {
            interval: false,
            ride: false
        });
    }
})();
