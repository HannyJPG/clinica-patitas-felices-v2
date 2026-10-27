# Citas veterinarias y carrusel

> Esta guía corresponde a la etapa HTML original. La versión actual está en Astro: consulta [README.md](README.md), inicia con `npm run dev` y ejecuta las pruebas con `npm test`.

> Actualización: la versión Astro ahora prepara solicitudes por WhatsApp al número confirmado por la clínica, en intervalos de 30 minutos. La versión HTML descrita aquí se conserva en `legacy/html-original/`.

## Qué se encontró

Al revisar los archivos guardados en disco, `referencias/carousel.css`, `referencias/carousel2.rtl` y `referencias/referencias_boostrap.css` tenían 0 bytes. No había un formulario que adaptar. Se creó uno con los controles del Bootstrap 5.3.8 local y con la paleta y la tipografía de `style.css`. Los archivos de referencia se conservaron.

No existe una carpeta `img`. Las dos fotografías están en `imagenes/`:

- `imagenes/imagen_familia1.jpg`
- `imagenes/imagen_famlia2.jpg` (el nombre original tiene esa escritura)

El HTML guardado tampoco tenía carrusel ni botones “Agendar cita”; se añadieron cuatro enlaces a la nueva página.

## Archivos modificados y creados

| Archivo | Función |
| --- | --- |
| `agendar-cita.html` | Formulario de siete campos, mensajes accesibles y resumen de demostración |
| `agendar-cita.js` | Validaciones compartidas por la página y las pruebas, y comportamiento local del formulario |
| `index.html` | Carrusel de dos fotografías y enlaces de citas en navegación, ambas diapositivas y presentación de la clínica |
| `style.css` | Estilos del carrusel y formulario, usando las variables existentes del tema |
| `funciones.js` | Inicialización del carrusel manual de Bootstrap |
| `tests/citas.test.js` | Pruebas de las reglas de validación, sin dependencias adicionales |

`agendar-cita.html` está junto a `index.html`, por lo que todos los enlaces usan `href="agendar-cita.html"`. Ambas páginas comparten `assets/vendor/bootstrap/css/bootstrap.min.css`, `style.css`, Work Sans y los mismos colores y botones. La página de citas también permite volver al inicio.

## Fotografías sin deformación

El carrusel usa directamente los dos JPG disponibles y sus dimensiones originales. No utiliza SVG de ejemplo ni imágenes remotas.

```css
.carousel-media { aspect-ratio: 16 / 9; }
.carousel-photo {
    width: 100%;
    height: 100%;
    object-fit: contain;
}
```

`contain` muestra la foto completa y conserva su proporción. Si la proporción de la foto difiere del marco, queda un pequeño espacio con el color del tema. Los textos y botones van debajo de las fotos para no taparlas. La imagen lateral del formulario usa `width: 100%` y `height: auto`.

Los controles permiten avanzar, retroceder o elegir una fotografía. No hay reproducción automática. Se conserva el resto del contenido de la página, incluidos los bloques previos de Minny & Cookies; sus imágenes de producto ausentes siguen siendo un pendiente aparte.

## Reglas del formulario

| Campo | Validación |
| --- | --- |
| Propietario | Obligatorio, entre 2 y 80 caracteres después de quitar espacios exteriores |
| Teléfono | Obligatorio, entre 9 y 15 dígitos; permite `+` al inicio, espacios, guiones y paréntesis; hasta 25 caracteres contando separadores |
| Mascota | Obligatorio, entre 1 y 60 caracteres después de quitar espacios exteriores |
| Servicio | Debe pertenecer a la lista del formulario |
| Fecha | Fecha de calendario válida, hoy o posterior según Lima |
| Hora | Hora válida con precisión de minutos; si es hoy, debe ser posterior a la hora actual de Lima |
| Motivo | Obligatorio, entre 10 y 1000 caracteres después de quitar espacios exteriores |

Se usa `America/Lima` mediante `Intl.DateTimeFormat`, sin depender de la zona horaria del equipo del visitante. No se inventaron horarios de atención ni cupos disponibles: las horas válidas son preferencias para la demostración.

