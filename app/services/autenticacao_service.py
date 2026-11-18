"""Regras de autenticação do administrador."""

from __future__ import annotations

from app.extensions import db
from app.models import Administrador


class AutenticacaoService:
    """Valida as credenciais do único administrador do sistema."""

    def autenticar(self, email: str, senha: str) -> Administrador | None:
        """Retorna o administrador ativo quando as credenciais são válidas."""
        email_normalizado = (email or "").strip().lower()
        if not email_normalizado or not senha:
            return None

        administrador = db.session.scalar(
            db.select(Administrador).where(
                db.func.lower(Administrador.email) == email_normalizado
            )
        )
        if administrador is None or not administrador.is_active:
            return None
        if not administrador.verificar_senha(senha):
            return None
        return administrador
