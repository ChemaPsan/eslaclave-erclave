from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleSeed:
    code: str
    name: str
    description: str
    status: str
    owner_service: str
    public_feature: bool
    sort_order: int


MVP_MODULE_SEEDS: tuple[ModuleSeed, ...] = (
    ModuleSeed(
        code="admin",
        name="Administracion",
        description="Tenants, usuarios, roles, permisos, configuracion y modulos activos.",
        status="active",
        owner_service="admin-service",
        public_feature=False,
        sort_order=10,
    ),
    ModuleSeed(
        code="production",
        name="Produccion",
        description="Productos, servicios, recetas, recursos productivos y ordenes de produccion.",
        status="active",
        owner_service="production-service",
        public_feature=True,
        sort_order=20,
    ),
    ModuleSeed(
        code="hr",
        name="Recursos Humanos",
        description="Areas, puestos, capacidad nominal, costo hora y elegibilidad productiva.",
        status="active",
        owner_service="hr-service",
        public_feature=True,
        sort_order=25,
    ),
    ModuleSeed(
        code="inventory",
        name="Almacenes e inventarios",
        description="Almacenes, articulos, existencias, movimientos, lotes, reservas y kardex.",
        status="active",
        owner_service="inventory-service",
        public_feature=True,
        sort_order=30,
    ),
    ModuleSeed(
        code="sales",
        name="Ventas",
        description="Clientes, cotizaciones, pedidos, entregas y devoluciones comerciales.",
        status="active",
        owner_service="sales-service",
        public_feature=True,
        sort_order=40,
    ),
    ModuleSeed(
        code="billing",
        name="Billing",
        description="Planes, suscripciones, pagos, activaciones manuales y estado comercial SaaS.",
        status="active",
        owner_service="billing-service",
        public_feature=False,
        sort_order=50,
    ),
    ModuleSeed(
        code="provisioning",
        name="Provisioning",
        description="Alta idempotente de tenants, admin inicial, modulos contratados y configuracion base.",
        status="active",
        owner_service="provisioning-service",
        public_feature=False,
        sort_order=60,
    ),
    ModuleSeed(
        code="integrations",
        name="Integraciones",
        description="Clientes API, scopes, credenciales, cuotas y uso de integraciones externas.",
        status="active",
        owner_service="integration-service",
        public_feature=True,
        sort_order=70,
    ),
)

MODULE_CODES: frozenset[str] = frozenset(module.code for module in MVP_MODULE_SEEDS)


def get_module_seed(code: str) -> ModuleSeed | None:
    normalized_code = code.strip().lower()
    for module in MVP_MODULE_SEEDS:
        if module.code == normalized_code:
            return module
    return None
