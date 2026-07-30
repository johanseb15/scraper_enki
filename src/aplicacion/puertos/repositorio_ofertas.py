from typing import Protocol, List
from src.dominio.oferta import Oferta


class RepositorioOfertas(Protocol):

    def guardar(self, oferta: Oferta) -> None:
        ...

    def obtener_todas(self) -> List[Oferta]:
        ...