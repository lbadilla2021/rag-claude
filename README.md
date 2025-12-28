# Apex AI - Sistema RAG con Agentes Inteligentes

Sistema completo de chat similar a ChatGPT que conecta con un backend RAG (Retrieval-Augmented Generation) con múltiples agentes especializados y base de datos vectorial.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## 🎯 Características Principales

### Frontend (Similar a ChatGPT)
- ✨ **Interfaz moderna** estilo ChatGPT con tema oscuro
- 💬 **Chat interactivo** con historial de conversaciones
- 🤖 **Selector de agentes** especializados
- 📚 **Visualización de fuentes** consultadas por RAG
- 🎨 **Diseño responsive** para móvil y desktop
- ⚡ **Tiempo real** con indicadores de carga

### Gestor Documental (Nuevo)
- 📁 **Gestión completa** de documentos (PDF, DOCX, PPTX, TXT)
- 🏷️ **Metadatos ricos** (categoría, propietario, versión, tags, etc.)
- 📤 **Subida masiva** con drag & drop
- ✏️ **Edición de metadatos** en cualquier momento
- 🗑️ **Eliminación** de documentos y embeddings
- 🔍 **Búsqueda y filtros** avanzados
- 📊 **Vista de cuadrícula y lista**
- 🔄 **Integración directa** con base vectorial

### Backend RAG
- 🧠 **5 Agentes especializados** con diferentes expertise
- 🔍 **Búsqueda semántica** en base de datos vectorial
- 📄 **Procesamiento de documentos** (PDF, DOCX, TXT, PPTX)
- 💾 **ChromaDB** como base vectorial (configurable)
- 🔄 **Memoria conversacional** para contexto
- 🎯 **Sistema de reranking** de documentos
- 📊 **API RESTful** completa con FastAPI
- 🗂️ **API de gestión documental** completa

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (HTML/CSS/JS)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Chat UI      │  │ Selector de  │  │ Historial    │     │
│  │ (ChatGPT-    │  │ Agentes      │  │ Conversación │     │
│  │  style)      │  │              │  │              │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         └────────────┬────────────────────────┘            │
└───────────────────────┼─────────────────────────────────────┘
                        │ HTTP/REST API
┌───────────────────────┼─────────────────────────────────────┐
│                       │   BACKEND (FastAPI)                 │
│  ┌────────────────────▼──────────────────────────┐         │
│  │         API Endpoints & Routing               │         │
│  └────────────────────┬──────────────────────────┘         │
│                       │                                      │
│  ┌────────────────────▼──────────────────────────┐         │
│  │     Gestor de Agentes IA (Multi-Agent)        │         │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌────┐ │         │
│  │  │General││  HR  ││Legal ││Tech ││Train│ │         │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └────┘ │         │
│  └────────────────────┬──────────────────────────┘         │
│                       │                                      │
│  ┌────────────────────▼──────────────────────────┐         │
│  │          Sistema RAG (LangChain)              │         │
│  │  • Document Loaders                           │         │
│  │  • Text Splitters                             │         │
│  │  • Embeddings (OpenAI/Local)                  │         │
│  │  • Retrieval Chain                            │         │
│  │  • Conversational Memory                      │         │
│  └────────────────────┬──────────────────────────┘         │
│                       │                                      │
│  ┌────────────────────▼──────────────────────────┐         │
│  │      Base de Datos Vectorial (ChromaDB)       │         │
│  │  • Embeddings almacenados                     │         │
│  │  • Búsqueda por similitud                     │         │
│  │  • Metadata de documentos                     │         │
│  └───────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Requisitos Previos

- **Python 3.11+**
- **Node.js** (opcional, para desarrollo)
- **Docker & Docker Compose** (para deployment)
- **OpenAI API Key** (para funcionalidad completa)

## 🚀 Instalación y Configuración

### Opción 1: Instalación Local

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/apex-ai.git
cd apex-ai

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env y agregar tu OPENAI_API_KEY

