# 🚀 INSTRUCCIONES DE DEPLOYMENT

## Problema Común en Servidores

Si ves la página pero los enlaces no funcionan, verifica:

### ✅ Estructura de Archivos Correcta

Todos estos archivos deben estar en la MISMA carpeta:

```
tu-servidor/
├── index.html              ← Chat principal (OBLIGATORIO)
├── document-manager.html   ← Gestor documental
├── styles.css              ← Estilos (OBLIGATORIO)
├── document-manager.css    ← Estilos del gestor
├── app.js                  ← JavaScript del chat (OBLIGATORIO)
├── document-manager.js     ← JavaScript del gestor
└── backend.py              ← Backend (opcional, para funcionalidad completa)
```

### ✅ Verificación Rápida

Abre tu navegador y prueba cada URL:

```
http://TU-SERVIDOR:PUERTO/index.html          ← Debe cargar el chat
http://TU-SERVIDOR:PUERTO/document-manager.html  ← Debe cargar el gestor
http://TU-SERVIDOR:PUERTO/styles.css          ← Debe mostrar CSS
http://TU-SERVIDOR:PUERTO/app.js              ← Debe mostrar JavaScript
```

Si alguno da error 404, ese archivo NO está en la carpeta correcta.

### ✅ Navegación

- **index.html** = Chat principal
- Click en "Documentos" → va a document-manager.html
- En document-manager.html, click en "Chat IA" → vuelve a index.html

### ❌ Errores Comunes

**Problema**: Los archivos están pero no cargan
**Causa**: Permisos incorrectos en el servidor
**Solución**:
```bash
chmod 644 *.html *.css *.js
chmod 755 *.py
```

**Problema**: "404 Not Found" en los enlaces
**Causa**: Archivos en carpetas diferentes
**Solución**: Todos los archivos HTML, CSS y JS deben estar en la MISMA carpeta

**Problema**: La página se ve pero sin estilos
**Causa**: styles.css no está accesible
**Solución**: Verifica que styles.css esté en la misma carpeta que index.html

### 🔧 Configuración de Nginx (si usas Nginx)

```nginx
server {
    listen 8900;
    server_name 65.108.150.100;
    root /ruta/a/tu/carpeta;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    # CORS headers si necesitas llamar a API en otro puerto
    add_header Access-Control-Allow-Origin *;
}
```

### 🔧 Configuración de Apache

```apache
<VirtualHost *:8900>
    DocumentRoot /ruta/a/tu/carpeta
    
    <Directory /ruta/a/tu/carpeta>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>
</VirtualHost>
```

### 🐍 Servidor Python Simple (para desarrollo)

Si estás probando en local o en servidor:

```bash
cd /ruta/a/tu/carpeta
python3 -m http.server 8900
```

Luego accede a: http://65.108.150.100:8900

### 📋 Checklist de Deployment

- [ ] Todos los archivos HTML, CSS y JS están en la misma carpeta
- [ ] Los archivos tienen permisos de lectura (644)
- [ ] El servidor web apunta a esa carpeta
- [ ] Puedes acceder a index.html directamente
- [ ] Los estilos se cargan (la página no se ve "sin formato")
- [ ] Los enlaces funcionan correctamente

### 🆘 Debugging

Para saber qué está fallando:

1. **Abre la consola del navegador** (F12)
2. **Ve a la pestaña "Network"**
3. **Recarga la página**
4. **Busca errores en rojo** (404, 403, etc.)
5. Esos errores te dirán qué archivo no se encuentra

### 📞 URLs de Verificación

En tu caso específico (65.108.150.100:8900):

```
✅ http://65.108.150.100:8900/
   → Debe mostrar el chat

✅ http://65.108.150.100:8900/index.html
   → Debe mostrar el chat

✅ http://65.108.150.100:8900/document-manager.html
   → Debe mostrar el gestor de documentos

✅ http://65.108.150.100:8900/styles.css
   → Debe mostrar el código CSS (no 404)
```

Si todos funcionan pero el click en los botones no funciona, es un problema de JavaScript. Verifica:

```
✅ http://65.108.150.100:8900/app.js
   → Debe mostrar el código JavaScript
```

---

**Resumen**: Todos los archivos en UNA sola carpeta, servidor web apuntando a esa carpeta, permisos correctos. ¡Así de simple!
