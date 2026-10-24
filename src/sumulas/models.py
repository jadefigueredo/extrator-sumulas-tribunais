from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class DocumentLink:
    """A PDF found on a court's listing page."""

    url: str
    label: str


@dataclass
class Sumula:
    tribunal: str
    numero: int
    enunciado: str
    url_fonte: str
    resolucao: str | None = None
    publicacao: str | None = None
    data_publicacao: str | None = None
    data_aprovacao: str | None = None
    referencias: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
