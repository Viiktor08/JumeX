# Jumex

**Jumex** es una plataforma web para el análisis inteligente de vulnerabilidades en componentes de software, basada en **SBOM (Software Bill of Materials)** y potenciada con **Inteligencia Artificial**. Permite a los usuarios evaluar la seguridad de sus proyectos cruzando datos con bases como **CVE/NVD**, priorizando según criterios personalizados.

## Características principales

- Subida de proyectos con SBOM para análisis automático.
- Evaluación mediante IA basada en criterios definidos por el usuario.
- Integración con bases de datos de vulnerabilidades (CVE/NVD).
- Interfaz web intuitiva para visualización de resultados.
- Arquitectura de microservicios con Docker Compose.

## Tecnologías utilizadas

- Python + Flask
- MariaDB + SQLAlchemy
- Flask-Praetorian (autenticación y roles)
- Google Generative AI (para análisis con IA)
- Docker y Docker Compose

## Estructura del proyecto

```text
JumeX/
├── docker-compose.mac.yaml         # Versión para macOS con procesador M1/M2/M3
├── docker-compose.windows.yaml     # Versión para sistemas Windows (x86_64)
└── App/
    ├── api/       # Microservicio de gestión de datos y seguridad
    ├── chat/      # Microservicio de IA para análisis de SBOM
    └── web/       # Frontend Flask con la interfaz de usuario
```

## Instalación y ejecución

### Requisitos

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Iniciar el proyecto

**Para sistemas macOS con chip M1/M2/M3:**

```bash
docker compose -f docker-compose.mac.yaml up --build
```

**Para sistemas Windows o procesadores x86_64:**

```bash
docker compose -f docker-compose.windows.yaml up --build
```

### Servicios disponibles

| Servicio           | URL                    |
|--------------------|------------------------|
| Interfaz Web       | http://localhost:5010  |
| phpMyAdmin         | http://localhost:8080  |

## Archivos SBOM de prueba

En la ruta:

App/web/uploads/


se incluyen varios archivos JSON de ejemplo que representan **SBOMs de prueba**. Puedes utilizarlos para comprobar el funcionamiento de la plataforma sin necesidad de generar tus propios ficheros.

> Estos ficheros están preparados para integrarse directamente en el flujo de análisis de la aplicación.

## Credenciales de prueba

Para facilitar la evaluación, se incluye un usuario administrador de prueba que se crea automáticamente al iniciar el sistema:

- Correo electrónico: admin@example.es
- Contraseña: admin

Esta cuenta es segura ya que la aplicación se ejecuta en entorno local, sin exposición a internet por defecto.

## Cómo detener y desmontar los contenedores

**En macOS**

```bash
docker compose -f docker-compose.mac.yaml down --volumes --remove-orphans
```

**En Windows**

```bash
docker compose -f docker-compose.windows.yaml down --volumes --remove-orphans
```

## Estado actual

- [x] Arquitectura de microservicios operativa
- [x] Análisis de SBOM con IA funcional
- [x] Comunicación entre microservicios asegurada
- [ ] Despliegue en la nube

## Licencia

Este proyecto se desarrolla en el marco del curso de **Ingeniería del Software Seguro**.

Pull requests y sugerencias son bienvenidas.
