"""
DroneVision - Aplicacao Web de analise de imagens com Azure AI Vision.

GS 2o Semestre - Cloud Computing & Machine as a Service (MaaS) - FIAP 5EMR
Marcelo Alves da Silva Junior - RM93624
Joao Pedro Leca Ferreira      - RM565431

A aplicacao recebe uma imagem (simulando uma foto capturada por um drone),
envia os bytes da imagem para o servico Azure AI Vision (Computer Vision) e
exibe a descricao textual gerada pela IA, alem das tags e objetos detectados.
"""

import os
import base64

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# Limite de 4 MB por imagem (limite do endpoint Analyze do Azure AI Vision).
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "bmp"}

# Credenciais lidas das variaveis de ambiente (configuradas no App Service
# pelo script de implantacao). Nunca ficam hardcoded no codigo.
VISION_ENDPOINT = os.environ.get("VISION_ENDPOINT", "").rstrip("/")
VISION_KEY = os.environ.get("VISION_KEY", "")
VISION_LANGUAGE = os.environ.get("VISION_LANGUAGE", "en")


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    # 1) Validacao da imagem enviada (requisito 6: imagem invalida).
    file = request.files.get("image")
    if file is None or file.filename == "":
        return render_template(
            "index.html",
            error="Nenhuma imagem foi selecionada. Escolha um arquivo e tente novamente.",
        )
    if not _allowed(file.filename):
        return render_template(
            "index.html",
            error="Formato de imagem invalido. Envie um arquivo .jpg, .png, .gif ou .bmp.",
        )

    image_bytes = file.read()
    if not image_bytes:
        return render_template(
            "index.html",
            error="A imagem enviada esta vazia ou corrompida.",
        )

    # 2) Verifica se o servico esta configurado (requisito 6: indisponibilidade).
    if not VISION_ENDPOINT or not VISION_KEY:
        return render_template(
            "index.html",
            error="Servico de Visao Computacional indisponivel (credenciais nao configuradas).",
        )

    # 3) Chamada ao Azure AI Vision - Computer Vision Analyze Image (v3.2).
    url = f"{VISION_ENDPOINT}/vision/v3.2/analyze"
    params = {
        "visualFeatures": "Description,Tags,Objects",
        "language": VISION_LANGUAGE,
    }
    headers = {
        "Ocp-Apim-Subscription-Key": VISION_KEY,
        "Content-Type": "application/octet-stream",
    }

    try:
        resp = requests.post(url, headers=headers, params=params, data=image_bytes, timeout=30)
    except requests.exceptions.RequestException:
        # Requisito 6: falha de conexao / servico fora do ar.
        return render_template(
            "index.html",
            error="Servico de Visao Computacional indisponivel. Tente novamente em instantes.",
        )

    if resp.status_code != 200:
        # Requisito 6: falha na analise (ex.: imagem nao suportada, chave invalida).
        try:
            msg = resp.json().get("error", {}).get("message", "")
        except ValueError:
            msg = ""
        return render_template(
            "index.html",
            error=f"Falha na analise da imagem (codigo {resp.status_code}). {msg}",
        )

    data = resp.json()

    # 4) Descricao textual da imagem (requisito 4).
    captions = data.get("description", {}).get("captions", [])
    if captions:
        description = captions[0]["text"]
        description_conf = round(captions[0]["confidence"] * 100, 1)
    else:
        description = "Nao foi possivel gerar uma descricao para esta imagem."
        description_conf = None

    # 5) Tags e objetos identificados (requisito 5).
    tags = [
        {"name": t["name"], "confidence": round(t["confidence"] * 100, 1)}
        for t in data.get("tags", [])
    ]
    objects = [
        {"name": o["object"], "confidence": round(o["confidence"] * 100, 1)}
        for o in data.get("objects", [])
    ]

    # Pre-visualizacao da imagem enviada (embutida em base64).
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    mime = file.mimetype or "image/jpeg"
    preview = f"data:{mime};base64,{b64}"

    return render_template(
        "index.html",
        description=description,
        description_conf=description_conf,
        tags=tags,
        objects=objects,
        preview=preview,
    )


@app.errorhandler(413)
def too_large(e):
    # Requisito 6: imagem acima do limite permitido.
    return (
        render_template(
            "index.html",
            error="Imagem muito grande. O tamanho maximo permitido e de 4 MB.",
        ),
        413,
    )


if __name__ == "__main__":
    # Execucao local (desenvolvimento). No Azure, o gunicorn chama "app:app".
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
