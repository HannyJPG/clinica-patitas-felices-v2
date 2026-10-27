"""Exportación de los 4 Patrones de Diseño GoF implementados en Python."""

from .adapter import (
    IDatabaseAdapter,
    IWhatsAppNotificationAdapter,
    MySQLDatabaseAdapter,
    SQLiteDatabaseAdapter,
    SupabasePostgresAdapter,
    WhatsAppAdapter,
    obtener_adaptador_bd,
)
from .facade import (
    ErrorProcesoVenta,
    SubsistemaCRMTransacciones,
    SubsistemaGeneradorPDF,
    SubsistemaInventario,
    TiendaFacade,
)
from .proxy import (
    AuthSessionProxy,
    ErrorSeguridadProxy,
    ISecureController,
    RealClinicController,
    generar_token_jwt,
    verificar_token_jwt,
)
from .strategy import (
    AdminRoleStrategy,
    ClientRoleStrategy,
    DoctorRoleStrategy,
    RBACContext,
    RoleAuthorizationStrategy,
)

__all__ = [
    "IDatabaseAdapter",
    "IWhatsAppNotificationAdapter",
    "SQLiteDatabaseAdapter",
    "SupabasePostgresAdapter",
    "MySQLDatabaseAdapter",
    "WhatsAppAdapter",
    "obtener_adaptador_bd",
    "RoleAuthorizationStrategy",
    "ClientRoleStrategy",
    "DoctorRoleStrategy",
    "AdminRoleStrategy",
    "RBACContext",
    "ISecureController",
    "RealClinicController",
    "AuthSessionProxy",
    "ErrorSeguridadProxy",
    "generar_token_jwt",
    "verificar_token_jwt",
    "SubsistemaInventario",
    "SubsistemaCRMTransacciones",
    "SubsistemaGeneradorPDF",
    "TiendaFacade",
    "ErrorProcesoVenta",
]
