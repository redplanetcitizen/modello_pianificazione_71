# pianificazione71

Modello di programmazione lineare intertemporale per la pianificazione economica a **71 industrie e 73 prodotti**, dati BEA 2012–2016, prezzi 2012.

Codice nuovo. È indipendente da `csvplan.jl` e dal motore LP a 411 commodity (`Documents\Codex\2026-09-08\co`), che restano linee separate con risultati propri e non si attribuiscono a questo modello. Gli identificativi delle esecuzioni di questo repository iniziano con `M71-`, per non confondersi con le linee precedenti (`LP-*-71`, `K2-*-71`).

## Documenti di riferimento

Nel progetto "Creazione di un modello di pianificazione economica":

- `progetto/04_specifica_modello.md` — specifica formale (v0.2.1);
- `progetto/03_registro_decisioni.md` — scelte adottate, approssimazioni del primo test, verifiche aperte;
- `progetto/02_dati_e_fonti.md` — release dei dati e copertura;
- `progetto/05_linee_precedenti.md` — provenienza dei modelli precedenti e confronti previsti.

Al momento della consegna per la revisione le versioni correnti saranno copiate in `docs/`.

## Regole

1. **Dati fuori dal repository.** Il modello legge dall'archivio `dati_economici` e ne verifica le impronte a ogni esecuzione (`config/dati.toml`). Un file non dichiarato in configurazione non si può leggere (`percorso_dati`).
2. **Ogni esecuzione è registrata** in `runs/<data-ora>_<nome>/esecuzione.json`: commit git e modifiche non registrate, versioni di Python e pacchetti, impronta della configurazione, esito della verifica dei dati, parametri, file prodotti con impronte, esito.
3. **Se l'archivio non è integro l'esecuzione non parte.**
4. **Risultati citati nei documenti:** solo da esecuzioni con commit registrato e senza modifiche non registrate.

## Struttura

```
config/dati.toml             release usate, impronte dei manifest, file letti
src/pianificazione71/
  archivio.py                verifica e accesso ai dati
  registro.py                registro delle esecuzioni
  __main__.py                comandi
tests/                       test automatici (archivio di prova, registro, solver)
runs/                        esecuzioni (esclusa da git)
```

## Installazione (Windows, PowerShell)

Dalla cartella del repository:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m pip freeze > requisiti-bloccati.txt
```

`requisiti-bloccati.txt` fissa le versioni esatte usate; va registrato in git.

## Comandi

```powershell
python -m pytest                                  # test automatici
python -m pianificazione71 verifica-dati          # impronte dei manifest e dei file usati
python -m pianificazione71 verifica-dati --completa   # tutti i file di tutte le release (più lenta)
python -m pianificazione71 ambiente               # versioni di Python e pacchetti
python -m pianificazione71 controllo-solver       # LP di prova con HiGHS, registrato in runs/
```

Per usare l'archivio in un'altra posizione: `$env:DATI_ECONOMICI = "D:\percorso\dati_economici"`.

## Stato

| Passo | Contenuto | Stato |
|---|---|---|
| B | Infrastruttura: verifica dei dati, registro, test, solver | fatto |
| C | Pipeline dei dati a 71 industrie | da fare |
| D | Modello | da fare |
| E | Test | da fare |
