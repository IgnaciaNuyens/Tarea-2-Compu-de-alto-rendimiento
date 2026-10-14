#!/usr/bin/env bash
# Muestra las caracteristicas del computador que pide el item (g):
# modelo de CPU, cores fisicos, cores logicos y velocidad de reloj.
# Funciona en Linux, WSL y macOS.

echo "Fecha: $(date)"
echo "Sistema: $(uname -srm)"
if grep -qi microsoft /proc/version 2>/dev/null; then
    echo "Entorno: WSL (Linux dentro de Windows)"
fi

if [[ "$(uname)" == "Darwin" ]]; then
    echo "CPU: $(sysctl -n machdep.cpu.brand_string)"
    echo "Cores fisicos: $(sysctl -n hw.physicalcpu)"
    echo "Cores logicos: $(sysctl -n hw.logicalcpu)"
    if sysctl -n hw.perflevel0.physicalcpu >/dev/null 2>&1; then
        echo "Cores de rendimiento (P): $(sysctl -n hw.perflevel0.physicalcpu)"
        echo "Cores de eficiencia (E): $(sysctl -n hw.perflevel1.physicalcpu 2>/dev/null)"
    fi
    f=$(sysctl -n hw.cpufrequency 2>/dev/null)
    if [[ -n "$f" ]]; then
        echo "Reloj base: $(awk -v f="$f" 'BEGIN{printf "%.2f GHz", f/1e9}')"
    else
        echo "Reloj: macOS no lo informa en Apple Silicon, buscar el modelo de chip en la web"
    fi
    echo "Memoria RAM: $(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 )) GB"
else
    modelo=$(lscpu | sed -n 's/^Model name:[[:space:]]*//p' | head -1)
    hilos_por_core=$(lscpu | sed -n 's/^Thread(s) per core:[[:space:]]*//p')
    cores_por_socket=$(lscpu | sed -n 's/^Core(s) per socket:[[:space:]]*//p')
    sockets=$(lscpu | sed -n 's/^Socket(s):[[:space:]]*//p')
    echo "CPU: $modelo"
    echo "Cores fisicos: $(( cores_por_socket * sockets ))"
    echo "Cores logicos: $(nproc --all)"
    echo "Threads por core: $hilos_por_core"
    maxmhz=$(lscpu | sed -n 's/^CPU max MHz:[[:space:]]*//p')
    [[ -n "$maxmhz" ]] && echo "Reloj maximo (turbo): $(awk -v f="$maxmhz" 'BEGIN{printf "%.2f GHz", f/1000}')"
    echo "Reloj base: ver el valor @ en el nombre de la CPU (si aparece) o buscar el modelo en la web"
    lscpu | grep -E "^L1d|^L2|^L3"
    echo "Memoria RAM: $(free -g | awk '/Mem:/{print $2}') GB"
fi
