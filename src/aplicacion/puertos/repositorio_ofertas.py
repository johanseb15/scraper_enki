from typing import Protocol
from src.dominio.oferta import Oferta

class RepositorioOfertas(Protocol):

    def guardar(self, oferta: Oferta) -> None:
        ...