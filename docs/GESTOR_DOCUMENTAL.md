# Gestor Documental - Apex AI

Sistema completo de gestión documental integrado con base de datos vectorial para el sistema RAG.

## 🎯 Características

### Gestión de Documentos
- ✅ **Subida masiva** de archivos (PDF, DOCX, PPTX, TXT)
- ✅ **Drag & Drop** para facilidad de uso
- ✅ **Validación** de tipos y tamaños de archivo
- ✅ **Metadatos completos** para cada documento
- ✅ **Edición** de metadatos en cualquier momento
- ✅ **Eliminación** de documentos y sus embeddings

### Metadatos Disponibles

#### Obligatorios
- **Categoría**: legal, hr, training, technical, general
- **Propietario**: Persona o equipo responsable del documento

#### Opcionales
- **Versión**: Control de versiones del documento
- **Departamento**: Departamento al que pertenece
- **Etiquetas**: Tags para búsqueda y clasificación
- **Descripción**: Descripción del contenido
- **Público**: Si es visible para todos los agentes
- **Indexable**: Si debe procesarse para RAG

#### Automáticos
- **Fecha de creación**: Timestamp de subida
- **Última modificación**: Timestamp de última edición
- **Tamaño**: Tamaño del archivo en bytes
- **Tipo**: Extensión del archivo
- **Estado**: active, processing, error, archived
- **Chunks**: Número de fragmentos generados
- **Estado de embedding**: completed, processing, error, not_indexed

### Visualización

#### Vista de Cuadrícula
- Tarjetas visuales con iconos por tipo de archivo
- Metadatos principales visibles
- Acciones rápidas por documento

#### Vista de Lista
- Tabla compacta con toda la información
- Ideal para gestión de múltiples documentos
- Ordenamiento y filtros avanzados

### Filtros y Búsqueda
- 🔍 **Búsqueda de texto** en nombre, descripción y etiquetas
- 📁 **Filtro por categoría**
- 📄 **Filtro por tipo de archivo**
- 🏷️ **Filtro por estado**
- ⚡ **Búsqueda en tiempo real**

## 📋 Uso del Sistema

### 1. Subir Documentos

**Opción A: Drag & Drop**
```
1. Abrir modal de subida (botón "Subir Documentos")
2. Arrastrar archivos a la zona de carga
3. Los archivos se validan automáticamente
```

**Opción B: Selector de archivos**
```
1. Clic en zona de carga
2. Seleccionar archivos del sistema
3. Pueden seleccionarse múltiples archivos
```

**Completar metadatos:**
```
- Categoría (obligatorio)
- Propietario (obligatorio)
- Versión (opcional, default: 1.0)
- Departamento (opcional)
- Etiquetas (separadas por comas)
- Descripción (opcional)
- Marcar si es público
- Marcar si debe indexarse en RAG
```

### 2. Editar Metadatos

```
1. Clic en botón "Editar" del documento
2. Modificar los campos necesarios
3. Guardar cambios
```

**Campos editables:**
- Categoría
- Estado
- Propietario
- Departamento
- Versión
- Etiquetas
- Descripción
- Público
- Indexable

**Campos de solo lectura:**
- Nombre del archivo
- Tipo
- Tamaño
- Fecha de creación
- Última modificación

### 3. Descargar Documentos

```
1. Clic en botón "Descargar"
2. El archivo se descarga automáticamente
```

### 4. Eliminar Documentos

```
1. Clic en botón "Eliminar"
2. Confirmar eliminación
3. El documento y sus embeddings se eliminan permanentemente
```

**⚠️ Advertencia:** La eliminación es permanente y no se puede deshacer.

## 🔄 Integración con RAG

### Proceso de Indexación

Cuando un documento se marca como "Indexable":

```
1. Subida del archivo
   ↓
2. Extracción de texto
   ↓
3. División en chunks (fragmentos)
   ↓
4. Generación de embeddings
   ↓
5. Almacenamiento en base vectorial
   ↓
6. Estado: Activo y listo para consultas
```

### Estados de Embedding

- **completed**: Documento indexado y listo
- **processing**: En proceso de indexación
- **error**: Error al indexar
- **not_indexed**: No marcado para indexación
- **pending_reindex**: Cambió a indexable, esperando procesamiento

### Búsqueda Semántica

Los documentos indexados están disponibles para:
- Consultas de los agentes IA
- Búsqueda por similitud semántica
- Generación de respuestas contextuales
- Citación de fuentes

## 📊 API Endpoints

### Listar Documentos
```bash
GET /api/documents
GET /api/documents?category=legal
GET /api/documents?status=active
```

### Obtener Documento
```bash
GET /api/documents/{document_id}
```

### Subir Documento
```bash
POST /api/documents/upload
Content-Type: multipart/form-data

file: (archivo)
category: "legal"
owner: "Luciano Araneda"
version: "1.0"
department: "Legal"
tags: "ley karin, protocolo"
description: "Protocolo de prevención"
public: true
indexable: true
```

