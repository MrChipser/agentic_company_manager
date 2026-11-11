# Első működő verzió tesztbizonyítéka

## Futtatás

```bash
cd backend
.venv/bin/pytest -q
```

Eredmény: `8 passed`.

## Lefedett esetek

- Normál: 1 000 000 Ft nettó kimenő számla 27% ÁFA-val, 270 000 Ft számított ÁFA.
- Normál: 2% skontó 7 nappal korábban, 32,38% APR és `RECOMMENDED` státusz.
- Normál: negatív cash-flow egyenleg és a hiány pontos összege.
- Határeset: hitelkamatot el nem érő APR és hitelkeret-túllépés.
- Hibás: nulla összegű számla 422 válasszal, változatlan adatbázissal.
- Jogosultság: token nélküli számlarögzítés 401 válasszal.

## Ismert következő lépés

A változtatási igény az első verzió beadása után kerül átvezetésre; addig az eredeti állapotot a git mérföldkő/tag rögzíti.