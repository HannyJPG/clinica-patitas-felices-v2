# Integración de Bootstrap en Patitas felices

> Esta guía describe la integración HTML previa. La versión actual está migrada a Astro y se desarrolla en `src/`; consulta [README.md](README.md).

> Los archivos HTML originales y sus recursos están archivados en `legacy/html-original/` para evitar conflictos con las rutas del servidor Astro.

La página original **no utilizaba Bootstrap**: solo cargaba `style.css`, Google Fonts y dos referencias a un archivo inexistente, `bakery.js`. La clase `.card` estaba definida por tu propio CSS; tener ese nombre no significaba que Bootstrap estuviera instalado.

Se integró **Bootstrap 5.3.8** con archivos locales. No necesitas npm, un compilador ni jQuery para esta página.

Actualización: se añadieron un carrusel y una página de citas veterinarias de demostración. Su funcionamiento y validaciones se explican en [README_CITAS.md](README_CITAS.md).

## 1. Archivos y rutas

```text
frontend_Veterinaria/
├── index.html
├── login.html                         (continúa vacío)
├── style.css                          (tu tema)
├── funciones.js                       (inicia el carrusel manual)
├── imagenes/
│   └── logotipoveterinaria.jpg
└── assets/vendor/bootstrap/
    ├── LICENSE
    ├── css/
    │   ├── bootstrap.min.css
    │   └── bootstrap.min.css.map
    └── js/
        ├── bootstrap.bundle.min.js
        └── bootstrap.bundle.min.js.map
```

`vendor` agrupa código de terceros. Los archivos `.map` ayudan a las herramientas de desarrollo a mostrar el código fuente original; no necesitas modificarlos. Se conserva la licencia MIT de Bootstrap.

En el `<head>` de `index.html`:

```html
<link rel="stylesheet" href="assets/vendor/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" href="style.css">
```

Antes de `</body>`:

```html
<script src="assets/vendor/bootstrap/js/bootstrap.bundle.min.js"></script>
<script src="funciones.js"></script>
```

Estas rutas son relativas a `index.html`, que está en la raíz del proyecto. Funcionan al abrir ese archivo y al servir el proyecto desde una subcarpeta. Si después mueves el HTML a `paginas/`, deberás usar `../assets/vendor/bootstrap/...` y `../style.css`.

Las rutas `url(...)` escritas dentro de un CSS se resuelven desde la carpeta del propio CSS, no desde el HTML.

Bootstrap se carga **antes** de `style.css`: en reglas con la misma prioridad y especificidad, gana la que aparece después. Una regla con un selector más específico, un estilo inline o `!important` puede cambiar ese resultado. Por eso también se retiraron los estilos inline y las reglas antiguas que interferían con los componentes.

`bootstrap.bundle.min.js` incluye Popper. Se carga una sola vez y antes de tu JavaScript, para que puedas usar Bootstrap desde `funciones.js` cuando añadas comportamiento propio.

## 2. Colores y tipografía en style.css

La paleta sigue usando los marrones, beiges y cremas del original. Ahora está centralizada al principio de `style.css`:

| Variable propia | Valor | Uso |
| --- | --- | --- |
| `--patitas-primary` | `#776b5d` | Encabezados, enlaces y botones principales |
| `--patitas-primary-hover` | `#5c5146` | Botones y enlaces al pasar el puntero |
| `--patitas-primary-active` | `#4e453b` | Botones al pulsarlos |
| `--patitas-background` | `#f3eeea` | Fondo general |
| `--patitas-surface` | `#fff7f0` | Tarjetas y paneles |
| `--patitas-accent` | `#ebe3d5` | Fondos de secciones |
| `--patitas-border` | `#b0a695` | Bordes |
| `--patitas-text` | `#333333` | Texto principal |
| `--patitas-muted` | `#5e554a` | Texto secundario |
| `--patitas-font` | `"Work Sans", system-ui, ...` | Familia tipográfica |

Las tarjetas de producto ahora tienen fondo crema y texto oscuro. Los párrafos que antes usaban crema sobre beige también pasan a texto oscuro para facilitar la lectura.

Las variables propias se conectan con las de Bootstrap:

```css
:root {
    --patitas-primary: #776b5d;
    --patitas-font: "Work Sans", system-ui, sans-serif;
    --bs-primary: var(--patitas-primary);
    --bs-primary-rgb: 119, 107, 93;
    --bs-body-font-family: var(--patitas-font);
}
```

Así Bootstrap y tus clases comparten valores. Si cambias el color principal, actualiza también `--bs-primary-rgb` con sus tres canales RGB, sin `rgb(...)`. Se incluyen igualmente las parejas hexadecimal/RGB del fondo, el texto y los enlaces para que las utilidades que usan RGB sean coherentes.

**Cambiar `--bs-primary` por sí solo no cambia todos los componentes compilados.** Por eso `.btn-primary` y `.btn-outline-primary` personalizan sus variables `--bs-btn-*`, incluyendo los estados normal, hover, foco, activo y deshabilitado. Otras variantes, como `.btn-success`, mantienen sus colores originales hasta que las personalices expresamente.