Cada control tiene etiqueta, mensaje de ayuda cuando corresponde y un mensaje de error asociado mediante `aria-describedby`. Los errores también aparecen en una lista con enlaces a los campos y se enfoca el primero que necesita corrección. Al corregir valores se actualiza el error del campo; al limpiar se retiran los errores y el resumen.

Los campos permanecen deshabilitados hasta que el JavaScript registra el manejador de envío. Si no carga el script, no se permite rellenar ni enviar el formulario. El envío se intercepta con `preventDefault()` y los datos del resumen se insertan con `textContent`, no como HTML.

## Qué significa “demostración”

En este proyecto no se encontraron servidor, API ni base de datos de citas. El formulario avisa de ello antes de rellenarlo, en el botón de envío y en el resumen final.

La página no hace peticiones de reserva, no usa `localStorage` ni escribe en una base de datos. Los valores se muestran únicamente en el formulario y en un resumen de la página. Editarlos oculta el resumen anterior. Limpiar el formulario elimina también el contenido del resumen. No se genera número de cita ni se presenta una confirmación real.

Las validaciones del navegador sirven para orientar a quien rellena el formulario. Para aceptar reservas reales, el servidor deberá volver a validar todos los datos.

## Qué falta para reservar citas reales

1. **Configurar la agenda de la clínica:** servicios reales, duración de cada atención, veterinarios, horarios, descansos y fechas bloqueadas.
2. **Consultar disponibilidad mediante una API:** obtener los turnos libres para el servicio y la fecha seleccionados. El campo de hora pasaría a ofrecer esos turnos, con estados de carga, ausencia de horarios y errores de conexión.
3. **Crear el endpoint de reservas y una base de datos:** guardar propietario, contacto, mascota, servicio, fecha, hora y motivo. En el servidor deben validarse nuevamente, normalizarse los teléfonos y tratarse las fechas con la zona horaria de la clínica.
4. **Evitar reservas simultáneas del mismo turno:** volver a comprobar el cupo al guardar y proteger la operación con transacciones o restricciones adecuadas. También debe evitarse crear duplicados si se reintenta una petición.
5. **Confirmar solo tras guardar:** mostrar el identificador y estado de la cita que devuelva el servidor. Si el turno dejó de estar disponible, pedir otro; si falla la petición, conservar el formulario para reintentar sin afirmar que se reservó.

Los servicios actuales son opciones de demostración y deben confirmarse con la clínica antes de habilitar reservas reales.

## Comprobaciones

Desde la raíz del proyecto:

```powershell
node --test tests/citas.test.js
node --check agendar-cita.js
node --check funciones.js
```

Las 14 pruebas pasan. Incluyen campos vacíos y espacios, límites de longitud, teléfonos válidos e inválidos, servicios manipulados, fechas imposibles y pasadas, años bisiestos, horas transcurridas, fechas futuras y cambios de día entre UTC y Lima.

También se comprobó el anidado del HTML, ID únicos por página, etiquetas de campos, referencias de accesibilidad, existencia de archivos locales del formulario y carrusel, y los cuatro enlaces hacia `agendar-cita.html`. El patrón de teléfono del HTML se compiló y se comprobó con ejemplos locales e internacionales.

No se ha completado una prueba visual o de interacción en navegador. La herramienta no dispone de un navegador conectado para la inspección DOM y la revisión anterior de Chrome quedó bloqueada al no poder determinar su URL con seguridad. Las pruebas automatizadas realizadas verifican las reglas JavaScript y la estructura de los archivos, no la representación final del navegador.

Para la comprobación manual, abre `index.html`, prueba las dos fotos y los cuatro enlaces. En el formulario prueba un envío vacío, un teléfono con letras, una fecha pasada, una hora ya transcurrida de hoy y una solicitud futura válida. Esta última debe mostrar exclusivamente un resumen de demostración. Revisa también una ventana estrecha y el botón “Limpiar formulario”.
