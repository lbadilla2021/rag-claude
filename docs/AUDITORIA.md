Perfecto, gracias por aclarar 👍
Aquí va **TODO el contenido de la auditoría**, **completo, íntegro y autocontenido**, en **un solo archivo Markdown**, sin referencias externas ni resúmenes.
Puedes **copiar y guardar tal cual** como `AUDITORIA_RAG_ETAPA_1.md`.

---

````md
# Auditoría Técnica RAG – Etapa 1: Estabilización

Proyecto: Apex AI  
Tipo: Auditoría técnica de sistema RAG  
Estado: Producción temprana / pre-escalamiento  
Arquitectura validada: FastAPI + PostgreSQL + Qdrant + OpenAI  
Fecha: ___________________

---

## 0. Objetivo de la auditoría

Esta auditoría tiene como objetivo validar que el sistema RAG:

- Recupera información **real** desde documentos cargados
- No genera respuestas genéricas o inventadas
- Responde **exclusivamente** usando contexto documental
- Falla de forma controlada cuando no hay información
- Mantiene coherencia entre backend y frontend

Esta etapa **NO** evalúa:
- OCR
- Multi-tenant
- Autenticación
- Agentes especialistas
- Performance o costos

---

## 1. Ingesta de documentos

### 1.1 Verificación de texto real en PDFs

**Objetivo:** confirmar que el PDF contiene texto y no solo imágenes.

**Prueba**
```bash
python - <<EOF
from PyPDF2 import PdfReader
r = PdfReader("archivo.pdf")
print(sum(len((p.extract_text() or "")) for p in r.pages))
EOF
````

**Criterios**

* ✔️ Más de 500 caracteres → Documento válido
* ❌ Menos de 100 caracteres → PDF imagen (OCR pendiente)

**Acción correctiva**

* Marcar documento como `needs_ocr`
* Excluirlo del pipeline RAG

---

## 2. Chunking

### 2.1 Existencia de chunks por documento

```sql
SELECT document_id, COUNT(*) 
FROM document_chunks 
GROUP BY document_id;
```

**Criterios**

* ✔️ 3 o más chunks → correcto
* ❌ 0 chunks → ingestión fallida

---

### 2.2 Detección de chunks vacíos o irrelevantes

```sql
SELECT COUNT(*) 
FROM document_chunks 
WHERE LENGTH(TRIM(content)) < 50;
```

**Criterios**

* ✔️ 0 registros → correcto
* ❌ > 0 → chunking defectuoso

**Acción correctiva**

* Excluir chunks < 50 caracteres del embedding

---

## 3. Embeddings y Vector DB (Qdrant)

### 3.1 Conteo de vectores

```bash
curl -X POST http://localhost:6333/collections/documents/points/count \
  -H "Content-Type: application/json" \
  -d '{}' | jq
```

**Criterios**

* ✔️ Cantidad de vectores ≈ cantidad de chunks
* ❌ Menor cantidad → ingestión incompleta

---

### 3.2 Validación de payload en Qdrant

```bash
curl -X POST http://localhost:6333/collections/documents/points/scroll \
  -H "Content-Type: application/json" \
  -d '{ "limit": 1 }' | jq
```

**Campos obligatorios**

```json
payload.content
payload.filename
payload.document_id
```

**Criterio**

* ✔️ Todos presentes → RAG funcional
* ❌ Falta `content` → RAG ciego

---

## 4. Recuperación semántica

### 4.1 Confirmación de resultados desde Qdrant

Agregar log temporal en `/api/ask`:

```python
logger.info(f"Resultados Qdrant: {len(search_results)}")
```

**Criterios**

* ✔️ Al menos 1 resultado
* ❌ 0 resultados → embeddings o consulta mal alineados

---

### 4.2 Evaluación de scores semánticos

```python
for hit in search_results:
    logger.info(hit.score)
```

**Interpretación**

* ✔️ > 0.25 → contexto usable
* ⚠️ 0.15 – 0.25 → débil
* ❌ < 0.15 → ruido

Nota: el umbral definitivo se define en Etapa 3.

---

## 5. Prompt RAG (Control del modelo)

### 5.1 Prueba de respuesta sin contexto

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{ "question": "¿Cuál es la capital de Japón?" }'
```

**Respuesta esperada**

```
No hay información suficiente en los documentos cargados.
```

**Criterios**

* ✔️ Respuesta negativa → correcto
* ❌ Respuesta factual → prompt inválido

---

### 5.2 Evaluación de uso del contexto

Validar que las respuestas:

* Citan fechas, artículos o definiciones reales
* No usan conocimiento general
* No rellenan con explicaciones genéricas

---

## 6. Contrato Backend ↔ Frontend

### 6.1 Fuentes reales

El backend debe retornar en `sources`:

```json
{
  "filename",
  "chunk_index",
  "score"
}
```

**Criterios**

* ✔️ Frontend muestra fuentes reales
* ❌ Frontend inventa títulos → mock activo

---

## 7. Señales de alerta (STOP)

No avanzar de etapa si ocurre alguno:

* Respuestas educadas pero vacías
* Nunca responde “no hay información”
* Scores siempre similares
* No existe trazabilidad a documentos
* Frontend muestra datos ficticios

---

## 8. Resultado esperado al cerrar Etapa 1

* El sistema responde solo con documentos
* El modelo dice NO cuando corresponde
* El contexto es real y trazable
* El pipeline es estable y predecible

---

## 9. Estado de la etapa

* [ ] Etapa 1.A – Prompt anti-respuesta genérica
* [ ] Etapa 1.B – Auditoría técnica completa
* [ ] Etapa 1.C – Contrato frontend ↔ backend validado

Solo avanzar cuando **todas** estén completas.

---

## 10. Próxima etapa (bloqueada hasta cierre)

**Etapa 2 – Inteligencia**

* Router de intención
* Decisión RAG vs agentes especialistas
* Base para agentes expertos (HR, Legal, Técnico)

---

Documento vivo.
Debe ejecutarse nuevamente ante:

* Nuevos documentos
* Cambios de embeddings
* Cambios de prompt
* Incidentes en producción

```

---

Si quieres, el siguiente paso natural es uno de estos (tú eliges):

1️⃣ Script automático que ejecute toda la auditoría  
2️⃣ Versión Word / PDF para clientes o auditoría externa  
3️⃣ Healthcheck avanzado integrado al backend  
4️⃣ Pasar formalmente a **Etapa 2 (Router de intención)**
```