# 5. Iniciar backend
python backend.py
# El backend estará disponible en http://localhost:8000

# 6. Servir frontend (en otra terminal)
# Opción A: Usando Python
python -m http.server 8080

# Opción B: Usando Node.js
npx http-server -p 8080

# La aplicación estará disponible en http://localhost:8080
```

### Opción 2: Usando Docker Compose (Recomendado)

```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env y agregar tu OPENAI_API_KEY

# 2. Construir y levantar servicios
docker-compose up -d

# 3. Verificar que los servicios estén corriendo
docker-compose ps

# Acceder a:
# - Frontend: http://localhost:8080
# - Backend API: http://localhost:8000
# - Documentación API: http://localhost:8000/docs
```

## 📖 Uso del Sistema

### Interfaz de Usuario

1. **Iniciar conversación**: Haz clic en "Nueva conversación"
2. **Seleccionar agente**: Elige el agente especializado según tu consulta
3. **Hacer consulta**: Escribe tu pregunta y presiona Enter o clic en enviar
4. **Revisar fuentes**: Las respuestas incluyen las fuentes consultadas en la base de conocimiento

### Agentes Disponibles

| Agente | Especialidad | Uso Recomendado |
|--------|--------------|-----------------|
| **General Assistant** | Consultas generales | Preguntas variadas, asistencia general |
| **HR Specialist** | RRHH y legislación laboral | Ley Karin, contratos, normativas SENCE |
| **Legal Compliance** | Cumplimiento legal | Normativas, auditorías, compliance |
| **Technical Support** | Soporte técnico | Desarrollo, arquitectura, sistemas |
| **Training Expert** | Capacitación | Diseño instruccional, metodologías, LMS |

### API Endpoints

#### Consultar RAG
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Cuáles son los requisitos de la Ley Karin?",
    "agent": "hr",
    "max_sources": 3
  }'
```

#### Subir Documento
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@documento.pdf" \
  -F "category=legal"
```

#### Obtener Agentes
```bash
curl http://localhost:8000/api/agents
```

#### Estadísticas del Sistema
```bash
curl http://localhost:8000/api/stats
```

## 📁 Estructura del Proyecto

```
apex-ai/
├── index.html              # Interfaz principal
├── styles.css              # Estilos del frontend
├── app.js                  # Lógica del frontend
├── backend.py              # API FastAPI con RAG
├── requirements.txt        # Dependencias Python
├── .env.example           # Configuración de ejemplo
├── Dockerfile             # Imagen Docker del backend
├── docker-compose.yml     # Orquestación de servicios
├── nginx.conf             # Configuración Nginx
├── README.md              # Esta documentación
├── chroma_db/             # Base de datos vectorial (generado)
├── uploads/               # Documentos subidos (generado)
└── logs/                  # Logs del sistema (generado)
```

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# OpenAI
OPENAI_API_KEY=sk-...                    # API key de OpenAI

# Modelo
DEFAULT_MODEL=gpt-4                      # Modelo a utilizar
DEFAULT_TEMPERATURE=0.7                  # Temperatura (0-1)

# Base de datos vectorial
VECTOR_DB_TYPE=chroma                    # chroma, pinecone, weaviate
VECTOR_DB_PATH=./chroma_db              # Ruta local
CHUNK_SIZE=1000                          # Tamaño de chunks
CHUNK_OVERLAP=200                        # Solapamiento

# Servidor
API_HOST=0.0.0.0
API_PORT=8000
```

### Usar Base de Datos Vectorial Alternativa

#### Pinecone
```python
# Instalar: pip install pinecone-client
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=tu-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
```

#### Weaviate
```python
# Instalar: pip install weaviate-client
VECTOR_DB_TYPE=weaviate
WEAVIATE_URL=http://localhost:8080
```

#### Qdrant
```python
# Instalar: pip install qdrant-client
VECTOR_DB_TYPE=qdrant
QDRANT_URL=http://localhost:6333
```

