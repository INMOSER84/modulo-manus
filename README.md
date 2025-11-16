# Proyecto Odoo 17 - Módulo Inmoser Service Order (Versión Final)

Este proyecto contiene la configuración y el módulo personalizado `inmoser_service_order` para Odoo 17 Community Edition, basado en la arquitectura proporcionada y con las siguientes mejoras:

-   **Generación de Código QR** para equipos.
-   **Funcionalidad de Facturación** de refacciones desde la Orden de Servicio.
-   **Integración de Módulos OCA de Contabilidad México** (`l10n-mexico`).

## Requisitos Previos

-   Docker
-   Docker Compose

## Estructura del Proyecto

```
/odoo_project
├── config/
│   └── odoo.conf
├── custom_addons/
│   └── inmoser_service_order/ (Módulo personalizado)
├── oca_addons/
│   ├── field-service/ (Módulos OCA de Field Service)
│   ├── partner-contact/ (Módulos OCA de Contactos)
│   └── l10n-mexico/ (Módulos OCA de Contabilidad México)
├── requirements.txt (Dependencias Python: qrcode)
├── docker-compose.yml
└── README.md
```

## Instrucciones de Instalación

1.  **Clonar el proyecto (o descomprimir el archivo .zip):**

    ```bash
    cd odoo_project
    ```

2.  **Revisar la configuración:**

    -   **`docker-compose.yml`**: Se ha modificado para instalar automáticamente la librería `qrcode` (necesaria para la generación de QR) al iniciar el contenedor de Odoo.
    -   **`requirements.txt`**: Contiene la dependencia `qrcode`.
    -   **`config/odoo.conf`**: Contiene la configuración de Odoo. La contraseña de administrador es `admin`.

3.  **Levantar los contenedores de Docker:**

    Desde el directorio raíz del proyecto (`/odoo_project`), ejecute:

    ```bash
    docker-compose up -d
    ```
    *Nota: La primera vez, Docker descargará las imágenes y el contenedor de Odoo instalará automáticamente la librería `qrcode`.*

4.  **Acceder a Odoo:**

    Abra su navegador y vaya a `http://localhost:8069`.

5.  **Crear la base de datos e instalar módulos:**

    -   Cree una nueva base de datos desde la interfaz de Odoo.
    -   **Importante:** Para la localización mexicana, asegúrese de seleccionar **México** como país en la configuración de la compañía durante la creación de la base de datos o en la configuración de la compañía después.
    -   Una vez creada la base de datos, inicie sesión.
    -   Vaya al menú **"Aplicaciones"**.
    -   Haga clic en **"Actualizar lista de aplicaciones"**.
    -   Busque e instale los módulos necesarios:
        -   **`inmoser_service_order`** (Módulo personalizado)
        -   **`l10n_mx_edi`** (Módulo base de Contabilidad Electrónica Mexicana de Odoo/OCA)
        -   Otros módulos de `l10n-mexico` que considere necesarios para su operación (ej. `l10n_mx_edi_40` para CFDI 4.0).

## Configuración del Módulo

Una vez instalado el módulo, deberá configurar lo siguiente:

1.  **Grupos de Seguridad:** Asigne los usuarios a los grupos de seguridad correspondientes (`Inmoser / Call Center`, `Inmoser / Técnico`, etc.).
2.  **Tipos de Servicio:** Vaya a `Servicio Inmoser > Configuración > Tipos de Servicio`.
3.  **Técnicos:** Edite los registros de los empleados en el módulo de **Recursos Humanos** y marque la casilla **"Es Técnico"**.
4.  **Clientes de Servicio:** Marque la casilla **"Es Cliente de Servicios"** en el contacto para generar la secuencia de cliente y habilitar la gestión de equipos.

## Mejoras Implementadas

| Característica | Implementación |
| :--- | :--- |
| **Generación de QR** | Implementada en `inmoser.service.equipment` usando la librería `qrcode`. El QR codifica la secuencia del cliente y del equipo. |
| **Generación de Factura** | Implementada la acción `action_create_invoice` en `inmoser.service.order` para crear una factura de cliente (`account.move`) con las líneas de refacciones utilizadas. |
| **Contabilidad México** | Se ha incluido el repositorio `OCA/l10n-mexico` en el directorio `oca_addons` para permitir la instalación de los módulos de localización mexicana. |
| **Dependencias** | Se ha configurado `docker-compose.yml` y `requirements.txt` para asegurar la instalación de la dependencia Python `qrcode`. |
