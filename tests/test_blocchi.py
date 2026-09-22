from __future__ import annotations

from pianificazione71.blocchi import COMPARTI, FTE_RIGHE, industrie_comparto
from tests.test_margini import INDUSTRIE_IO


def test_fte_copre_tutte_le_industrie_tranne_abitazioni():
    assert set(INDUSTRIE_IO) - set(FTE_RIGHE.values()) == {"HS"}
    assert len(set(FTE_RIGHE.values())) == len(FTE_RIGHE)


def test_comparti_scorte_partizione_delle_industrie_private():
    private = [j for j in INDUSTRIE_IO if not j.startswith("G")]
    viste = []
    for riga in COMPARTI:
        if riga == 9:  # ingrosso non durevole: stessa industria dell'ingrosso durevole
            continue
        viste += industrie_comparto(riga, private)
    assert sorted(viste) == sorted(private)
