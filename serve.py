#!/usr/bin/env python3
"""
Servidor simple para ejecutar Apex AI localmente
Sirve los archivos HTML, CSS y JS necesarios
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys

class ApexAIHandler(SimpleHTTPRequestHandler):
    """Handler personalizado para servir los archivos"""
    
    def end_headers(self):
        # Agregar headers CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def run_server(port=8080):
    """Iniciar servidor HTTP"""
    
    # Cambiar al directorio actual
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, ApexAIHandler)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                  APEX AI - SERVIDOR LOCAL                    ║
╚══════════════════════════════════════════════════════════════╝

✅ Servidor iniciado correctamente

🌐 Accede a la aplicación en:
   
   • Chat IA:            http://localhost:{port}
   • Gestor Documental:  http://localhost:{port}/document-manager.html
   • API Backend:        http://localhost:8000 (iniciar aparte)

📝 Archivos disponibles:
   - index.html (Chat principal)
   - document-manager.html (Gestor documental)
   - Todos los CSS y JS necesarios

⚠️  IMPORTANTE:
   Para funcionalidad completa, inicia también el backend:
   
   Terminal 1 (Frontend - ESTE):
   $ python serve.py
   
   Terminal 2 (Backend):
   $ python backend.py

🛑 Para detener: Ctrl+C

════════════════════════════════════════════════════════════════
    """)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido")
        httpd.shutdown()
        sys.exit(0)

if __name__ == '__main__':
    port = 8080
    
    # Verificar si el puerto está especificado
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Puerto inválido: {sys.argv[1]}")
            print("Uso: python serve.py [puerto]")
            sys.exit(1)
    
    run_server(port)
