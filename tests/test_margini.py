from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from pianificazione71.margini import investimento_per_industria_io, leggi_concordanza

CONC = Path(__file__).resolve().parents[1] / "config" / "concordanza_fa_io.csv"
INDUSTRIE_IO = ["111CA", "113FF", "211", "212", "213", "22", "23", "321", "327", "331", "332", "333", "334", "335",
                "3361MV", "3364OT", "337", "339", "311FT", "313TT", "315AL", "322", "323", "324", "325", "326", "42",
                "441", "445", "452", "4A0", "481", "482", "483", "484", "485", "486", "487OS", "493", "511", "512",
                "513", "514", "521CI", "523", "524", "525", "HS", "ORE", "532RL", "5411", "5415", "5412OP", "55",
                "561", "562", "61", "621", "622", "623", "624", "711AS", "713", "721", "722", "81", "GFGD", "GFGN",
                "GFE", "GSLG", "GSLE"]


def test_concordanza_completa():
    c = leggi_concordanza(CONC)
    assert len(c) == 74 and c["industria_fa"].is_unique
    assert set(c["industria_io"]) <= set(INDUSTRIE_IO)
    # le industrie I/O senza investimento privato non residenziale FA: abitazioni (residenziale) e pubbliche
    assert set(INDUSTRIE_IO) - set(c["industria_io"]) == {"HS", "GFGD", "GFGN", "GFE", "GSLG", "GSLE"}


def test_aggregazione_conserva_i_totali():
    fa = pd.DataFrame({"industria_fa": ["2211", "2212", "2211", "3380", "3390"], "bene": ["EQ00", "EQ00", "ST00", "IP00", "IP00"],
                       "anno": 2012, "valore": [10.0, 5.0, 7.0, 1.0, 2.0]})
    conc = pd.DataFrame({"industria_fa": ["2211", "2212", "3380", "3390"], "industria_io": ["22", "22", "339", "339"]})
    io = investimento_per_industria_io(fa, conc)
    assert io["valore"].sum() == pytest.approx(fa["valore"].sum())
    assert io.set_index(["industria_io", "tipo"]).loc[("22", "E"), "valore"] == 15.0


def test_industria_fa_non_mappata():
    fa = pd.DataFrame({"industria_fa": ["9999"], "bene": ["EQ00"], "anno": 2012, "valore": [1.0]})
    with pytest.raises(ValueError, match="senza corrispondenza"):
        investimento_per_industria_io(fa, pd.DataFrame({"industria_fa": ["2211"], "industria_io": ["22"]}))
