#!/usr/bin/env python3
"""
Rechnungsgenerator GoBD - Application Runner
=============================================

Este script permite iniciar/detener la aplicación completa desde VS Code.

Uso:
    python run.py start      - Inicia backend y frontend
    python run.py stop       - Detiene todos los servicios
    python run.py restart    - Reinicia la aplicación
    python run.py status     - Muestra el estado de los servicios
    
O simplemente ejecuta con F5 en VS Code para iniciar la aplicación.
"""

import os
import sys
import time
import subprocess
import signal
import psutil
from pathlib import Path
from typing import Optional, List


class Colors:
    """ANSI color codes"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class AppRunner:
    """Gestor de la aplicación Rechnungsgenerator"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.backend_dir = self.base_dir / "backend"
        self.frontend_dir = self.base_dir / "frontend"
        self.pid_file = self.base_dir / ".app_pids.txt"
        
    def print_header(self, text: str):
        """Imprime un header formateado"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    def print_success(self, text: str):
        """Imprime mensaje de éxito"""
        print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")
    
    def print_error(self, text: str):
        """Imprime mensaje de error"""
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")
    
    def print_info(self, text: str):
        """Imprime mensaje informativo"""
        print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")
    
    def print_warning(self, text: str):
        """Imprime mensaje de advertencia"""
        print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")
    
    def is_port_in_use(self, port: int) -> bool:
        """Verifica si un puerto está en uso"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return True
        return False
    
    def get_process_on_port(self, port: int) -> Optional[int]:
        """Obtiene el PID del proceso usando un puerto"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return conn.pid
        return None
    
    def kill_process_tree(self, pid: int):
        """Mata un proceso y todos sus hijos"""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Primero intentamos terminar gracefully
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            
            parent.terminate()
            
            # Esperamos un poco
            gone, alive = psutil.wait_procs(children + [parent], timeout=3)
            
            # Si aún quedan procesos vivos, los matamos a la fuerza
            for p in alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
                    
        except psutil.NoSuchProcess:
            pass
    
    def stop_services(self):
        """Detiene todos los servicios"""
        self.print_header("Deteniendo Servicios")
        
        # Detener backend (puerto 8000)
        backend_pid = self.get_process_on_port(8000)
        if backend_pid:
            self.print_info(f"Deteniendo backend (PID: {backend_pid})...")
            self.kill_process_tree(backend_pid)
            time.sleep(1)
            if not self.is_port_in_use(8000):
                self.print_success("Backend detenido")
            else:
                self.print_error("No se pudo detener el backend")
        else:
            self.print_warning("Backend no estaba corriendo")
        
        # Detener frontend (puerto 5173)
        frontend_pid = self.get_process_on_port(5173)
        if frontend_pid:
            self.print_info(f"Deteniendo frontend (PID: {frontend_pid})...")
            self.kill_process_tree(frontend_pid)
            time.sleep(1)
            if not self.is_port_in_use(5173):
                self.print_success("Frontend detenido")
            else:
                self.print_error("No se pudo detener el frontend")
        else:
            self.print_warning("Frontend no estaba corriendo")
        
        # Limpiar archivo de PIDs
        if self.pid_file.exists():
            self.pid_file.unlink()
    
    def check_dependencies(self) -> bool:
        """Verifica que las dependencias estén instaladas"""
        self.print_info("Verificando dependencias...")
        
        # Verificar Python venv del backend
        backend_venv = self.backend_dir / "venv" / "bin" / "python"
        if not backend_venv.exists():
            self.print_error(f"No se encontró el virtualenv del backend en {backend_venv}")
            self.print_info("Ejecuta: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt")
            return False
        
        # Verificar node_modules del frontend
        frontend_modules = self.frontend_dir / "node_modules"
        if not frontend_modules.exists():
            self.print_error(f"No se encontró node_modules en el frontend")
            self.print_info("Ejecuta: cd frontend && npm install")
            return False
        
        self.print_success("Todas las dependencias están instaladas")
        return True
    
    def start_backend(self) -> Optional[subprocess.Popen]:
        """Inicia el backend"""
        self.print_info("Iniciando backend en http://localhost:8000...")
        
        if self.is_port_in_use(8000):
            self.print_warning("El puerto 8000 ya está en uso")
            return None
        
        venv_python = self.backend_dir / "venv" / "bin" / "python"
        
        # Iniciamos el backend
        process = subprocess.Popen(
            [str(venv_python), "-m", "uvicorn", "app.main:app", 
             "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=str(self.backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Esperamos a que el backend esté listo
        self.print_info("Esperando a que el backend esté listo...")
        max_retries = 30
        for i in range(max_retries):
            if self.is_port_in_use(8000):
                self.print_success(f"Backend iniciado (PID: {process.pid})")
                return process
            time.sleep(1)
        
        self.print_error("El backend no pudo iniciar en 30 segundos")
        process.kill()
        return None
    
    def start_frontend(self) -> Optional[subprocess.Popen]:
        """Inicia el frontend"""
        self.print_info("Iniciando frontend en http://localhost:5173...")
        
        if self.is_port_in_use(5173):
            self.print_warning("El puerto 5173 ya está en uso")
            return None
        
        # Iniciamos el frontend
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(self.frontend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Esperamos a que el frontend esté listo
        self.print_info("Esperando a que el frontend esté listo...")
        max_retries = 30
        for i in range(max_retries):
            if self.is_port_in_use(5173):
                self.print_success(f"Frontend iniciado (PID: {process.pid})")
                return process
            time.sleep(1)
        
        self.print_error("El frontend no pudo iniciar en 30 segundos")
        process.kill()
        return None
    
    def start_services(self):
        """Inicia todos los servicios"""
        self.print_header("Rechnungsgenerator GoBD - Iniciando Aplicación")
        
        # Verificar dependencias
        if not self.check_dependencies():
            sys.exit(1)
        
        # Detener servicios existentes
        if self.is_port_in_use(8000) or self.is_port_in_use(5173):
            self.print_warning("Hay servicios corriendo, deteniéndolos primero...")
            self.stop_services()
            time.sleep(2)
        
        # Iniciar backend
        backend_process = self.start_backend()
        if not backend_process:
            self.print_error("No se pudo iniciar el backend")
            sys.exit(1)
        
        time.sleep(2)
        
        # Iniciar frontend
        frontend_process = self.start_frontend()
        if not frontend_process:
            self.print_error("No se pudo iniciar el frontend")
            self.print_info("Deteniendo backend...")
            self.kill_process_tree(backend_process.pid)
            sys.exit(1)
        
        # Guardar PIDs
        with open(self.pid_file, 'w') as f:
            f.write(f"{backend_process.pid}\n")
            f.write(f"{frontend_process.pid}\n")
        
        # Mostrar información
        self.print_header("Aplicación Iniciada Correctamente")
        print(f"{Colors.OKGREEN}✓ Backend:  {Colors.BOLD}http://localhost:8000{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ Frontend: {Colors.BOLD}http://localhost:5173{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ API Docs: {Colors.BOLD}http://localhost:8000/docs{Colors.ENDC}")
        print()
        self.print_info("Presiona Ctrl+C para detener la aplicación")
        print()
        
        # Mantener el script corriendo y mostrar logs
        try:
            while True:
                # Verificar que los procesos sigan vivos
                if backend_process.poll() is not None:
                    self.print_error("El backend se ha detenido inesperadamente")
                    break
                if frontend_process.poll() is not None:
                    self.print_error("El frontend se ha detenido inesperadamente")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print()
            self.print_info("Deteniendo aplicación...")
            self.stop_services()
            self.print_success("Aplicación detenida correctamente")
    
    def show_status(self):
        """Muestra el estado de los servicios"""
        self.print_header("Estado de los Servicios")
        
        # Backend
        backend_pid = self.get_process_on_port(8000)
        if backend_pid:
            self.print_success(f"Backend corriendo (PID: {backend_pid}) - http://localhost:8000")
        else:
            self.print_warning("Backend no está corriendo")
        
        # Frontend
        frontend_pid = self.get_process_on_port(5173)
        if frontend_pid:
            self.print_success(f"Frontend corriendo (PID: {frontend_pid}) - http://localhost:5173")
        else:
            self.print_warning("Frontend no está corriendo")
    
    def restart_services(self):
        """Reinicia todos los servicios"""
        self.print_header("Reiniciando Aplicación")
        self.stop_services()
        time.sleep(2)
        self.start_services()


def main():
    runner = AppRunner()
    
    # Si no hay argumentos, iniciar la aplicación (para el play button de VS Code)
    if len(sys.argv) == 1:
        runner.start_services()
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        runner.start_services()
    elif command == "stop":
        runner.stop_services()
    elif command == "restart":
        runner.restart_services()
    elif command == "status":
        runner.show_status()
    else:
        print(f"Comando desconocido: {command}")
        print("Uso: python run.py [start|stop|restart|status]")
        sys.exit(1)


if __name__ == "__main__":
    main()