Se mantiene Work Sans y se solicitan los pesos 400, 500, 600 y 700, además de la cursiva 400. Antes solo se solicitaba el peso 500, aunque la página utilizaba negritas. Los títulos usan 600 y los botones 600; los párrafos usan 400.

La fuente sigue descargándose de Google Fonts, como en el original. **Bootstrap es local; Work Sans requiere conexión.** Si la fuente no carga, se utiliza la tipografía del sistema. Los títulos y los espacios de sección usan `clamp(...)` para adaptar su tamaño a la pantalla.

## 3. Cuadrícula adaptable

Los productos utilizan esta estructura:

```html
<div class="container">
  <div class="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-4">
    <div class="col">
      <div class="producto h-100">
        <!-- Tu imagen, título, precio y botón -->
      </div>
    </div>
  </div>
</div>
```

- `.container` centra el contenido y limita su anchura.
- `.row` organiza las columnas.
- `.row-cols-1` muestra un producto por fila en pantallas pequeñas.
- `.row-cols-md-2` muestra dos desde 768 px.
- `.row-cols-xl-3` muestra tres desde 1200 px, si hay suficientes productos.
- `.g-4` añade separación entre columnas y filas.
- `.col` controla el ancho; `.producto` controla colores, borde y espacio interior.
- `.h-100` iguala la altura de las tarjetas de una misma fila.
- `.img-fluid` limita la imagen al ancho disponible y mantiene su proporción.

Las secciones de presentación usan `.col-12` y `.col-lg-*`: se apilan en pantallas pequeñas y se reparten el ancho a partir de 992 px.

## 4. Conflictos corregidos

| Antes | Cambio y motivo |
| --- | --- |
| `.card` tenía un estilo propio y ancho fijo de 300 px | Se renombró a `.patitas-card`. Bootstrap ya define `.card`; mantener el mismo nombre mezclaría ambos estilos. Esa clase no se utilizaba en el HTML actual. |
| `.producto` imponía 280 px y luego 80 % en móvil | Se eliminaron esos anchos. Ahora `.col` calcula el tamaño y las tarjetas pueden adaptarse sin competir con la cuadrícula. |
| `.about-wrapper` imponía otro sistema flex y `gap` | Se dejó la distribución a `.row`, `.col-*` y `.g-4`, conservando la apariencia en `.about-wrapper`. |
| Reglas generales como `header` y `header a` | Se sustituyeron por `.site-header`, `.brand-header` y `.site-nav`, para que el tema no afecte accidentalmente a otros encabezados. |
| `#productos h2`, `#productos p` y `#testimonios` usaban `position: fixed` | Se quitaron. Sacaban el contenido del flujo y provocaban superposiciones al desplazarse. |
| Las presentaciones tenían `height: 100vh` | Se retiró la altura fija. Los textos largos ahora pueden aumentar la altura de la sección. |
| Botones con estilos dispersos, reglas por ID y estilos inline | Se usan `.btn` y sus variantes, personalizadas en `style.css`. Las clases `.add-to-cart` y `.btn-ir-a-comprar` se conservan. |
| El carrito imponía `display: none`, posición y `z-index` propios | Se sustituyó por el componente `offcanvas`. Bootstrap gestiona esas propiedades y su fondo superpuesto. |

Bootstrap también aplica su normalización de estilos, llamada Reboot, incluyendo `box-sizing: border-box`. Con ella, el borde y el padding se incluyen en las medidas de ancho y alto. Al eliminar los anchos rígidos, el diseño funciona con ese modelo de caja.

No se editó el código de Bootstrap ni se añadieron reglas `!important`. Las preferencias de movimiento reducido desactivan el desplazamiento suave y la animación propia de las tarjetas.

## 5. HTML y contenido conservado

- Se conserva el texto de la clínica y de Minny & Cookies, los 12 bloques de producto con sus precios y atributos `data-*`, los cuatro testimonios y los dos pies originales. También se mantienen ambos catálogos y ambos paneles de carrito.
- Se agruparon los seis productos del primer catálogo, que tenían cierres de etiquetas intercalados, y se dejó la presentación del equipo a continuación. El segundo catálogo conserva sus categorías.
- Se cerraron correctamente los bloques, se añadió `<main>` y se repararon comentarios HTML mal formados. El producto de ejemplo comentado no se publica.
- Se retiraron un encabezado vacío y los atributos generados `data-astro-cid-*`, que no tenían contenido ni reglas asociadas en este proyecto.
- Se eliminaron las cargas duplicadas de CSS, fuentes y scripts, así como el segundo `title`, `charset` y `viewport`.
- Se dejó un solo favicon, usando el JPG que sí existe en `imagenes/`, con el tipo `image/jpeg`.
- Se ajustaron los niveles de títulos: hay un solo `h1` principal; los demás encabezados de sección usan `h2` o `h3`, conservando sus textos.
- Los ID repetidos se hicieron únicos. La segunda presentación usa `about-us-equipo`; el segundo catálogo, `productos-categorias`; los segundos testimonios, `testimonios-adicionales`. El segundo carrito y sus elementos usan el sufijo `-catalogo`.
- Las secciones repetidas comparten clases como `.productos`, `.about-section` y `.testimonios`. Un ID identifica un solo elemento; una clase puede repetirse.
- El primer enlace “Ir a comprar” ahora apunta a `#productos`: el destino anterior, `#reserva`, no existía.
- Se corrigieron los textos alternativos de las imágenes de gelatina y Pepsi para que describan esos productos.
- Los botones tienen `type="button"` y los enlaces que abren otra pestaña tienen `rel="noopener"`.
- Se sustituyeron las dos referencias a `bakery.js` por una sola carga del archivo existente `funciones.js`. Posteriormente se añadió a este archivo la inicialización del carrusel manual.
- `login.html` continúa vacío; no se inventó una página de acceso.

