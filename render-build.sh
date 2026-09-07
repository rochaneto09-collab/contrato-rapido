#!/usr/bin/env bash
# Sair em caso de erro
set -o errexit

# Atualizar pacotes e instalar LibreOffice
apt-get update && apt-get install -y libreoffice

# Instalar dependencias Python
pip install -r requirements.txt