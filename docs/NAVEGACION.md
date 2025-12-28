# ⚠️ IMPORTANTE: Cómo Ejecutar la Aplicación

## 🚫 Problema Común

Si abres los archivos HTML **directamente desde el explorador de archivos** (usando file:///), los enlaces entre páginas NO funcionarán correctamente.

## ✅ Solución: Usar un Servidor Web

Debes servir los archivos a través de un servidor HTTP. Aquí tienes 3 opciones:

### Opción 1: Servidor Python Incluido (Más Fácil)

```bash
# Navegar a la carpeta del proyecto
cd apex-ai

# Iniciar servidor
python serve.py

# Acceder en el navegador
http://localhost:8080
```

### Opción 2: Python Simple

```bash
# Navegar a la carpeta del proyecto
cd apex-ai

# Python 3
python -m http.server 8080

# Acceder en el navegador
http://localhost:8080
```

### Opción 3: Node.js

```bash
# Instalar http-server globalmente (una sola vez)
npm install -g http-server

# En la carpeta del proyecto
http-server -p 8080

# Acceder en el navegador
http://localhost:8080
```

### Opción 4: Docker Compose (Producción)

```bash
# En la carpeta del proyecto
docker-compose up -d

# Acceder en el navegador
http://localhost:8080
```

## 📍 URLs de Acceso

Una vez el servidor esté corriendo:

- **🏠 Inicio**: http://localhost:8080
- **💬 Chat IA**: http://localhost:8080/chat.html
- **📁 Gestor Documental**: http://localhost:8080/document-manager.html
- **🔧 API Backend**: http://localhost:8000/docs (requiere iniciar backend aparte)

## 🔄 Navegación entre Páginas

Una vez usando un servidor web:
- Desde la **página de inicio** → clic en las tarjetas para ir al Chat o Gestor
- En el **menú lateral** → clic en "Chat IA" o "Documentos" para cambiar entre aplicaciones
- Todo funcionará correctamente ✅

## 🐛 Si Aún No Funciona

1. **Verifica que el servidor esté corriendo**
   ```bash
   # Deberías ver algo como:
   # Serving HTTP on 0.0.0.0 port 8080 ...
   ```

2. **Verifica que accedes mediante http:// y NO file://**
   - ✅ CORRECTO: `http://localhost:8080`
   - ❌ INCORRECTO: `file:///C:/Users/...`

3. **Verifica que los archivos estén en la misma carpeta**
   ```
   apex-ai/
   ├── index.html
   ├── chat.html
   ├── document-manager.html
   ├── styles.css
   ├── app.js
   └── document-manager.js
   ```

4. **Revisa la consola del navegador (F12)**
   - Busca errores 404 (archivos no encontrados)
   - Busca errores CORS (si usas file://)

## 📦 Estructura Completa del Proyecto

```
apex-ai/
├── index.html              # Página de inicio
├── welcome.html            # Igual que index.html
├── chat.html               # Chat IA
├── document-manager.html   # Gestor documental
├── styles.css              # Estilos compartidos
├── document-manager.css    # Estilos del gestor
├── app.js                  # Lógica del chat
├── document-manager.js     # Lógica del gestor
├── serve.py                # Servidor Python simple
├── backend.py              # API FastAPI
└── ...
```

## 🎯 Resumen

1. **NO** abrir archivos HTML directamente
2. **SÍ** usar servidor web (Python, Node, Docker)
3. **Acceder** vía http://localhost:8080
4. **Disfrutar** de la navegación fluida ✨

---

**¿Necesitas ayuda?** Revisa QUICK_START.md o README.md para más detalles.
