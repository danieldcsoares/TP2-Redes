#!/bin/bash
IFACE="lo"

echo "[0s] Iniciando Fase 1: 5 Mbit/s (Rede Boa)"
sudo tc qdisc replace dev $IFACE root netem rate 5mbit
sleep 30

echo "[30s] Iniciando Fase 2: 1 Mbit/s (Queda Moderada)"
sudo tc qdisc replace dev $IFACE root netem rate 1mbit
sleep 30

echo "[60s] Iniciando Fase 3: 300 Kbit/s + 100ms delay (Gargalo)"
sudo tc qdisc replace dev $IFACE root netem rate 300kbit delay 100ms
sleep 30

echo "[90s] Iniciando Fase 4: 5 Mbit/s (Recuperação)"
sudo tc qdisc replace dev $IFACE root netem rate 5mbit
sleep 30

echo "[120s] Experimento finalizado! Removendo limitações..."
sudo tc qdisc del dev $IFACE root