## 6. Paneles del carrito

Los botones de los dos encabezados abren sus respectivos paneles mediante atributos de Bootstrap:

```html
<button type="button" data-bs-toggle="offcanvas"
        data-bs-target="#cart" aria-controls="cart">Carrito</button>

<aside id="cart" class="offcanvas offcanvas-end"
       tabindex="-1" aria-labelledby="cart-title">
  <h2 id="cart-title">Carrito de compras</h2>
  <button type="button" data-bs-dismiss="offcanvas">Cerrar</button>
</aside>
```

`data-bs-target` debe coincidir con el ID del panel. `aria-labelledby` lo relaciona con su título. Bootstrap proporciona apertura, cierre, gestión del foco, fondo y cierre con Escape. El CSS solo personaliza el ancho y los colores del panel.

**Esto no implementa las compras.** No había código de carrito disponible: `bakery.js` no existe y `funciones.js` ahora solo inicia el carrusel. Añadir productos, actualizar cantidades y totales, comprar y contactar por WhatsApp siguen pendientes. Los dos carritos conservados tampoco comparten un estado de compra todavía.

## 7. Recursos que ya faltaban

No hay carpeta `imgs/` en este proyecto. Se conservaron las referencias para no sustituir tus imágenes por otras distintas. Faltan:

```text
imgs/about-us.jpg
imgs/productos/pack-3-galletas-clasicas.png
imgs/productos/pack-5-galletas-clasicas.png
imgs/productos/keke-de-platano.png
imgs/productos/muffin-de-chocochips.png
imgs/productos/gelatina.png
imgs/productos/pepsi-355ml.png
soon.html
```

Cuando tengas las imágenes, puedes crear esas carpetas y añadir los archivos, o moverlas a `imagenes/` y actualizar sus atributos `src`. Si están en `imagenes/productos/`, por ejemplo, la ruta sería `imagenes/productos/gelatina.png`.

La referencia de fondo a `imgs/minny.jpg`, también ausente, se sustituyó por un fondo del tema en `#minny`. La referencia duplicada a `imgs/favico.ico` se retiró al conservar el favicon que sí existe.

## 8. Comprobaciones realizadas

- Etiquetas correctamente anidadas y cerradas; 26 ID únicos.
- Destinos de enlaces internos, `data-bs-target`, `aria-controls` y `aria-labelledby` existentes.
- CSS y JavaScript locales presentes y cargados una sola vez, en el orden esperado.
- Conservación de textos, productos, precios, testimonios y pies mediante comparación con el HTML original.
- Sintaxis de JavaScript comprobada con `node --check`.
- Hashes SHA-384 de los dos archivos minificados coincidentes con los publicados en la documentación oficial de Bootstrap 5.3.8.

**Límite de verificación:** no se completó la revisión visual ni la prueba interactiva de los paneles. La herramienta de control del navegador se detuvo porque no pudo identificar con seguridad la URL de Chrome. La distribución móvil y el comportamiento en ejecución deben confirmarse en el navegador.

Para comprobarlo manualmente, abre `index.html`, revisa el diseño con una ventana estrecha y otra ancha, abre los dos carritos y comprueba el cierre con “Cerrar” y con Escape. Las imágenes seguirán sin mostrarse hasta que añadas sus archivos.

## Referencias oficiales

- [Descarga de Bootstrap y versión utilizada](https://getbootstrap.com/docs/5.3/getting-started/download/)
- [Introducción y hashes oficiales de integridad](https://getbootstrap.com/docs/5.3/getting-started/introduction/)
- [Variables CSS de Bootstrap](https://getbootstrap.com/docs/5.3/customize/css-variables/)
- [Variables de los botones](https://getbootstrap.com/docs/5.3/components/buttons/#variables)
- [Cuadrícula](https://getbootstrap.com/docs/5.3/layout/grid/)
- [Paneles offcanvas](https://getbootstrap.com/docs/5.3/components/offcanvas/)
