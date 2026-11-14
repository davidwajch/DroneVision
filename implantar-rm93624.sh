#!/usr/bin/env bash
# ==========================================================================
#  DroneVision - Script de implantacao automatizada
#  GS 2o Semestre - Cloud Computing & Machine as a Service (MaaS) - FIAP 5EMR
#
#  Marcelo Alves da Silva Junior - RM93624
#  Joao Pedro Leca Ferreira      - RM565431
#
#  Cria toda a infraestrutura na Azure via Azure CLI e publica a aplicacao.
#  >>> Executar no Azure Cloud Shell (modo Bash) <<<
#
#  Como usar:
#    1. Abra o Azure Cloud Shell (https://shell.azure.com) em modo Bash
#    2. Faca o clone do repositorio:  git clone <URL_DO_SEU_REPO>
#    3. Entre na pasta do projeto:    cd <pasta-do-repo>
#    4. De permissao e execute:       chmod +x implantar-rm93624.sh && ./implantar-rm93624.sh
# ==========================================================================

set -euo pipefail

# ------------------------- Parametros -------------------------------------
# Ajuste apenas o RM se quiser usar o do outro integrante (ex.: 565431).
RM="93624"
LOCATION="brazilsouth"

# Nomes seguindo o padrao de nomenclatura exigido na GS.
RG="rg-dronevision-rm${RM}"
AIV="aiv-dronevision-rm${RM}"
PLAN="plan-dronevision-rm${RM}"
APP="app-dronevision-rm${RM}"

# SKUs: F0 = Vision gratuito | B1 = plano basico (use F1 para plano gratuito).
AIV_SKU="F0"
PLAN_SKU="B1"
RUNTIME="PYTHON:3.11"
# --------------------------------------------------------------------------

echo "==> [1/8] Criando o Resource Group: ${RG}"
az group create --name "${RG}" --location "${LOCATION}" --output table

echo "==> Registrando os provedores necessarios (CognitiveServices e Web)"
az provider register --namespace Microsoft.CognitiveServices --wait
az provider register --namespace Microsoft.Web --wait

echo "==> [2/8] Criando o recurso Azure AI Vision (Computer Vision): ${AIV}"
az cognitiveservices account create \
  --name "${AIV}" \
  --resource-group "${RG}" \
  --kind ComputerVision \
  --sku "${AIV_SKU}" \
  --location "${LOCATION}" \
  --yes \
  --output table

echo "==> [3/8] Obtendo o endpoint e a chave do Azure AI Vision"
VISION_ENDPOINT=$(az cognitiveservices account show \
  --name "${AIV}" --resource-group "${RG}" \
  --query "properties.endpoint" -o tsv)
VISION_KEY=$(az cognitiveservices account keys list \
  --name "${AIV}" --resource-group "${RG}" \
  --query "key1" -o tsv)
echo "    Endpoint: ${VISION_ENDPOINT}"

echo "==> [4/8] Criando o App Service Plan (Linux): ${PLAN}"
az appservice plan create \
  --name "${PLAN}" \
  --resource-group "${RG}" \
  --location "${LOCATION}" \
  --is-linux \
  --sku "${PLAN_SKU}" \
  --output table

echo "==> [5/8] Criando o Web App: ${APP}"
az webapp create \
  --name "${APP}" \
  --resource-group "${RG}" \
  --plan "${PLAN}" \
  --runtime "${RUNTIME}" \
  --output table

echo "==> [6/8] Configurando variaveis de ambiente (chave/endpoint do Vision)"
az webapp config appsettings set \
  --name "${APP}" \
  --resource-group "${RG}" \
  --settings \
     VISION_ENDPOINT="${VISION_ENDPOINT}" \
     VISION_KEY="${VISION_KEY}" \
     VISION_LANGUAGE="en" \
     SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
  --output table

echo "==> [7/8] Definindo o comando de inicializacao (gunicorn)"
az webapp config set \
  --name "${APP}" \
  --resource-group "${RG}" \
  --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 app:app" \
  --output table

echo "==> [8/8] Empacotando e publicando a aplicacao (deploy via Azure CLI)"
rm -f app.zip
zip -r app.zip app.py requirements.txt templates > /dev/null
az webapp deploy \
  --resource-group "${RG}" \
  --name "${APP}" \
  --src-path app.zip \
  --type zip

APP_URL="https://$(az webapp show --name "${APP}" --resource-group "${RG}" --query defaultHostName -o tsv)"
echo ""
echo "=========================================================================="
echo "  Implantacao concluida com sucesso!"
echo "  Acesse a aplicacao em: ${APP_URL}"
echo ""
echo "  Para remover todos os recursos depois da entrega:"
echo "    az group delete --name ${RG} --yes --no-wait"
echo "=========================================================================="
