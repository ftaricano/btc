#!/usr/bin/env python3
"""
Script para descobrir o IP local para acesso pelo celular
"""

import socket
import subprocess
import platform

def get_local_ip():
    """Descobre o IP local da máquina"""
    try:
        # Método 1: Conectar a um servidor externo
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        pass
    
    try:
        # Método 2: Usar hostname
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip != "127.0.0.1":
            return ip
    except:
        pass
    
    return None

def get_network_info():
    """Obtém informações de rede do sistema"""
    system = platform.system().lower()
    
    try:
        if system == "windows":
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
        else:
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        
        return result.stdout
    except:
        return "Não foi possível obter informações de rede"

def main():
    print("🔍 Descobrindo IP local para acesso pelo celular...")
    print("=" * 50)
    
    # IP local
    local_ip = get_local_ip()
    if local_ip:
        print(f"📱 IP Local: {local_ip}")
        print(f"🌐 URL para o celular: http://{local_ip}:8080")
    else:
        print("❌ Não foi possível descobrir o IP local automaticamente")
    
    print("\n" + "=" * 50)
    print("💡 Como usar:")
    print("1. Execute: python web_collector.py")
    print("2. No celular, acesse a URL acima")
    print("3. Conecte o celular na mesma rede WiFi")
    
    print("\n" + "=" * 50)
    print("🔧 Informações de rede completas:")
    print(get_network_info())

if __name__ == "__main__":
    main() 