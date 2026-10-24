from sumulas.tribunais.base import Tribunal
from sumulas.tribunais.tjpa import TJPA
from sumulas.tribunais.trepa import TREPA

TRIBUNAIS: dict[str, Tribunal] = {t.slug: t for t in (TJPA(), TREPA())}

__all__ = ["TRIBUNAIS", "Tribunal"]