### Usar Embeddings Locales

```python
# En lugar de OpenAI, usar modelo local
# Instalar: pip install sentence-transformers

from langchain.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
```

## 🎯 Casos de Uso

### 1. Gestión Documental
```javascript
// Acceder al gestor
window.location.href = 'document-manager.html';

// Subir documentos con metadatos completos
- Arrastrar archivos PDF, DOCX, PPTX
- Completar categoría, propietario, versión
- Agregar tags y descripción
- Marcar si debe indexarse en RAG
```

### 2. Consultoría de RRHH
```javascript
// Seleccionar agente HR
agentSelector.value = 'hr';

// Consultar sobre Ley Karin
messageInput.value = '¿Cuáles son las obligaciones del empleador según la Ley Karin?';
```

### 2. Capacitación Técnica
```javascript
// Seleccionar agente Training
agentSelector.value = 'training';

// Consultar sobre diseño de cursos
messageInput.value = 'Dame una estructura para un curso de seguridad laboral de 20 horas';
```

### 3. Consulta Legal
```javascript
// Seleccionar agente Legal
agentSelector.value = 'legal';

// Consultar normativas
messageInput.value = 'Resumen de normativas para protección de datos personales en Chile';
```

## 📊 Monitoreo y Logs

### Ver logs en tiempo real
```bash
# Docker Compose
docker-compose logs -f backend

# Local
tail -f logs/apex_ai.log
```

### Estadísticas del sistema
```bash
curl http://localhost:8000/api/stats
```

## 🔐 Seguridad

- ✅ CORS configurado para dominios específicos
- ✅ Validación de tipos de archivo en uploads
- ✅ Límites de tamaño para archivos
- ✅ Headers de seguridad en Nginx
- ✅ API keys en variables de entorno
- ⚠️ **Importante**: En producción, usar HTTPS y autenticación

## 🚀 Deployment en Producción

### 1. Configurar dominio y SSL
```nginx
# Agregar a nginx.conf
server {
    listen 443 ssl http2;
    server_name tu-dominio.com;
    
    ssl_certificate /etc/ssl/certs/tu-cert.crt;
    ssl_certificate_key /etc/ssl/private/tu-key.key;
    
    # ... resto de configuración
}
```

### 2. Usar servicio de base vectorial en la nube
```bash
# Pinecone (recomendado para producción)
PINECONE_API_KEY=tu-api-key-produccion
PINECONE_ENVIRONMENT=gcp-starter
```

### 3. Configurar reverse proxy con Traefik
```yaml
# docker-compose.production.yml
services:
  traefik:
    image: traefik:v2.10
    command:
      - --providers.docker
      - --entrypoints.websecure.address=:443
      - --certificatesresolvers.letsencrypt.acme.tlschallenge=true
    # ... configuración adicional
```

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Roadmap

- [ ] Autenticación de usuarios
- [ ] Almacenamiento de conversaciones en base de datos
- [ ] Exportación de conversaciones (PDF, DOCX)
- [ ] Compartir conversaciones
- [ ] Modo voz (speech-to-text)
- [ ] Integración con más LLMs (Claude, Llama, etc.)
- [ ] Panel de administración
- [ ] Analytics y métricas
- [ ] API para integraciones externas
- [ ] App móvil nativa

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👤 Autor

**Luciano - Apex 360**
- OTEC Apex Capacitaciones
- Especialista en HR Tech y sistemas de capacitación

## 🙏 Agradecimientos

- [LangChain](https://langchain.com) - Framework RAG
- [FastAPI](https://fastapi.tiangolo.com) - Framework web
- [ChromaDB](https://www.trychroma.com) - Base de datos vectorial
- [OpenAI](https://openai.com) - Modelos de lenguaje

---

**¿Necesitas ayuda?** Abre un issue en GitHub o consulta la [documentación de la API](http://localhost:8000/docs)
