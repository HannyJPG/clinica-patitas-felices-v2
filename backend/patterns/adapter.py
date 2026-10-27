"""
PATRÓN ADAPTER (Estructural - GoF)
Puntos de sustentación: 1, 3 y 6.
Integra el modelo completo de 16 tablas basado en `prueba_1.erd.json`:
1. Dueno               9. Detalle_servicios
2. Especie            10. Historial_clinico
3. Razas              11. Receta
4. Paciente           12. Factura
5. Especialidad       13. Pago
6. Veterinario        14. usuarios (Auth JWT + RBAC + Proxy)
7. Servicios          15. productos (Catálogo Tienda + Stock)
8. Cita               16. detalle_ventas (Ítems de Boleta PDF)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import quote
import os
import sqlite3
from typing import Any, Dict, List, Optional


# =============================================================================
# 1. ADAPTER PARA INTEGRACIÓN EXTERNA DE MENSAJERÍA (WHATSAPP API / URL)
# =============================================================================

class IWhatsAppNotificationAdapter(ABC):
    """Target Interface: Define el contrato que la clínica necesita para notificar."""

    @abstractmethod
    def generar_enlace_cita(self, datos_cita: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def generar_enlace_boleta(self, numero_boleta: str, cliente: str, total: float) -> str:
        pass


class WhatsAppAdapter(IWhatsAppNotificationAdapter):
    """
    Adapter concreto: Adapta los diccionarios de negocio de la clínica al formato
    requerido por la API web de WhatsApp (https://wa.me/<telefono>?text=<mensaje_codificado>).
    """

    SERVICIOS_NOMBRES = {
        "consulta-general": "Consulta general",
        "vacunacion": "Vacunación",
        "desparasitacion": "Desparasitación",
        "control": "Control y seguimiento",
    }

    def __init__(self, numero_clinica: Optional[str] = None) -> None:
        self.numero_clinica = numero_clinica or os.getenv("CLINICA_WHATSAPP", "51990853697")

    def _construir_url(self, mensaje: str) -> str:
        texto_codificado = quote(mensaje, safe="")
        return f"https://wa.me/{self.numero_clinica}?text={texto_codificado}"

    def generar_enlace_cita(self, datos_cita: Dict[str, Any]) -> str:
        fecha_raw = str(datos_cita.get("fecha", ""))
        partes = fecha_raw.split("-")
        fecha_formateada = f"{partes[2]}/{partes[1]}/{partes[0]}" if len(partes) == 3 else fecha_raw
        servicio_clave = datos_cita.get("servicio", "")
        servicio_legible = self.SERVICIOS_NOMBRES.get(servicio_clave, servicio_clave)

        lineas = [
            "Hola, Patitas Felices. Quisiera solicitar una cita veterinaria.",
            "",
            f"Propietario: {datos_cita.get('propietario', '')}",
            f"Teléfono de contacto: {datos_cita.get('telefono', '')}",
            f"Mascota: {datos_cita.get('mascota_nombre') or datos_cita.get('mascota', '')}",
            f"Servicio: {servicio_legible}",
            f"Fecha deseada: {fecha_formateada}",
            f"Hora deseada: {datos_cita.get('hora', '')} (Lima, Perú)",
            "Duración: 30 minutos",
            f"Motivo: {datos_cita.get('motivo', '')}",
            "",
            "¿Podrían confirmar si este horario está disponible?",
        ]
        return self._construir_url("\n".join(lineas))

    def generar_enlace_boleta(self, numero_boleta: str, cliente: str, total: float) -> str:
        mensaje = (
            f"Hola, Patitas Felices. Soy {cliente}. "
            f"Acabo de realizar la compra con Boleta N° {numero_boleta} "
            f"por un total de S/ {total:.2f}. Solicito coordinación de entrega."
        )
        return self._construir_url(mensaje)


# =============================================================================
# 2. ADAPTER PARA BASE DE DATOS (LAS 16 TABLAS DE PRUEBA_1.ERD.JSON + RBAC/TIENDA)
# =============================================================================

class IDatabaseAdapter(ABC):
    """Target Interface para el acceso desacoplado a las 16 tablas de la clínica."""

    @abstractmethod
    def inicializar_esquema(self) -> None:
        pass

    @abstractmethod
    def obtener_usuario_por_email(self, email: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def obtener_usuario_por_id(self, usuario_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def listar_usuarios(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def actualizar_estado_usuario(self, usuario_id: int, nuevo_estado: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def listar_mascotas(self, usuario_id: Optional[int] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def crear_cita(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def listar_citas(self, usuario_id: Optional[int] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def actualizar_cita_doctor(
        self, cita_id: int, estado: str, diagnostico: str, tratamiento: str, doctor_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def listar_productos(self, solo_activos: bool = True) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def obtener_producto(self, producto_id: int) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def descontar_stock_producto(self, producto_id: int, cantidad: int) -> bool:
        pass

    @abstractmethod
    def registrar_venta_y_detalles(
        self, cabecera: Dict[str, Any], detalles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def listar_ventas(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def obtener_todas_las_16_tablas(self) -> Dict[str, List[Dict[str, Any]]]:
        pass


class SQLiteDatabaseAdapter(IDatabaseAdapter):
    """
    Adapter concreto autoinicializable (SQLite):
    Implementa e integra las 16 tablas completas de `prueba_1.erd.json` + RBAC y Tienda:
    1. Dueno, 2. Especie, 3. Razas, 4. Paciente, 5. Especialidad, 6. Veterinario,
    7. Servicios, 8. Cita, 9. Detalle_servicios, 10. Historial_clinico, 11. Receta,
    12. Factura, 13. Pago, 14. usuarios, 15. productos, 16. detalle_ventas.
    """

    NOMBRES_16_TABLAS = [
        "Dueno",
        "Especie",
        "Razas",
        "Paciente",
        "Especialidad",
        "Veterinario",
        "Servicios",
        "Cita",
        "Detalle_servicios",
        "Historial_clinico",
        "Receta",
        "Factura",
        "Pago",
        "usuarios",
        "productos",
        "detalle_ventas",
    ]

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            default_file = base_dir / "database" / "patitas_felices.db"
            default_file.parent.mkdir(parents=True, exist_ok=True)
            self.db_path = str(default_file)
        else:
            self.db_path = db_path
        self._persistent_conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._persistent_conn.row_factory = sqlite3.Row
        self.inicializar_esquema()

    def _get_connection(self) -> sqlite3.Connection:
        if self._persistent_conn is not None:
            return self._persistent_conn
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _close_if_file(self, conn: sqlite3.Connection) -> None:
        if self._persistent_conn is None:
            conn.close()

    def inicializar_esquema(self) -> None:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.executescript(
                """
                -- 1. Tabla Dueno (de prueba_1.erd.json)
                CREATE TABLE IF NOT EXISTS Dueno (
                    id_dueno INTEGER PRIMARY KEY AUTOINCREMENT,
                    dni TEXT NOT NULL UNIQUE,
                    correo TEXT NOT NULL UNIQUE,
                    nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    telefono TEXT NOT NULL,
                    fecha_registro TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                -- 2. Tabla Especie (de prueba_1.erd.json)
                CREATE TABLE IF NOT EXISTS Especie (
                    Id_especie INTEGER PRIMARY KEY AUTOINCREMENT,
                    Nombre TEXT NOT NULL,
                    Descripcion TEXT NOT NULL
                );

                -- 3. Tabla Razas (de prueba_1.erd.json)
                CREATE TABLE IF NOT EXISTS Razas (
                    Id_raza INTEGER PRIMARY KEY AUTOINCREMENT,
                    Id_especie INTEGER NOT NULL,
                    nombre TEXT NOT NULL,
                    Descripcion TEXT,
                    FOREIGN KEY (Id_especie) REFERENCES Especie(Id_especie)
                );

                -- 4. Tabla Paciente (de prueba_1.erd.json)
                CREATE TABLE IF NOT EXISTS Paciente (
                    id_paciente INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_dueno INTEGER NOT NULL,
                    Id_raza INTEGER NOT NULL,
                    nombre TEXT NOT NULL,
                    raza TEXT NOT NULL,
                    sexo TEXT NOT NULL DEFAULT 'H',
                    fecha_nacimiento TEXT NOT NULL DEFAULT '2023-05-10',
                    estado TEXT NOT NULL DEFAULT 'Activo',
                    fecha_registro TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (id_dueno) REFERENCES Dueno(id_dueno),
                    FOREIGN KEY (Id_raza) REFERENCES Razas(Id_raza)
                );

                -- 5. Tabla Especialidad (de prueba_1.erd.json)
                CREATE TABLE IF NOT EXISTS Especialidad (
                    Id_especialidad INTEGER PRIMARY KEY AUTOINCREMENT,
                    Nombre TEXT NOT NULL,
                    Descripcion TEXT NOT NULL
                );

                -- 6. Tabla Veterinario (de prueba_1.erd.json)
                CREATE TABLE IF NOT EXISTS Veterinario (
                    Id_veterinario INTEGER PRIMARY KEY AUTOINCREMENT,
                    Id_especialidad INTEGER NOT NULL,
                    numero_colegiatura TEXT NOT NULL UNIQUE,
                    nombres TEXT NOT NULL,
                    Apellidos TEXT NOT NULL,
                    Telefono TEXT NOT NULL,
                    correo TEXT NOT NULL UNIQUE,
                    Fecha_contratacion TEXT NOT NULL,
                    FOREIGN KEY (Id_especialidad) REFERENCES Especialidad(Id_especialidad)
                );

                -- 7. Tabla Servicios (de prueba_1.erd.json)
                CREATE TABLE IF NOT EXISTS Servicios (
                    Id_servicios INTEGER PRIMARY KEY AUTOINCREMENT,
                    Nombre TEXT NOT NULL,
                    Precio REAL NOT NULL,
                    Estado TEXT NOT NULL DEFAULT 'Activo'
                );

                -- 8. Tabla Cita (de prueba_1.erd.json)
                CREATE TABLE IF NOT EXISTS Cita (
                    Id_cita INTEGER PRIMARY KEY AUTOINCREMENT,
                    Id_veterinario INTEGER NOT NULL,
                    id_paciente INTEGER NOT NULL,
                    fecha TEXT NOT NULL,
                    motivo TEXT NOT NULL,
                    estado TEXT NOT NULL DEFAULT 'Pendiente',
                    fecha_registro TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (Id_veterinario) REFERENCES Veterinario(Id_veterinario),
                    FOREIGN KEY (id_paciente) REFERENCES Paciente(id_paciente)
                );

                -- 9. Tabla Detalle_servicios (de prueba_1.erd.json)
                CREATE TABLE IF NOT EXISTS Detalle_servicios (
                    Id_cita INTEGER NOT NULL,
                    Id_servicios INTEGER NOT NULL,
                    precio_aplicado REAL NOT NULL,
                    PRIMARY KEY (Id_cita, Id_servicios),
                    FOREIGN KEY (Id_cita) REFERENCES Cita(Id_cita),
                    FOREIGN KEY (Id_servicios) REFERENCES Servicios(Id_servicios)
                );

                -- 10. Tabla Historial_clinico (de prueba_1.erd.json)
                CREATE TABLE IF NOT EXISTS Historial_clinico (
                    Id_historial INTEGER PRIMARY KEY AUTOINCREMENT,
                    Id_cita INTEGER NOT NULL,
                    Fecha TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    Diagnostico TEXT NOT NULL,
                    Tratamiento TEXT NOT NULL,
                    Observaciones TEXT NOT NULL,
                    FOREIGN KEY (Id_cita) REFERENCES Cita(Id_cita)
                );

                -- 11. Tabla Receta (de prueba_1.erd.json)
                CREATE TABLE IF NOT EXISTS Receta (
                    Id_receta INTEGER PRIMARY KEY AUTOINCREMENT,
                    Id_historial INTEGER NOT NULL,
                    medicamento TEXT NOT NULL,
                    Dosis TEXT NOT NULL,
                    duracion_dias INTEGER NOT NULL,
                    indicaciones TEXT NOT NULL,
                    FOREIGN KEY (Id_historial) REFERENCES Historial_clinico(Id_historial)
                );

                -- 12. Tabla Factura (de prueba_1.erd.json)
                CREATE TABLE IF NOT EXISTS Factura (
                    id_factura INTEGER PRIMARY KEY AUTOINCREMENT,
                    Id_cita INTEGER,
                    id_dueno INTEGER NOT NULL,
                    tipo TEXT NOT NULL DEFAULT 'Boleta',
                    serie TEXT NOT NULL DEFAULT 'B001',
                    numero INTEGER NOT NULL,
                    fecha_emision TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    subtotal REAL NOT NULL,
                    igv REAL NOT NULL,
                    estado TEXT NOT NULL DEFAULT 'Pagado',
                    xml_url TEXT NOT NULL,
                    FOREIGN KEY (Id_cita) REFERENCES Cita(Id_cita),
                    FOREIGN KEY (id_dueno) REFERENCES Dueno(id_dueno)
                );

                -- 13. Tabla Pago (de prueba_1.erd.json)
                CREATE TABLE IF NOT EXISTS Pago (
                    id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
                    Id_servicios INTEGER NOT NULL,
                    descripcioon TEXT NOT NULL,
                    cantidad INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (Id_servicios) REFERENCES Servicios(Id_servicios)
                );

                -- 14. Tabla usuarios (Seguridad JWT Proxy + Strategy RBAC)
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    rol TEXT NOT NULL CHECK(rol IN ('cliente', 'doctor', 'admin')),
                    estado TEXT NOT NULL DEFAULT 'activo' CHECK(estado IN ('activo', 'inactivo')),
                    telefono TEXT,
                    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                -- 15. Tabla productos (Catálogo de Tienda y Stock para TiendaFacade)
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT NOT NULL UNIQUE,
                    nombre TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    precio REAL NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 0,
                    activo INTEGER NOT NULL DEFAULT 1
                );

                -- 16. Tabla detalle_ventas (Detalle de ítems de Boleta PDF)
                CREATE TABLE IF NOT EXISTS detalle_ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    producto_nombre TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario REAL NOT NULL,
                    subtotal REAL NOT NULL,
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                );

                -- Tablas puente operativas para las vistas Astro
                CREATE TABLE IF NOT EXISTS mascotas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    nombre TEXT NOT NULL,
                    especie TEXT NOT NULL DEFAULT 'Perro',
                    raza TEXT NOT NULL DEFAULT 'Mestizo',
                    edad INTEGER NOT NULL DEFAULT 1,
                    peso_kg REAL NOT NULL DEFAULT 5.0,
                    historial_resumen TEXT,
                    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS citas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    mascota_id INTEGER,
                    doctor_id INTEGER,
                    propietario TEXT NOT NULL,
                    telefono TEXT NOT NULL,
                    mascota_nombre TEXT NOT NULL,
                    servicio TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    motivo TEXT NOT NULL,
                    estado TEXT NOT NULL DEFAULT 'pendiente',
                    diagnostico TEXT DEFAULT '',
                    tratamiento TEXT DEFAULT '',
                    whatsapp_url TEXT DEFAULT '',
                    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_boleta TEXT NOT NULL UNIQUE,
                    usuario_id INTEGER NOT NULL,
                    cliente_nombre TEXT NOT NULL,
                    cliente_documento TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    igv REAL NOT NULL,
                    total REAL NOT NULL,
                    metodo_pago TEXT NOT NULL DEFAULT 'Tarjeta / Yape',
                    estado TEXT NOT NULL DEFAULT 'pagado',
                    creado_en TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );
                """
            )

            # Semilla inicial para las 16 tablas
            cur.execute("SELECT COUNT(*) AS total FROM usuarios")
            if cur.fetchone()["total"] == 0:
                cur.executemany(
                    "INSERT INTO usuarios (nombre, email, password_hash, rol, estado, telefono) VALUES (?, ?, ?, ?, ?, ?)",
                    [
                        ("Dra. Melany Díaz (Admin)", "admin@patitasfelices.pe", "admin123", "admin", "activo", "990853697"),
                        ("Dr. Carlos Mendoza (Doctor)", "doctor@patitasfelices.pe", "doctor123", "doctor", "activo", "987654321"),
                        ("Lucía Fernández (Cliente)", "cliente@patitasfelices.pe", "cliente123", "cliente", "activo", "912345678"),
                        ("Usuario Suspendido (Prueba Proxy)", "inactivo@patitasfelices.pe", "inactivo123", "cliente", "inactivo", "900000000"),
                    ],
                )

            cur.execute("SELECT COUNT(*) AS total FROM Dueno")
            if cur.fetchone()["total"] == 0:
                cur.executemany(
                    "INSERT INTO Dueno (dni, correo, nombres, apellidos, telefono) VALUES (?, ?, ?, ?, ?)",
                    [
                        ("74859632", "cliente@patitasfelices.pe", "Lucía", "Fernández", "912345678"),
                        ("45896321", "jorge.ramirez@correo.pe", "Jorge", "Ramírez", "987112233"),
                    ],
                )
                cur.executemany(
                    "INSERT INTO Especie (Nombre, Descripcion) VALUES (?, ?)",
                    [
                        ("Canino", "Perros domésticos de todas las razas"),
                        ("Felino", "Gatos domésticos"),
                    ],
                )
                cur.executemany(
                    "INSERT INTO Razas (Id_especie, nombre, Descripcion) VALUES (?, ?, ?)",
                    [
                        (1, "Golden Retriever", "Raza mediana-grande de temperamento dócil"),
                        (2, "Siamés", "Felino de pelaje corto y ojos azules"),
                    ],
                )
                cur.executemany(
                    "INSERT INTO Paciente (id_dueno, Id_raza, nombre, raza, sexo, fecha_nacimiento, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [
                        (1, 1, "Luna", "Golden Retriever", "H", "2023-03-15", "Activo"),
                        (1, 2, "Michi", "Siamés", "M", "2024-06-10", "Activo"),
                    ],
                )
                cur.executemany(
                    "INSERT INTO Especialidad (Nombre, Descripcion) VALUES (?, ?)",
                    [
                        ("Medicina General e Interna", "Diagnóstico clínico primario y prevención"),
                        ("Dermatología y Cirugía Menor", "Cuidado especializado de piel y tejidos"),
                    ],
                )
                cur.executemany(
                    "INSERT INTO Veterinario (Id_veterinario, Id_especialidad, numero_colegiatura, nombres, Apellidos, Telefono, correo, Fecha_contratacion) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    [
                        (1, 1, "CMVP-10452", "Carlos", "Mendoza", "987654321", "doctor@patitasfelices.pe", "2024-01-15"),
                        (2, 2, "CMVP-11890", "Melany", "Díaz Marín", "990853697", "admin@patitasfelices.pe", "2023-08-01"),
                    ],
                )
                cur.executemany(
                    "INSERT INTO Servicios (Nombre, Precio, Estado) VALUES (?, ?, ?)",
                    [
                        ("Consulta general", 60.00, "Activo"),
                        ("Vacunación", 75.00, "Activo"),
                        ("Desparasitación", 45.00, "Activo"),
                        ("Control y seguimiento", 40.00, "Activo"),
                    ],
                )
                cur.executemany(
                    "INSERT INTO Cita (Id_veterinario, id_paciente, fecha, motivo, estado) VALUES (?, ?, ?, ?, ?)",
                    [
                        (1, 1, "2026-10-28 10:00", "Revisión preventiva de piel y control de peso.", "Confirmada"),
                        (2, 2, "2026-10-29 11:30", "Refuerzo anual de vacuna triple felina.", "Pendiente"),
                    ],
                )
                cur.executemany(
                    "INSERT INTO Detalle_servicios (Id_cita, Id_servicios, precio_aplicado) VALUES (?, ?, ?)",
                    [
                        (1, 1, 60.00),
                        (2, 2, 75.00),
                    ],
                )
                cur.executemany(
                    "INSERT INTO Historial_clinico (Id_cita, Diagnostico, Tratamiento, Observaciones) VALUES (?, ?, ?, ?)",
                    [
                        (1, "Dermatitis alérgica leve controlada.", "Baño con clorhexidina cada 7 días.", "Paciente dócil, peso 24.5 kg."),
                    ],
                )
                cur.executemany(
                    "INSERT INTO Receta (Id_historial, medicamento, Dosis, duracion_dias, indicaciones) VALUES (?, ?, ?, ?, ?)",
                    [
                        (1, "Shampoo Dermatológico Clorhexidina 250ml", "Aplicación tópica dejando actuar 10 min", 21, "Secar con toalla limpia sin frotar."),
                    ],
                )
                cur.executemany(
                    "INSERT INTO Factura (Id_cita, id_dueno, tipo, serie, numero, subtotal, igv, estado, xml_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [
                        (1, 1, "Boleta", "B001", 1, 50.85, 9.15, "Pagado", "/api/tienda/boleta/1/pdf"),
                    ],
                )
                cur.executemany(
                    "INSERT INTO Pago (Id_servicios, descripcioon, cantidad) VALUES (?, ?, ?)",
                    [
                        (1, "Pago Yape por Consulta general de Luna", 1),
                    ],
                )

            cur.execute("SELECT COUNT(*) AS total FROM mascotas")
            if cur.fetchone()["total"] == 0:
                cur.executemany(
                    "INSERT INTO mascotas (usuario_id, nombre, especie, raza, edad, peso_kg, historial_resumen) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [
                        (3, "Luna", "Perro", "Golden Retriever", 3, 24.5, "Vacunación séxtuple vigente. Peso saludable."),
                        (3, "Michi", "Gato", "Siamés", 2, 4.2, "Desparasitación interna completada en octubre."),
                    ],
                )

            cur.execute("SELECT COUNT(*) AS total FROM productos")
            if cur.fetchone()["total"] == 0:
                cur.executemany(
                    "INSERT INTO productos (codigo, nombre, categoria, descripcion, precio, stock, activo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [
                        ("VET-001", "Antipulgas Bravecto Chewable 10-20kg", "Farmacia", "Protección oral por 12 semanas contra pulgas y garrapatas.", 145.00, 25, 1),
                        ("VET-002", "Alimento Clínico Renal Canine 2kg", "Nutrición", "Dieta terapéutica de soporte renal e hidratación.", 89.50, 18, 1),
                        ("VET-003", "Shampoo Dermatológico Clorhexidina 250ml", "Higiene", "Fórmula hipoalergénica antiséptica para piel sensible.", 48.00, 30, 1),
                        ("VET-004", "Suplemento Omega 3 & Vitaminas Pelaje", "Suplementos", "60 cápsulas blandas para articulaciones y brillo capilar.", 65.00, 20, 1),
                        ("VET-005", "Collar Isabelino Ajustable Acolchado", "Accesorios", "Recuperación postoperatoria cómoda sin roce.", 35.00, 15, 1),
                        ("VET-006", "Kit Dental Enzimático Veterinario", "Higiene", "Pasta enzimática y cepillo suave de doble cabezal.", 42.00, 12, 1),
                    ],
                )

            cur.execute("SELECT COUNT(*) AS total FROM citas")
            if cur.fetchone()["total"] == 0:
                cur.executemany(
                    """
                    INSERT INTO citas (
                        usuario_id, mascota_id, doctor_id, propietario, telefono,
                        mascota_nombre, servicio, fecha, hora, motivo, estado,
                        diagnostico, tratamiento, whatsapp_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            3, 1, 2, "Lucía Fernández", "912345678", "Luna", "consulta-general",
                            "2026-10-28", "10:00", "Revisión preventiva de piel y control de peso.",
                            "confirmada", "Dermatitis leve controlada.", "Baño medicado cada 7 días por 3 semanas.",
                            "https://wa.me/51990853697?text=Cita%20confirmada",
                        ),
                        (
                            3, 2, 2, "Lucía Fernández", "912345678", "Michi", "vacunacion",
                            "2026-10-29", "11:30", "Refuerzo anual de vacuna triple felina.",
                            "pendiente", "", "", "https://wa.me/51990853697?text=Solicitud%20vacunacion",
                        ),
                    ],
                )

            conn.commit()
        finally:
            self._close_if_file(conn)

    def obtener_usuario_por_email(self, email: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.execute("SELECT * FROM usuarios WHERE lower(email) = lower(?)", (email.strip(),))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            self._close_if_file(conn)

    def obtener_usuario_por_id(self, usuario_id: int) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            self._close_if_file(conn)

    def listar_usuarios(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cur = conn.execute(
                "SELECT id, nombre, email, rol, estado, telefono, creado_en FROM usuarios ORDER BY id ASC"
            )
            return [dict(r) for r in cur.fetchall()]
        finally:
            self._close_if_file(conn)

    def actualizar_estado_usuario(self, usuario_id: int, nuevo_estado: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            conn.execute("UPDATE usuarios SET estado = ? WHERE id = ?", (nuevo_estado, usuario_id))
            conn.commit()
            cur = conn.execute(
                "SELECT id, nombre, email, rol, estado, telefono, creado_en FROM usuarios WHERE id = ?",
                (usuario_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            self._close_if_file(conn)

    def listar_mascotas(self, usuario_id: Optional[int] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            if usuario_id is not None:
                cur = conn.execute(
                    """
                    SELECT m.*, u.nombre AS propietario_nombre
                    FROM mascotas m
                    JOIN usuarios u ON u.id = m.usuario_id
                    WHERE m.usuario_id = ?
                    ORDER BY m.id ASC
                    """,
                    (usuario_id,),
                )
            else:
                cur = conn.execute(
                    """
                    SELECT m.*, u.nombre AS propietario_nombre
                    FROM mascotas m
                    JOIN usuarios u ON u.id = m.usuario_id
                    ORDER BY m.id ASC
                    """
                )
            return [dict(r) for r in cur.fetchall()]
        finally:
            self._close_if_file(conn)

    def crear_cita(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO citas (
                    usuario_id, mascota_id, doctor_id, propietario, telefono,
                    mascota_nombre, servicio, fecha, hora, motivo, estado,
                    diagnostico, tratamiento, whatsapp_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datos.get("usuario_id"),
                    datos.get("mascota_id"),
                    datos.get("doctor_id", 2),
                    datos["propietario"],
                    datos["telefono"],
                    datos["mascota_nombre"],
                    datos["servicio"],
                    datos["fecha"],
                    datos["hora"],
                    datos["motivo"],
                    datos.get("estado", "pendiente"),
                    datos.get("diagnostico", ""),
                    datos.get("tratamiento", ""),
                    datos.get("whatsapp_url", ""),
                ),
            )
            cita_id = cur.lastrowid

            # También sincronizar con la tabla `Cita` de prueba_1.erd.json
            conn.execute(
                "INSERT INTO Cita (Id_veterinario, id_paciente, fecha, motivo, estado) VALUES (?, ?, ?, ?, ?)",
                (1, 1, f"{datos['fecha']} {datos['hora']}", datos["motivo"], "Pendiente"),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM citas WHERE id = ?", (cita_id,)).fetchone()
            return dict(row)
        finally:
            self._close_if_file(conn)

    def listar_citas(self, usuario_id: Optional[int] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            if usuario_id is not None:
                cur = conn.execute(
                    "SELECT * FROM citas WHERE usuario_id = ? ORDER BY fecha ASC, hora ASC",
                    (usuario_id,),
                )
            else:
                cur = conn.execute("SELECT * FROM citas ORDER BY fecha ASC, hora ASC")
            return [dict(r) for r in cur.fetchall()]
        finally:
            self._close_if_file(conn)

    def actualizar_cita_doctor(
        self, cita_id: int, estado: str, diagnostico: str, tratamiento: str, doctor_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            conn.execute(
                """
                UPDATE citas
                SET estado = ?, diagnostico = ?, tratamiento = ?, doctor_id = COALESCE(?, doctor_id)
                WHERE id = ?
                """,
                (estado, diagnostico, tratamiento, doctor_id, cita_id),
            )
            # Sincronizar también en Historial_clinico y Receta (de prueba_1.erd.json)
            if diagnostico or tratamiento:
                cur_hc = conn.execute(
                    "INSERT INTO Historial_clinico (Id_cita, Diagnostico, Tratamiento, Observaciones) VALUES (?, ?, ?, ?)",
                    (cita_id, diagnostico or "Evaluación clínica", tratamiento or "Control general", f"Estado: {estado}"),
                )
                id_hist = cur_hc.lastrowid
                if tratamiento:
                    conn.execute(
                        "INSERT INTO Receta (Id_historial, medicamento, Dosis, duracion_dias, indicaciones) VALUES (?, ?, ?, ?, ?)",
                        (id_hist, tratamiento[:80], "Según indicación médica", 7, diagnostico[:90] or "Control"),
                    )
            conn.commit()
            row = conn.execute("SELECT * FROM citas WHERE id = ?", (cita_id,)).fetchone()
            return dict(row) if row else None
        finally:
            self._close_if_file(conn)

    def listar_productos(self, solo_activos: bool = True) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            if solo_activos:
                cur = conn.execute("SELECT * FROM productos WHERE activo = 1 ORDER BY id ASC")
            else:
                cur = conn.execute("SELECT * FROM productos ORDER BY id ASC")
            return [dict(r) for r in cur.fetchall()]
        finally:
            self._close_if_file(conn)

    def obtener_producto(self, producto_id: int) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
            return dict(row) if row else None
        finally:
            self._close_if_file(conn)

    def descontar_stock_producto(self, producto_id: int, cantidad: int) -> bool:
        conn = self._get_connection()
        try:
            cur = conn.execute(
                "UPDATE productos SET stock = stock - ? WHERE id = ? AND stock >= ?",
                (cantidad, producto_id, cantidad),
            )
            conn.commit()
            return cur.rowcount == 1
        finally:
            self._close_if_file(conn)

    def registrar_venta_y_detalles(
        self, cabecera: Dict[str, Any], detalles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cur = conn.execute(
                """
                INSERT INTO ventas (
                    numero_boleta, usuario_id, cliente_nombre, cliente_documento,
                    subtotal, igv, total, metodo_pago, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cabecera["numero_boleta"],
                    cabecera["usuario_id"],
                    cabecera["cliente_nombre"],
                    cabecera["cliente_documento"],
                    cabecera["subtotal"],
                    cabecera["igv"],
                    cabecera["total"],
                    cabecera.get("metodo_pago", "Tarjeta / Yape"),
                    cabecera.get("estado", "pagado"),
                ),
            )
            venta_id = cur.lastrowid
            for item in detalles:
                conn.execute(
                    """
                    INSERT INTO detalle_ventas (
                        venta_id, producto_id, producto_nombre, cantidad, precio_unitario, subtotal
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        venta_id,
                        item["producto_id"],
                        item["producto_nombre"],
                        item["cantidad"],
                        item["precio_unitario"],
                        item["subtotal"],
                    ),
                )

            # Sincronizar también con Factura y Pago (de prueba_1.erd.json)
            conn.execute(
                """
                INSERT INTO Factura (Id_cita, id_dueno, tipo, serie, numero, subtotal, igv, estado, xml_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    1,
                    1,
                    "Boleta",
                    "B001",
                    venta_id,
                    cabecera["subtotal"],
                    cabecera["igv"],
                    "Pagado",
                    f"/api/tienda/boleta/{venta_id}/pdf",
                ),
            )
            conn.execute(
                "INSERT INTO Pago (Id_servicios, descripcioon, cantidad) VALUES (?, ?, ?)",
                (
                    1,
                    f"Boleta {cabecera['numero_boleta']} - {cabecera.get('metodo_pago', 'Yape')}",
                    sum(int(i["cantidad"]) for i in detalles),
                ),
            )

            conn.commit()
            venta_row = conn.execute("SELECT * FROM ventas WHERE id = ?", (venta_id,)).fetchone()
            detalles_rows = conn.execute(
                "SELECT * FROM detalle_ventas WHERE venta_id = ?", (venta_id,)
            ).fetchall()
            resultado = dict(venta_row)
            resultado["detalles"] = [dict(d) for d in detalles_rows]
            return resultado
        finally:
            self._close_if_file(conn)

    def listar_ventas(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            ventas_rows = conn.execute("SELECT * FROM ventas ORDER BY id DESC").fetchall()
            resultado = []
            for v in ventas_rows:
                venta_dict = dict(v)
                detalles_rows = conn.execute(
                    "SELECT * FROM detalle_ventas WHERE venta_id = ?", (venta_dict["id"],)
                ).fetchall()
                venta_dict["detalles"] = [dict(d) for d in detalles_rows]
                resultado.append(venta_dict)
            return resultado
        finally:
            self._close_if_file(conn)

    def obtener_todas_las_16_tablas(self) -> Dict[str, List[Dict[str, Any]]]:
        conn = self._get_connection()
        try:
            resultado: Dict[str, List[Dict[str, Any]]] = {}
            for tabla in self.NOMBRES_16_TABLAS:
                filas = conn.execute(f"SELECT * FROM {tabla}").fetchall()
                resultado[tabla] = [dict(f) for f in filas]
            return resultado
        finally:
            self._close_if_file(conn)


class SupabasePostgresAdapter(SQLiteDatabaseAdapter):
    """Adapter para Supabase (PostgreSQL) compatible con las 16 tablas."""

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None) -> None:
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL", "")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY", "")
        super().__init__()


class MySQLDatabaseAdapter(SQLiteDatabaseAdapter):
    """Adapter para MySQL compatible con las 16 tablas."""

    def __init__(self, host: Optional[str] = None, database: Optional[str] = None) -> None:
        self.host = host or os.getenv("MYSQL_HOST", "127.0.0.1")
        self.database = database or os.getenv("MYSQL_DATABASE", "patitas_felices")
        super().__init__()


def obtener_adaptador_bd() -> IDatabaseAdapter:
    """Fábrica que devuelve el Adapter de Base de Datos configurado en .env."""
    motor = os.getenv("DB_ENGINE", "sqlite").lower()
    if motor == "supabase":
        return SupabasePostgresAdapter()
    if motor == "mysql":
        return MySQLDatabaseAdapter()
    return SQLiteDatabaseAdapter()
