#!/usr/bin/env bash
# Sair imediatamente em caso de erro
set -o errexit

# Atualizar repositórios e instalar LibreOffice no container Linux
apt-get update && apt-get install -y libreoffice

# Instalar as dependências do Python
pip install -r requirements.txt