# Clínica Patitas Felices — Sistema Integral (Astro + FastAPI + 4 Patrones GoF + 16 Tablas)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/HannyJPG/clinica-patitas-felices-v2)

Proyecto Astro 7.4.2 + Backend Python (FastAPI) con los **4 Patrones de Diseño GoF** (`Proxy`, `Strategy + RBAC`, `Adapter`, `Facade`), **Base de Datos de 16 Tablas** (`prueba_1.erd.json`), **Generador de Boletas PDF en memoria** y **PWA instalable**.

- **Despliegue en la Nube (1 clic en Render)**: [https://render.com/deploy?repo=https://github.com/HannyJPG/clinica-patitas-felices-v2](https://render.com/deploy?repo=https://github.com/HannyJPG/clinica-patitas-felices-v2)
- **Guía de Sustentación, UML y DER**: Ver [`docs/ARQUITECTURA_UML_DER_SUSTENTO.md`](docs/ARQUITECTURA_UML_DER_SUSTENTO.md)
- **Iniciar todo en un solo comando**: `npm.cmd start` o doble clic en `iniciar-todo.bat`
- **Abrir como App de Escritorio**: Doble clic en `PatitasFelices_App.bat`

## Iniciar el proyecto

Requisitos del paquete instalado: Node.js >=22.23.4 y npm >=9.6.5. Se comprobó con Node 24.22.0 y npm 11.19.1.

```powershell
npm install
npm run dev
```

Abre la dirección que imprima Astro, normalmente http://127.0.0.1:4321/. Si ese puerto está ocupado, utilizará otro. En PowerShell puedes usar `npm.cmd` si el sistema bloquea `npm.ps1`.

```powershell
npm test
npm run build
npm run check:build
npm run preview
```

No edites `dist/`, `.astro/`, `node_modules/` ni `.npm-cache/`. Son carpetas generadas.

## Qué cambió al pulir el diseño

Se conservaron colores, fuente, logotipo, fotografías y textos veterinarios. Se retiraron de la aplicación Astro los restos de la plantilla de panadería: Minny & Cookies, productos, precios, carritos, reseñas de galletas y pie duplicado. Los HTML, CSS y JavaScript originales están conservados en `legacy/html-original/`, con copias de sus recursos.

Se archivaron fuera de la raíz porque `agendar-cita.js` estaba interceptando la ruta `/agendar-cita` en el servidor de desarrollo: devolvía JavaScript en lugar de la página Astro. La ruta actual ya devuelve HTML y el formulario correcto.

La portada se organiza en cuatro secciones: servicios, nosotros, espacio para experiencias y acceso al formulario de citas. Hay una sola navegación y un solo pie compartidos por todas las páginas.

No se transformaron opiniones de panadería en reseñas veterinarias falsas. El carrusel muestra textos de compromiso de la clínica y explica que las opiniones reales están pendientes. Sus fotografías son ilustrativas.

## Páginas

| Archivo | Ruta | Función |
| --- | --- | --- |
| `src/pages/index.astro` | `/` | Portada de la clínica |
| `src/pages/agendar-cita.astro` | `/agendar-cita` | Solicitud de cita mediante enlace a WhatsApp |
| `src/pages/login.astro` | `/login` | Información sobre el acceso todavía no disponible |
| `src/pages/soon.astro` | `/soon` | Espacio de novedades próximas |

Los enlaces a servicios, nosotros y opiniones funcionan también desde las páginas interiores: `/#servicios`, `/#nosotros` y `/#testimonios`.

## Cómo está organizado

| Archivo o carpeta | Responsabilidad |
| --- | --- |
| `src/layouts/Layout.astro` | Documento HTML, título, fuente, estilos, enlace para saltar al contenido, Header, Footer y JavaScript común |
| `src/components/Header.astro` | Navegación de Bootstrap y portada fotográfica en la página de inicio |
| `src/components/Footer.astro` | Identidad, enlaces y año actual de Lima |
| `src/components/Servicios.astro` | Cuatro tarjetas con enlaces al formulario |
| `src/components/SelectorServicio.astro` | Selector de servicios del formulario |
| `src/components/SobreNosotros.astro` | Presentación y textos veterinarios existentes |
| `src/components/Testimonios.astro` | Carrusel de compromisos mientras se recopilan opiniones reales |
| `src/components/Contacto.astro` | Acceso final al formulario, con aviso de demostración |
| `src/components/FormularioCita.astro` | Campos, ayuda, errores, resumen y explicación de la prueba |
| `src/data/servicios.js` | Lista única de servicios, títulos, descripciones e iconos |
| `src/data/clinica.js` | WhatsApp confirmado, teléfono visible, duración de 30 minutos y zona horaria |
| `src/data/portada.js` | Fotografía de portada y video opcional |
| `src/scripts/main.js` | Menú móvil, carrusel y reproducción opcional del video |
| `src/scripts/validar-cita.js` | Reglas de validación, hora de Lima y servicio desde la URL |
| `src/scripts/agendar-cita.js` | Validación, resumen y preparación del enlace de WhatsApp |
| `src/scripts/whatsapp.js` | Construcción del mensaje y del enlace al número de la clínica |
| `src/styles/global.css` | Tema y ajustes adaptables |
| `public/img/` | Dos fotografías y el logotipo originales |
| `public/vendor/bootstrap/` | Bundle JavaScript, mapa y licencia originales |

Se retiraron los componentes que solo contenían el catálogo y las secciones de la panadería. Los archivos históricos y los documentos de las etapas previas se conservan.

## Estilos y recursos

`global.css` importa primero el Bootstrap local de `src/styles/vendor/` y aplica después el tema personalizado. No se añadieron dependencias. Los componentes comparten una escala de títulos, espacios, bordes, radios y botones.

Puedes cambiar la identidad desde las variables `--patitas-*` del comienzo de esa hoja. Las variantes de botones usan las variables `--bs-btn-*` para conservar colores coherentes al pasar el puntero, pulsar, enfocar o deshabilitar.

El menú se pliega por debajo de 992 px. Con JavaScript abre y cierra mediante Bootstrap, se cierra al elegir un destino y admite Escape. Sin JavaScript, sus enlaces quedan visibles. Hay foco visible, áreas de pulsación de al menos 44 px y un enlace para saltar al contenido.

Las tarjetas muestran cuatro columnas en pantallas grandes, dos desde 768 px y una en celular. Los paneles de foto y texto se apilan en pantallas estrechas. El texto del carrusel se coloca en un panel claro separado de la imagen.

Las imágenes de contenido usan `object-fit: contain` para verse completas. El fondo de portada usa `cover`: recorta lo necesario para llenar el marco y mantiene la proporción. La capa oscura protege la lectura del título y las acciones.

Work Sans sigue viniendo de Google Fonts, con una fuente de sistema como alternativa. Bootstrap e imágenes son locales.

## Video de portada

Todavía no hay un archivo de video local. La portada utiliza la fotografía indicada en `src/data/portada.js`. Cuando tengas uno, guárdalo en `public/video/` y configura:

```js
export const portada = {
    imagen: "/img/imagen_familia1.jpg",
    video: "/video/portada.mp4",
    tipoVideo: "video/mp4"
};
```

El video se reproducirá silenciado y en bucle con control de pausa, salvo que el visitante prefiera movimiento reducido. Si no puede reproducirse, queda la fotografía. Las plantillas de `referencias/` siguen vacías: el diseño no depende de su contenido.

## Formulario y backend

Las tarjetas de servicio abren una URL como `/agendar-cita?servicio=vacunacion`. El formulario preselecciona solo valores que están en la lista permitida. Opciones, tarjetas y validación comparten esa misma lista.

Se conservan los siete campos y sus reglas: propietario de 2 a 80 caracteres; teléfono de 9 a 15 dígitos; mascota de hasta 60 caracteres; servicio válido; fecha y hora futuras según Lima; motivo de 10 a 1000 caracteres. Los campos son obligatorios y no aceptan solo espacios. Las horas deben corresponder a intervalos de 30 minutos, como 09:00 o 09:30.

El botón **Preparar solicitud** muestra un resumen. **Continuar en WhatsApp** abre un enlace a **+51 990 853 697** con los siete campos, fecha, hora y duración de 30 minutos. La persona revisa el mensaje y pulsa Enviar dentro de WhatsApp. El enlace se construye con el formato oficial `wa.me` y texto codificado: [documentación de WhatsApp](https://faq.whatsapp.com/5913398998672934).

La web no envía mensajes automáticamente, no guarda datos y no comprueba cupos. La clínica confirma por WhatsApp el horario de atención, la disponibilidad y la reserva. No se inventó un horario de apertura.

Al modificar un campo se oculta el resumen anterior y se elimina su enlace. Al limpiar, se borran todos los datos y errores. Los mensajes están asociados a los controles y el primero incorrecto recibe el foco. Sin JavaScript, los campos permanecen deshabilitados y se ofrece un enlace directo de contacto por WhatsApp.

Por indicación del usuario, **no se avanzó el backend**. Esta etapa es de frontend y solicitud por WhatsApp. Para una etapa posterior quedan:

- Agenda real, disponibilidad y duración de las atenciones.
- API y base de datos para guardar citas, con validación de servidor y protección contra duplicados.
- Autenticación del acceso de usuarios.
- La dirección y el horario de atención, si se desean publicar. El WhatsApp ya está configurado con el número confirmado.
- Opiniones reales de clientes para reemplazar los textos de compromiso del carrusel.
- Un video local, si se desea sustituir la foto de fondo.

No se inventaron precios, horarios, dirección, reseñas ni credenciales.

## Comprobaciones realizadas

- `npm run build`: cuatro páginas generadas correctamente.
- `npm test`: 20 pruebas de validación, intervalos de media hora, preselección de servicios y generación segura del enlace de WhatsApp.
- `npm run check:build`: enlaces entre páginas y secciones, recursos locales, etiquetas de formulario, referencias de accesibilidad, carga única de Bootstrap, un H1 y un Footer por página, y ausencia de los textos de panadería.
- Sintaxis JavaScript correcta y respuesta HTTP 200 de la vista de producción.

## Pruebas del frontend con Playwright

Se añadió Playwright como dependencia de desarrollo con autorización del usuario. No añade peso a la web publicada. En Windows utiliza el Chrome instalado en un perfil de pruebas separado; también puede usar Edge con `$env:PLAYWRIGHT_BROWSER_CHANNEL = 'msedge'`.

```powershell
npm run test:e2e
```

La configuración reutiliza el servidor local en http://127.0.0.1:4321/ o lo inicia si no está ejecutándose. Comprueba cuatro tamaños: computadora (1440 px), tablet (768 px), celular (390 px) y pantalla compacta (320 px).

Las pruebas cubren menú, cierre con Escape, navegación durante las transiciones, carrusel con teclado e indicadores, imágenes, desbordamientos, selección de servicios, errores del formulario, resumen, enlace de WhatsApp y limpieza de datos. También comprueban la navegación y el contacto alternativo sin JavaScript. Las peticiones a WhatsApp se bloquean dentro de las pruebas: no se envían mensajes.

Las capturas quedan en `artifacts/frontend/` y el informe en `playwright-report/`. Son resultados locales, no se publican con la página. El problema detectado al pulsar un enlace mientras el menú se abría se corrigió esperando la transición de Bootstrap antes de cerrar y navegar.

Para completar la revisión manual, usa anchos de 1440, 768 y 390 px, y comprueba también 320 px:

1. Abrir y cerrar el menú; elegir una sección desde inicio y desde una página interior.
2. Navegar por teclado y cerrar el menú con Escape.
3. Cambiar las dos diapositivas con flechas, indicadores y teclado.
4. Elegir un servicio desde su tarjeta y comprobar la selección del formulario.
5. Preparar una solicitud vacía, corregir errores, elegir una fecha futura y una hora de media hora, y limpiar datos.
6. Comprobar que no haya desplazamiento horizontal, fotos estiradas ni texto sobrepuesto.
7. Confirmar que el resumen permite continuar en WhatsApp y explica que la clínica debe confirmar la cita.

Los documentos `README_BOOTSTRAP.md` y `README_CITAS.md` describen las etapas HTML previas. Esta es la guía de la versión actual.
