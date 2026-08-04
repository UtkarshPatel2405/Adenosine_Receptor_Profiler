"""Canonical SMILES registry for barcode lookup and deduplication."""
from src.chem_utils import canonicalize

class SmilesRegistry:
    def __init__(self):
        self._cache = {}

    def get_canonical(self, smiles: str) -> str | None:
        if smiles not in self._cache:
            self._cache[smiles] = canonicalize(smiles)
        return self._cache[smiles]

    def register(self, smiles: str) -> tuple[str | None, bool]:
        is_new = smiles not in self._cache
        canon = self.get_canonical(smiles)
        return canon, is_new

    def save(self) -> None:
        pass

    def __len__(self) -> int:
        return len(self._cache)
