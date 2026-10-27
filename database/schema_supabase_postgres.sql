-- =============================================================================
-- CLÍNICA VETERINARIA PATITAS FELICES - ESQUEMA SUPABASE (POSTGRESQL)
-- Tablas clave: usuarios, mascotas, citas, productos, ventas, detalle_ventas
-- =============================================================================

-- 1. Tabla: usuarios (con rol RBAC y estado activo/inactivo para el Patrón Proxy)
CREATE TABLE IF NOT EXISTS public.usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'cliente' CHECK (rol IN ('cliente', 'doctor', 'admin')),
    estado VARCHAR(20) NOT NULL DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo')),
    telefono VARCHAR(20),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Tabla: mascotas
CREATE TABLE IF NOT EXISTS public.mascotas (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL REFERENCES public.usuarios(id) ON DELETE CASCADE,
    nombre VARCHAR(60) NOT NULL,
    especie VARCHAR(40) NOT NULL DEFAULT 'Perro',
    raza VARCHAR(60) NOT NULL DEFAULT 'Mestizo',
    edad INT NOT NULL DEFAULT 1,
    peso_kg NUMERIC(5,2) NOT NULL DEFAULT 5.00,
    historial_resumen VARCHAR(500),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Tabla: citas
CREATE TABLE IF NOT EXISTS public.citas (
    id SERIAL PRIMARY KEY,
    usuario_id INT REFERENCES public.usuarios(id) ON DELETE SET NULL,
    mascota_id INT REFERENCES public.mascotas(id) ON DELETE SET NULL,
    doctor_id INT REFERENCES public.usuarios(id) ON DELETE SET NULL,
    propietario VARCHAR(80) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    mascota_nombre VARCHAR(60) NOT NULL,
    servicio VARCHAR(50) NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    motivo VARCHAR(1000) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'confirmada', 'atendida', 'cancelada')),
    diagnostico VARCHAR(500),
    tratamiento VARCHAR(500),
    whatsapp_url VARCHAR(600),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Tabla: productos
CREATE TABLE IF NOT EXISTS public.productos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(120) NOT NULL,
    categoria VARCHAR(60) NOT NULL,
    descripcion VARCHAR(300) NOT NULL,
    precio NUMERIC(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 5. Tabla: ventas
CREATE TABLE IF NOT EXISTS public.ventas (
    id SERIAL PRIMARY KEY,
    numero_boleta VARCHAR(30) NOT NULL UNIQUE,
    usuario_id INT NOT NULL REFERENCES public.usuarios(id),
    cliente_nombre VARCHAR(100) NOT NULL,
    cliente_documento VARCHAR(20) NOT NULL,
    subtotal NUMERIC(10,2) NOT NULL,
    igv NUMERIC(10,2) NOT NULL,
    total NUMERIC(10,2) NOT NULL,
    metodo_pago VARCHAR(40) NOT NULL DEFAULT 'Tarjeta / Yape',
    estado VARCHAR(30) NOT NULL DEFAULT 'pagado',
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Tabla: detalle_ventas
CREATE TABLE IF NOT EXISTS public.detalle_ventas (
    id SERIAL PRIMARY KEY,
    venta_id INT NOT NULL REFERENCES public.ventas(id) ON DELETE CASCADE,
    producto_id INT NOT NULL REFERENCES public.productos(id),
    producto_nombre VARCHAR(120) NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL,
    subtotal NUMERIC(10,2) NOT NULL
);

-- =============================================================================
-- DATOS SEMILLA (SEED DATA)
-- =============================================================================
INSERT INTO public.usuarios (nombre, email, password_hash, rol, estado, telefono) VALUES
('Dra. Melany Díaz (Admin)', 'admin@patitasfelices.pe', 'admin123', 'admin', 'activo', '990853697'),
('Dr. Carlos Mendoza (Veterinario)', 'doctor@patitasfelices.pe', 'doctor123', 'doctor', 'activo', '987654321'),
('Lucía Fernández (Cliente)', 'cliente@patitasfelices.pe', 'cliente123', 'cliente', 'activo', '912345678'),
('Usuario Suspendido (Prueba Proxy)', 'inactivo@patitasfelices.pe', 'inactivo123', 'cliente', 'inactivo', '900000000')
ON CONFLICT (email) DO NOTHING;

INSERT INTO public.productos (codigo, nombre, categoria, descripcion, precio, stock, activo) VALUES
('VET-001', 'Antipulgas Bravecto Chewable 10-20kg', 'Farmacia', 'Protección por 12 semanas contra pulgas y garrapatas.', 145.00, 25, TRUE),
('VET-002', 'Alimento Clínico Renal Canine 2kg', 'Nutrición', 'Fórmula veterinaria de soporte renal e hidratación.', 89.50, 18, TRUE),
('VET-003', 'Shampoo Dermatológico Clorhexidina 250ml', 'Higiene', 'Cuidado antiséptico hipoalergénico para piel sensible.', 48.00, 30, TRUE),
('VET-004', 'Suplemento Omega 3 & Vitaminas Pelaje', 'Suplementos', 'Cápsulas blandas para fortalecer articulaciones y pelaje.', 65.00, 20, TRUE),
('VET-005', 'Collar Isabelino Ajustable acolchado', 'Accesorios', 'Recuperación postoperatoria cómoda y segura.', 35.00, 15, TRUE),
('VET-006', 'Kit Dental Enzimático Veterinario', 'Higiene', 'Pasta enzimática y cepillo de doble cabezal.', 42.00, 12, TRUE)
ON CONFLICT (codigo) DO NOTHING;
