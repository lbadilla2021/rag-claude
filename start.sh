#!/bin/bash

# Apex AI - Script de Inicio Rápido
# Este script facilita el inicio del sistema en modo desarrollo

set -e

echo "🚀 Apex AI - Sistema RAG con Agentes Inteligentes"
echo "=================================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_message() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Verificar Python
check_python() {
    print_info "Verificando Python..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 no está instalado"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_message "Python $PYTHON_VERSION encontrado"
}

# Verificar Docker
check_docker() {
    print_info "Verificando Docker..."
    if ! command -v docker &> /dev/null; then
        print_warning "Docker no está instalado (opcional)"
        return 1
    fi
    print_message "Docker encontrado"
    return 0
}

# Crear entorno virtual
setup_venv() {
    print_info "Configurando entorno virtual..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_message "Entorno virtual creado"
    else
        print_message "Entorno virtual ya existe"
    fi
}

# Instalar dependencias
install_dependencies() {
    print_info "Instalando dependencias..."
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt
    print_message "Dependencias instaladas"
}

# Configurar variables de entorno
setup_env() {
    print_info "Configurando variables de entorno..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_warning "Archivo .env creado - Por favor configura OPENAI_API_KEY"
        print_info "Abre .env y agrega tu API key de OpenAI"
    else
        print_message "Archivo .env ya existe"
    fi
}

# Crear directorios necesarios
setup_directories() {
    print_info "Creando directorios..."
    mkdir -p chroma_db uploads logs
    print_message "Directorios creados"
}

# Modo de inicio
start_mode_selection() {
    echo ""
    print_info "Selecciona modo de inicio:"
    echo "  1) Desarrollo local (Python + HTTP Server)"
    echo "  2) Docker Compose (Recomendado)"
    echo "  3) Solo Backend"
    echo "  4) Configuración completa sin iniciar"
    echo ""
    read -p "Selecciona una opción (1-4): " mode
    
    case $mode in
        1)
            start_local
            ;;
        2)
            start_docker
            ;;
        3)
            start_backend_only
            ;;
        4)
            print_message "Configuración completada"
            echo ""
            print_info "Para iniciar manualmente:"
            echo "  Backend: python backend.py"
            echo "  Frontend: python -m http.server 8080"
            ;;
        *)
            print_error "Opción inválida"
            exit 1
            ;;
    esac
}

# Inicio en modo desarrollo local
start_local() {
    print_info "Iniciando en modo desarrollo local..."
    
    # Verificar si .env tiene API key
    if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        print_warning "OPENAI_API_KEY no configurado - el sistema funcionará en modo simulado"
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Iniciar backend en background
    print_info "Iniciando backend en http://localhost:8000"
    python backend.py &
    BACKEND_PID=$!
    
    # Esperar a que el backend esté listo
    sleep 3
    
    # Iniciar frontend
    print_info "Iniciando frontend en http://localhost:8080"
    python -m http.server 8080 &
    FRONTEND_PID=$!
    
    echo ""
    print_message "Sistema iniciado correctamente!"
    echo ""
    print_info "Accede a la aplicación en: ${BLUE}http://localhost:8080${NC}"
    print_info "Documentación API en: ${BLUE}http://localhost:8000/docs${NC}"
    echo ""
    print_warning "Presiona Ctrl+C para detener el sistema"
    echo ""
    
    # Trap para limpiar procesos al salir
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
    
    # Mantener script corriendo
    wait
}

# Inicio con Docker Compose
start_docker() {
    print_info "Iniciando con Docker Compose..."
    
    if ! check_docker; then
        print_error "Docker no está disponible"
        exit 1
    fi
    
    # Verificar docker-compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose no está instalado"
        exit 1
    fi
    
    # Construir y levantar servicios
    print_info "Construyendo imágenes..."
    docker-compose build
    
    print_info "Levantando servicios..."
    docker-compose up -d
    
    # Esperar a que los servicios estén listos
    sleep 5
    
    # Verificar estado
    docker-compose ps
    
    echo ""
    print_message "Sistema iniciado con Docker Compose!"
    echo ""
    print_info "Accede a la aplicación en: ${BLUE}http://localhost:8080${NC}"
    print_info "Documentación API en: ${BLUE}http://localhost:8000/docs${NC}"
    echo ""
    print_info "Para ver logs: docker-compose logs -f"
    print_info "Para detener: docker-compose down"
}

# Solo backend
start_backend_only() {
    print_info "Iniciando solo backend..."
    
    source venv/bin/activate
    print_info "Backend corriendo en http://localhost:8000"
    python backend.py
}

# Función principal
main() {
    # Verificar requisitos
    check_python
    
    # Setup inicial
    setup_venv
    install_dependencies
    setup_env
    setup_directories
    
    # Seleccionar modo de inicio
    start_mode_selection
}

# Ejecutar
main
