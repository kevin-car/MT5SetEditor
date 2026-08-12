"""Parser/writer pour les fichiers .set de MetaTrader 5.

Un fichier .set contient :
 - des lignes de commentaire commençant par ';'
 - des lignes vides
 - des paramètres simples :  Nom=Valeur
 - des paramètres optimisables : Nom=Valeur||Defaut||Min||Max||Y ou N

Ce module conserve l'ordre et la structure d'origine du fichier (y compris
les commentaires et lignes vides) afin de pouvoir le ré-écrire fidèlement
après modification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CommentLine:
    text: str

    def to_line(self) -> str:
        return self.text


@dataclass
class BlankLine:
    def to_line(self) -> str:
        return ""


@dataclass
class Parameter:
    name: str
    value: str
    default: Optional[str] = None
    min: Optional[str] = None
    max: Optional[str] = None
    optimize: Optional[bool] = None
    optimizable: bool = False  # True si la ligne a le format complet avec ||

    def to_line(self) -> str:
        if self.optimizable:
            flag = "Y" if self.optimize else "N"
            return (
                f"{self.name}={self.value}||{self.default}||"
                f"{self.min}||{self.max}||{flag}"
            )
        return f"{self.name}={self.value}"


Entry = object  # CommentLine | BlankLine | Parameter


class SetFile:
    """Représente un fichier .set chargé, avec ses entrées ordonnées."""

    def __init__(self) -> None:
        self.entries: List[Entry] = []
        # MetaTrader 5 enregistre ses fichiers .set en UTF-16 LE avec BOM.
        # On garde une trace de l'encodage détecté pour le réutiliser à la
        # sauvegarde, mais UTF-16 reste la valeur par défaut.
        self.encoding: str = "utf-16"

    @property
    def parameters(self) -> List[Parameter]:
        return [e for e in self.entries if isinstance(e, Parameter)]

    def get_parameter(self, name: str) -> Optional[Parameter]:
        for p in self.parameters:
            if p.name == name:
                return p
        return None

    @staticmethod
    def _detect_encoding(raw: bytes) -> str:
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            return "utf-16"
        if raw.startswith(b"\xef\xbb\xbf"):
            return "utf-8-sig"
        return "utf-8"

    @classmethod
    def load(cls, path: str) -> "SetFile":
        sf = cls()
        with open(path, "rb") as fb:
            raw = fb.read()
        sf.encoding = cls._detect_encoding(raw)
        text = raw.decode(sf.encoding, errors="replace")
        for raw_line in text.splitlines():
            sf.entries.append(cls._parse_line(raw_line))
        return sf

    @staticmethod
    def _parse_line(raw_line: str) -> Entry:
        line = raw_line.rstrip("\r\n")
        if line.strip() == "":
            return BlankLine()
        if line.lstrip().startswith(";"):
            return CommentLine(line)
        if "=" not in line:
            # ligne non reconnue, conservée comme commentaire pour ne rien perdre
            return CommentLine(line)

        name, rest = line.split("=", 1)
        name = name.strip()

        if "||" in rest:
            parts = rest.split("||")
            if len(parts) == 5:
                value, default, pmin, pmax, flag = parts
                return Parameter(
                    name=name,
                    value=value,
                    default=default,
                    min=pmin,
                    max=pmax,
                    optimize=(flag.strip().upper() == "Y"),
                    optimizable=True,
                )
        return Parameter(name=name, value=rest, optimizable=False)

    def save(self, path: str) -> None:
        lines = [entry.to_line() for entry in self.entries]
        with open(path, "w", encoding=self.encoding, newline="\r\n") as f:
            f.write("\n".join(lines))
            f.write("\n")
