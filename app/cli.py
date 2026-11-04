"""Comandos de linha de comando (flask ...)."""

import click
from flask import Flask


def register_cli(app: Flask) -> None:
    @app.cli.command("seed")
    def seed_command() -> None:
        """Popula um banco vazio com dados fictícios (só fora de produção)."""
        if not app.config.get("SEED_ALLOWED"):
            raise click.ClickException("O seed não roda em produção.")
        from app.seed import SeedError, seed_demo

        try:
            summary = seed_demo()
        except SeedError as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo(
            f"Pronto: {summary.years} anos, {summary.classes} shiurim, {summary.students} alunos, "
            f"{summary.assessments} provas, {summary.scores} notas."
        )
        for note in summary.notes:
            click.echo(note)
