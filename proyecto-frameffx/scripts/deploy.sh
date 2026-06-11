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
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod build

echo "🛑 Deteniendo contenedores anteriores..."
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod down

echo "🚀 Iniciando nuevos contenedores..."
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod up -d

echo "⏳ Esperando a que los servicios estén listos..."
sleep 10

echo "📋 Mostrando logs (Ctrl+C para salir)..."
docker compose -f docker/docker-compose.prod.yml --env-file .env.prod logs -f web

echo "================================"
echo "✨ Deploy completado"
echo "================================"
