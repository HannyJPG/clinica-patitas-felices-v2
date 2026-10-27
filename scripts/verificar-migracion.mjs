import assert from "node:assert/strict";
import { readFile, access } from "node:fs/promises";
import { resolve, join } from "node:path";

const salida = resolve("dist");
const rutas = ["/", "/agendar-cita", "/login", "/soon", "/tienda", "/doctor", "/admin"];

function archivoDeRuta(ruta) {
    return ruta === "/" ? join(salida, "index.html") : join(salida, ruta.slice(1), "index.html");
}

function etiquetas(html) {
    // Los scripts se verifican como elementos, sin interpretar su código como HTML.
    const limpio = html.replace(/(<script\b[^>]*>)[\s\S]*?<\/script>/gi, "$1</script>");
    return [...limpio.matchAll(/<([a-z][\w:-]*)\b([^>]*?)>/gi)].map(([, tag, atributos]) => ({
        tag: tag.toLowerCase(),
        attrs: Object.fromEntries([...atributos.matchAll(/([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g)].map(([, nombre, doble, simple]) => [nombre, doble ?? simple]))
    }));
}

const paginas = new Map(await Promise.all(rutas.map(async ruta => [ruta, await readFile(archivoDeRuta(ruta), "utf8")])));

for (const ruta of rutas) {
    const html = paginas.get(ruta);
    const tags = etiquetas(html);
    const ids = tags.flatMap(({ attrs }) => attrs.id ? [attrs.id] : []);
    assert.equal(new Set(ids).size, ids.length, `${ruta}: hay ID repetidos`);
    assert.equal(tags.filter(({ tag }) => tag === "title").length, 1, `${ruta}: título duplicado`);
    assert.equal(tags.filter(({ tag }) => tag === "h1").length, 1, `${ruta}: debe haber un solo título principal`);
    assert.equal(tags.filter(({ tag }) => tag === "footer").length, 1, `${ruta}: debe haber un solo pie de página`);
    assert.equal(tags.filter(({ tag }) => tag === "main").length, 1, `${ruta}: debe haber un solo contenido principal`);
    assert.ok(!/Minny|Cookies|galletas|reposter|Pepsi|antojo|add-to-cart/.test(html), `${ruta}: quedan textos o acciones de la plantilla de panadería`);
    const etiquetasFormulario = tags.filter(({ tag }) => tag === "label").map(({ attrs }) => attrs.for);
    for (const { tag, attrs } of tags) {
        if (["input", "select", "textarea"].includes(tag)) assert.ok(etiquetasFormulario.includes(attrs.id), `${ruta}: control sin etiqueta: ${attrs.id}`);
        if (tag === "img") assert.ok(Object.hasOwn(attrs, "alt"), `${ruta}: imagen sin texto alternativo`);
    }

    const scriptsBootstrap = tags.filter(({ tag, attrs }) => tag === "script" && attrs.src?.includes("bootstrap.bundle.min.js"));
    assert.equal(scriptsBootstrap.length, 1, `${ruta}: Bootstrap JS debe cargarse una vez`);
    assert.equal(tags.filter(({ tag, attrs }) => tag === "script" && attrs.type === "module").length > 0, true, `${ruta}: falta JavaScript de navegador procesado por Astro`);

    const estilos = tags.filter(({ tag, attrs }) => tag === "link" && attrs.rel === "stylesheet" && attrs.href?.startsWith("/"));
    assert.equal(estilos.length, 1, `${ruta}: se espera una hoja CSS común`);
    const css = await readFile(join(salida, estilos[0].attrs.href.slice(1)), "utf8");
    // Vite puede retirar el comentario de versión al minimizar; comprobar su bloque de variables.
    assert.equal((css.match(/--bs-blue:/g) ?? []).length, 1, `${ruta}: Bootstrap CSS duplicado o ausente`);
    assert.ok(css.indexOf("--bs-blue:") < css.indexOf("--patitas-primary:"), `${ruta}: el tema debe aparecer después de Bootstrap`);
    assert.ok(css.includes("object-fit:contain"), "Falta la proporción del carrusel");

    for (const { tag, attrs } of tags) {
        for (const atributo of ["aria-controls", "aria-labelledby", "aria-describedby"]) {
            for (const id of (attrs[atributo] ?? "").split(/\s+/).filter(Boolean)) {
                assert.ok(ids.includes(id), `${ruta}: ${atributo} apunta a ${id}, que no existe`);
            }
        }
        for (const atributo of ["href", "src", "poster", "data-bs-target"]) {
            const valor = attrs[atributo];
            if (!valor || valor.startsWith("http") || valor.startsWith("data:")) continue;
            if (valor.startsWith("#")) {
                assert.ok(ids.includes(valor.slice(1)), `${ruta}: destino inexistente ${valor}`);
                continue;
            }
            assert.ok(valor.startsWith("/"), `${ruta}: ruta relativa sin migrar: ${valor}`);
            if (tag === "a") {
                const url = new URL(valor, "https://patitas.local");
                const destino = url.pathname;
                assert.ok(rutas.includes(destino), `${ruta}: enlace a una página ausente: ${valor}`);
                await access(archivoDeRuta(destino));
                if (url.hash) {
                    const destinos = etiquetas(paginas.get(destino)).map(({ attrs }) => attrs.id);
                    assert.ok(destinos.includes(decodeURIComponent(url.hash.slice(1))), `${ruta}: sección ausente: ${valor}`);
                }
            } else if (["img", "script", "link", "video", "source"].includes(tag)) {
                await access(join(salida, valor.split(/[?#]/)[0].slice(1)));
            }
        }
    }
    console.log(`Correcto: ${ruta} — enlaces, recursos, ID y carga única de Bootstrap.`);
}

console.log("Verificación del resultado compilado completada. Esta comprobación no sustituye la revisión visual.");
