"""Armazenamento local das imagens enviadas para os cursos."""

from __future__ import annotations

import uuid
from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

_ASSINATURAS = (
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpg"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
)


class UploadImagemService:
    """Salva e remove imagens na pasta estática configurada."""

    def salvar(self, arquivo: FileStorage) -> str:
        extensao_original = self._extensao_original(arquivo)
        if extensao_original not in current_app.config["UPLOAD_EXTENSOES_IMAGEM"]:
            raise ValueError("Envie uma imagem PNG, JPG, GIF ou WebP.")

        extensao = self._detectar_extensao(arquivo)
        nome = f"{uuid.uuid4().hex}.{extensao}"
        destino = self._pasta() / nome
        arquivo.stream.seek(0)
        arquivo.save(str(destino))

        return f"{current_app.config['UPLOAD_URL_PREFIX']}{nome}"

    def remover(self, imagem_url: str | None) -> None:
        prefixo = str(current_app.config["UPLOAD_URL_PREFIX"])
        if not imagem_url or not imagem_url.startswith(prefixo):
            return

        nome = imagem_url[len(prefixo) :]
        if not nome or "/" in nome or "\\" in nome or ".." in nome:
            return

        caminho = self._pasta() / nome
        if caminho.is_file():
            caminho.unlink()

    @staticmethod
    def _pasta() -> Path:
        pasta = Path(current_app.config["UPLOAD_FOLDER"])
        pasta.mkdir(parents=True, exist_ok=True)
        return pasta

    @staticmethod
    def _extensao_original(arquivo: FileStorage) -> str:
        nome = secure_filename(arquivo.filename or "")
        return nome.rsplit(".", 1)[-1].lower() if "." in nome else ""

    @staticmethod
    def _detectar_extensao(arquivo: FileStorage) -> str:
        arquivo.stream.seek(0, 2)
        tamanho = arquivo.stream.tell()
        arquivo.stream.seek(0)

        if tamanho == 0:
            raise ValueError("O arquivo enviado está vazio.")
        limite = int(
            current_app.config.get("MAX_CONTENT_LENGTH", 4 * 1024 * 1024)
        )
        if tamanho > limite:
            raise ValueError("A imagem deve ter no máximo 4 MB.")

        cabecalho = arquivo.stream.read(12)
        arquivo.stream.seek(0)

        for assinatura, extensao in _ASSINATURAS:
            if cabecalho.startswith(assinatura):
                return extensao
        if cabecalho[:4] == b"RIFF" and cabecalho[8:12] == b"WEBP":
            return "webp"

        raise ValueError("O arquivo enviado não é uma imagem válida.")
