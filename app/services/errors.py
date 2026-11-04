"""Erros de regra de negócio. A mensagem vai direto para a tela: diz o que fazer, sem desculpas."""


class DomainError(Exception):
    """Ação não permitida pelas regras do sistema."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationError(DomainError):
    """Dado inválido (ex: nota fora da escala)."""


class LockedError(DomainError):
    """Trimestre travado, shiur liberado ou ano arquivado."""


class PermissionDenied(DomainError):
    """O usuário não pode fazer esta ação."""


class ConflictError(DomainError):
    """A ação conflita com o estado atual (ex: já existe um ano ativo)."""