### Actualizar Metadatos
```bash
PUT /api/documents/{document_id}
Content-Type: application/json

{
  "category": "hr",
  "status": "active",
  "owner": "Luciano Araneda",
  "version": "2.0",
  "tags": ["actualizado", "2024"],
  "description": "Versión actualizada",
  "public": true,
  "indexable": true
}
```

### Descargar Documento
```bash
GET /api/documents/{document_id}/download
```

### Eliminar Documento
```bash
DELETE /api/documents/{document_id}
```

## 🗄️ Estructura de Datos

### Documento en la Base de Datos

```json
{
  "id": "doc_1_1702541234",
  "filename": "Ley_Karin_Protocolo.pdf",
  "type": "pdf",
  "size": 2457600,
  "category": "legal",
  "status": "active",
  "owner": "Luciano Araneda",
  "department": "Legal",
  "version": "1.0",
  "tags": ["ley karin", "protocolo", "acoso laboral"],
  "description": "Protocolo completo de prevención",
  "public": true,
  "indexable": true,
  "created_at": "2024-12-01T10:30:00",
  "modified_at": "2024-12-10T15:45:00",
  "chunks_count": 45,
  "embedding_status": "completed"
}
```

## 🔐 Seguridad y Validación

### Validaciones de Archivo

- **Tipos permitidos**: PDF, DOCX, PPTX, TXT
- **Tamaño máximo**: 50 MB por archivo
- **Nombres**: Sin caracteres especiales problemáticos
- **Duplicados**: Advertencia si ya existe

### Permisos

- **Documentos públicos**: Accesibles por todos los agentes
- **Documentos privados**: Solo para agentes específicos
- **Control de acceso**: Basado en metadato "public"

## 📈 Estadísticas

El gestor muestra en tiempo real:

- **Total de documentos**: Número de archivos en el sistema
- **Espacio utilizado**: MB totales almacenados
- **Documentos por categoría**: Distribución
- **Estado de indexación**: Procesados vs pendientes

## 🎨 Personalización

### Categorías Personalizadas

Editar en `document-manager.js`:

```javascript
const CATEGORIES = [
  { value: 'legal', label: 'Legal' },
  { value: 'hr', label: 'Recursos Humanos' },
  { value: 'training', label: 'Capacitación' },
  { value: 'technical', label: 'Técnico' },
  { value: 'marketing', label: 'Marketing' },  // Nueva categoría
  { value: 'finance', label: 'Finanzas' }      // Nueva categoría
];
```

### Tipos de Archivo Adicionales

En `backend.py`, agregar nuevos loaders:

```python
elif file_path.endswith('.xlsx'):
    loader = UnstructuredExcelLoader(file_path)
elif file_path.endswith('.csv'):
    loader = CSVLoader(file_path)
```

## 🚀 Mejores Prácticas

### Organización de Documentos

1. **Usar categorías consistentes**
   - Mantener nomenclatura estándar
   - Evitar categorías redundantes

2. **Etiquetas descriptivas**
   - Usar etiquetas específicas y relevantes
   - Incluir sinónimos para mejor búsqueda

3. **Versiones**
   - Formato recomendado: X.Y (ej: 1.0, 1.1, 2.0)
   - Incrementar versión mayor en cambios significativos

4. **Descripciones útiles**
   - Resumen claro del contenido
   - Palabras clave importantes

### Mantenimiento

1. **Revisar documentos obsoletos**
   - Archivar documentos viejos
   - Eliminar duplicados

2. **Actualizar metadatos**
   - Mantener información actualizada
   - Revisar etiquetas periódicamente

3. **Monitorear espacio**
   - Verificar uso de almacenamiento
   - Comprimir archivos grandes si es posible

## 🔧 Troubleshooting

### Documento no se indexa

**Problema**: Estado permanece en "processing"

**Soluciones**:
1. Verificar que OPENAI_API_KEY está configurado
2. Revisar logs del backend
3. Verificar que el archivo no está corrupto
4. Reintentar marcando indexable nuevamente

### Error al subir archivo

**Problema**: Upload falla

**Soluciones**:
1. Verificar tamaño del archivo (< 50 MB)
2. Confirmar tipo de archivo permitido
3. Revisar permisos de carpeta ./uploads
4. Verificar espacio en disco

### No se pueden editar metadatos

**Problema**: Cambios no se guardan

**Soluciones**:
1. Verificar conexión con backend
2. Comprobar que documento existe
3. Revisar logs del navegador (F12)

## 📝 Roadmap

- [ ] Soporte para más tipos de archivo (XLSX, CSV, MD)
- [ ] Vista previa de documentos en el navegador
- [ ] Edición de documentos en línea
- [ ] Historial de versiones completo
- [ ] Compartir documentos con links
- [ ] Permisos granulares por usuario
- [ ] Carpetas y organización jerárquica
- [ ] Búsqueda full-text avanzada
- [ ] OCR para PDFs escaneados
- [ ] Compresión automática de archivos grandes

---

**Gestor Documental - Apex AI** | Sistema de gestión documental profesional para RAG
