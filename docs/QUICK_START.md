# 🚀 INICIO RÁPIDO - Apex AI

## Opción 1: Inicio Rápido con Script (Recomendado)

```bash
# 1. Dar permisos al script
chmod +x start.sh

# 2. Ejecutar script de inicio
./start.sh
```

El script te guiará a través de:
- ✅ Verificación de requisitos
- ✅ Creación de entorno virtual
- ✅ Instalación de dependencias
- ✅ Configuración de variables de entorno
- ✅ Selección de modo de inicio

## Opción 2: Docker Compose (Producción)

```bash
# 1. Configurar variables de entorno
cp .env.example .env
nano .env  # Agregar OPENAI_API_KEY

# 2. Iniciar servicios
docker-compose up -d

# 3. Verificar estado
docker-compose ps

# Acceder a:
# - Frontend: http://localhost:8080
# - Backend API: http://localhost:8000/docs
```

## Opción 3: Manual (Desarrollo)

### Servidor Frontend Simple
```bash
# Opción más simple - usar el servidor incluido
python serve.py

# O usar Python estándar
python -m http.server 8080

# O Node.js
npx http-server -p 8080
```

### Backend
```bash
# Terminal aparte para el backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env y agregar OPENAI_API_KEY
python backend.py
```

## Configuración Mínima

### Archivo .env (Obligatorio)
```bash
# Mínimo necesario para funcionar
OPENAI_API_KEY=sk-tu-api-key-aqui
```

**Nota**: Sin OPENAI_API_KEY, el sistema funcionará en modo simulado.

## Verificar Instalación

```bash
# Probar backend
curl http://localhost:8000/api/health

# Ejecutar suite de pruebas
python test.py

# Modo interactivo
python test.py --interactive
```

## Acceso a la Aplicación

Una vez iniciado:

1. **Página Principal**: http://localhost:8080
   - Portal de entrada con enlaces a ambas aplicaciones
   
2. **Chat IA**: http://localhost:8080/chat.html
   - Interfaz conversacional estilo ChatGPT
   - Selector de agentes especializados
   
3. **Gestor Documental**: http://localhost:8080/document-manager.html
   - Gestión completa de documentos
   - Subir, editar, eliminar archivos
   - Control de metadatos y versiones
   
4. **Backend API**: http://localhost:8000
   - Documentación interactiva: http://localhost:8000/docs
   - Health check: http://localhost:8000/api/health

**⚠️ IMPORTANTE**: Debes acceder mediante servidor web (http://localhost) y NO abrir los archivos HTML directamente desde el explorador de archivos (file:///) para que los enlaces entre páginas funcionen correctamente.

## Primeros Pasos

### Chat IA

1. **Selecciona un agente** según tu consulta:
   - General: Consultas variadas
   - HR: Ley Karin, legislación laboral
   - Legal: Normativas y compliance
   - Technical: Soporte técnico
   - Training: Capacitación

2. **Haz tu primera consulta**:
   - "¿Cuáles son los requisitos de la Ley Karin?"
   - "Explica qué es un sistema RAG"
   - "Dame consejos para capacitación efectiva"

3. **Revisa las fuentes**:
   - Cada respuesta muestra documentos consultados
   - Scores de relevancia
   - Referencias específicas

### Gestor Documental

1. **Acceder al gestor**: Clic en "Documentos" en el menú lateral

2. **Subir documentos**:
   - Botón "Subir Documentos"
   - Arrastrar archivos o seleccionar
   - Completar metadatos (categoría, propietario, etc.)
   - Marcar si debe indexarse en RAG

3. **Gestionar documentos**:
   - **Editar**: Modificar metadatos, versión, tags
   - **Descargar**: Obtener copia del archivo
   - **Eliminar**: Quitar documento y embeddings

4. **Buscar y filtrar**:
   - Búsqueda por texto
   - Filtrar por categoría, tipo, estado
   - Cambiar entre vista de cuadrícula y lista

## Cargar Documentos

### Vía API
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@documento.pdf" \
  -F "category=legal"
```

### Vía Interfaz
- Clic en botón de adjuntar (📎)
- Seleccionar archivo
- Los documentos se procesan y agregan a la base vectorial

## Problemas Comunes

### Backend no inicia
```bash
# Verificar Python
python3 --version  # Debe ser 3.11+

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Error de OPENAI_API_KEY
```bash
# Verificar que existe
cat .env | grep OPENAI_API_KEY

# El sistema funcionará en modo simulado sin ella
```

### Puerto ya en uso
```bash
# Backend en otro puerto
uvicorn backend:app --port 8001

# Frontend en otro puerto
python -m http.server 8081
```

## Comandos Útiles

```bash
# Ver logs del backend (Docker)
docker-compose logs -f backend

# Reiniciar servicios
docker-compose restart

# Detener todo
docker-compose down

# Ver estadísticas del sistema
curl http://localhost:8000/api/stats

# Probar consulta específica
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "agent": "general"}'
```

## Estructura de Archivos Importantes

```
apex-ai/
├── index.html          # Frontend principal
├── app.js             # Lógica del frontend
├── styles.css         # Estilos
├── backend.py         # API y sistema RAG
├── .env               # Variables de entorno (crear desde .env.example)
├── start.sh           # Script de inicio
├── test.py            # Suite de pruebas
├── README.md          # Documentación completa
└── docker-compose.yml # Configuración Docker
```

## Próximos Pasos

1. ✅ Revisar README.md para documentación completa
2. ✅ Configurar OPENAI_API_KEY para funcionalidad completa
3. ✅ Cargar tus documentos a la base vectorial
4. ✅ Personalizar agentes según tus necesidades
5. ✅ Explorar la API en http://localhost:8000/docs

## Soporte

- 📖 Documentación: Ver README.md
- 🧪 Pruebas: `python test.py --interactive`
- 📊 API Docs: http://localhost:8000/docs
- 🐛 Issues: Revisar logs en `./logs/`

---

**¡Listo para usar Apex AI! 🎉**
