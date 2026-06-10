#!/bin/bash
# ============================================================
# deploy.sh — Actualiza la aplicación en producción
# Ejecutar en el VPS cada vez que haya cambios en GitHub
# ============================================================

set -e

echo "================================"
echo "🚀 Iniciando deploy a producción"
echo "================================"

# Cambiar a directorio del proyecto
cd "$(dirname "$0")/.."

echo "📦 Descargando cambios del repositorio..."
git pull origin main

echo "🔨 Construyendo imagen Docker..."
docker compose -f docker/docker-compose.prod.yml build

echo "🛑 Deteniendo contenedores anteriores..."
docker compose -f docker/docker-compose.prod.yml down

echo "🚀 Iniciando nuevos contenedores..."
docker compose -f docker/docker-compose.prod.yml up -d

echo "⏳ Esperando a que los servicios estén listos..."
sleep 10

echo "📋 Mostrando logs (Ctrl+C para salir)..."
docker compose -f docker/docker-compose.prod.yml logs -f web

echo "================================"
echo "✨ Deploy completado"
echo "================================"
