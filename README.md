# Cashline - KKV pénzügyi manager

Az első működő verzió KKV-k számláiból készít 30 napos cash-flow előrejelzést, ÁFA-egyenleget és skontó-ajánlást. Az alkalmazás lokális SQLite adatbázist és determinisztikus, külső szolgáltatás nélküli agent-szabályokat használ.

## Indítás

Backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Frontend külön terminálban:

```bash
cd frontend
npm install
npm run dev
```

Nyisd meg a Vite által jelzett címet. Demo belépés: `admin@demo.hu` / `admin`.

## Ellenőrzés

```bash
cd backend && .venv/bin/pytest -q
cd frontend && npm run build
```

Az első verzió az elfogadási feltételek 1-3 fő útvonalát, valamint a 4-7 határ- és hibás eseteinek backend alapját tartalmazza. A demo-auth kizárólag oktatási bemutatóhoz készült.