# Megvalósítási terv: KKV pénzügyi manager

## 1. Cél és döntések

Az alkalmazás egy kis, bemutatható webalkalmazás KKV-adminisztrátorok számára. A fő üzleti érték a számlákból számított 30 napos cash-flow előrejelzés, az ÁFA-fedezet kimutatása és a beszállítói skontó pénzügyi összehasonlítása.

### Választott technológia

- Backend: Python 3.12+, FastAPI, SQLModel/SQLAlchemy és SQLite.
- Tesztelés: pytest, FastAPI TestClient, külön unit- és integrációs tesztekkel.
- Frontend: React + TypeScript + Vite; a backend REST API-ját használja.
- Adatbázis: fejlesztéshez SQLite fájl, tesztekhez izolált ideiglenes adatbázis.
- Hitelesítés: lokális, determinisztikus bearer tokenes demo-auth; külső identity provider nem szükséges.
- Pénzösszegek: egész HUF-ban vagy `Decimal` értékkel, lebegőpontos számítás nélkül.

Az első verzióban nincs valódi banki vagy külső AI szolgáltatás. Az agent szerepét determinisztikus üzleti szolgáltatás valósítja meg, így a működés tesztelhető és a bemutatón reprodukálható. Külső AI csak akkor kerülhet be, ha későbbi követelmény ezt külön előírja.

## 2. Tervezett projektstruktúra

```text
agentic_company_manager/
  backend/
    app/
      main.py
      config.py
      db.py
      models.py
      schemas.py
      auth.py
      api/
        auth.py
        invoices.py
        forecast.py
        recommendations.py
      services/
        invoice_service.py
        vat_service.py
        cashflow_service.py
        discount_service.py
        agent_service.py
    tests/
      unit/
      integration/
      fixtures.py
    pyproject.toml
  frontend/
    src/
      api/
      components/
      pages/
      types/
      App.tsx
    package.json
  docs/
    AI_DECISIONS.md
    TEST_EVIDENCE.md
    CHANGE_REQUEST.md
  AGENTS.md
  README.md
  SPECIFICATION.md
  IMPLEMENTATION_PLAN.md
```

## 3. Backend megvalósítási sorrend

### 3.1 Adatmodell és validáció

A minimum modellkészlet:

- `User`: azonosító, email, jelszó hash vagy demo-token azonosító, szerepkör.
- `Partner`: név és korábbi számlákból számítható késedelmi adatok.
- `Invoice`: irány (`INCOME`/`EXPENSE`), nettó összeg, ÁFA-kulcs, kiállítási és esedékességi dátum, partner.
- `AccountState`: kezdő egyenleg, hitelkeret, éves hitelkamat és ÁFA-fizetési nap.
- `Recommendation`: típus, státusz, számítási adatok, létrehozás és jóváhagyás állapota.

Pydantic-sémák ellenőrzik, hogy az összeg pozitív, az ÁFA-kulcs az engedélyezett készletből származik, a dátumok értelmesek, és a korai skontóhatáridő kisebb a teljes fizetési határidőnél. Hibás bemenetnél az API 422 választ ad, és a tranzakció nem ment részleges adatot.

### 3.2 Üzleti szolgáltatások

1. `vat_service`: kimenő számlánál a nettó összeg és az ÁFA-kulcs alapján növeli a fizetendő ÁFA-egyenleget; bejövő számlánál levonható ÁFA-ként kezeli.
2. `discount_service`: kiszámítja a skontó megtakarítását és évesített hozamát. A specifikáció szerinti példa legyen rögzített teszt: 30 nap, 7 nap, 2% kedvezmény és 12% hitelkamat esetén az APR körülbelül 32,38%.
3. `cashflow_service`: napi bontásban előállítja a 30 napos egyenlegsort, az adott napi pénzmozgásokkal és a releváns ÁFA-fizetési eseményekkel.
4. `agent_service`: a fenti szolgáltatások eredményét összefoglalja, partnerenként átlagos korábbi késedelmet számít, és akciókártyát készít. A döntés indoka és a bemeneti számok minden ajánlásban láthatók.
5. `recommendation_service`: az ajánlást `RECOMMENDED` vagy `NOT_RECOMMENDED` státusszal hozza létre; az egyenlő APR/kamat és a hitelkeret túllépése mindig nem ajánlott.

Minden pénzügyi számítás tiszta, mellékhatásmentes függvényként készül, hogy unit teszttel és a védésen önállóan is magyarázható legyen.

### 3.3 API és jogosultság

Tervezett végpontok:

- `POST /api/auth/login` - demo felhasználó hitelesítése és token kiadása.
- `POST /api/invoices` - számla rögzítése és a kapcsolódó számítások indítása.
- `GET /api/invoices` - a bejelentkezett felhasználó számlái.
- `GET /api/forecast?days=30` - 30 napos cash-flow előrejelzés és deficitjelzések.
- `GET /api/recommendations` - agent-akciókártyák.
- `POST /api/recommendations/{id}/approve` és `/reject` - ajánlás kezelése.

Minden védett végpont közös auth-függőséget használ. Hiányzó vagy hibás token esetén 401 válasz érkezik; más felhasználó adatai nem kérhetők le az erőforrás-azonosító módosításával.

## 4. Frontend megvalósítás

Az első képernyő a bejelentkezés. Sikeres belépés után egyetlen áttekintő felületen jelenik meg:

- aktuális egyenleg és a 30 napos grafikon;
- a legkorábbi likviditási deficit napja és összege;
- számlák listája, valamint számlarögzítő űrlap;
- ÁFA-fizetési összesítő;
- agent-akciókártyák indoklással, jóváhagyás és elutasítás gombbal.

A frontend csak a backend válaszából jelenít meg pénzügyi eredményt. Betöltési, üres, validációs, 401-es és API-hibaállapotot is kezel. A kliensoldali validáció felhasználói segítség, a végleges szabályokat mindig a backend érvényesíti.

## 5. Teszt- és bizonyítékterv

| Elfogadási feltétel | Automatizált ellenőrzés |
| --- | --- |
| 1. Számla és ÁFA | API integrációs teszt: 1 000 000 Ft, 27%, 200 és 270 000 Ft ÁFA-változás |
| 2. Skontó-ajánlás | Unit teszt: APR közel 32,38%, státusz `RECOMMENDED` |
| 3. Likviditási hiány | Integrációs teszt: negatív napi egyenleg, kód és pontos hiány |
| 4. Küszöb és hitelkeret | Unit tesztek: egyenlő kamat és kerettúllépés, `NOT_RECOMMENDED` |
| 5. ÁFA-határnap | Cash-flow unit teszt: hó 20-i bevétel aznapi fedezetbe kerül |
| 6. Hibás számla | API tesztek: összeg, ÁFA-kulcs, skontó-dátum; 422 és változatlan DB |
| 7. Jogosulatlan művelet | API tesztek: token nélkül 401 számlarögzítés és jóváhagyás |

A tesztcsomag ezen felül tartalmaz:

- legalább egy normál esetet, két határesetet, egy jogosulatlan/hibás esetet és egy regressziós esetet;
- izolált adatbázis-fixture-t, hogy a futások sorrendje ne számítson;
- egy reprodukálható mutation/regression bizonyítékot: a skontó-feltétel szándékosan hibás változatán a teszt bukik, a javított változaton átmegy;
- `TEST_EVIDENCE.md` dokumentumot a parancsokkal, futási eredménnyel, hibás és javított változattal.

Ajánlott parancsok:

```text
cd backend && pytest -q
cd frontend && npm test
cd frontend && npm run build
```

## 6. AI által végzett implementációs munkafolyamat

Az implementációt az AI végzi, de minden létrehozott kódot futtatással és célzott tesztekkel kell ellenőrizni. A hallgató feladata a döntések megértése, a specifikáció jóváhagyása és a védésre való felkészülés.

### Fázisok

1. **Követelményelemzés:** az AI a `SPECIFICATION.md` alapján létrehozza az adatmodellt, API-szerződést és tesztmátrixot. A hallgató ellenőrzi, hogy minden elfogadási feltétel mérhető.
2. **Backend implementáció:** az AI először a tiszta számítási szolgáltatásokat és unit teszteket írja meg, majd az adatbázist és az API-t. Minden kisebb módosítás után célzott teszt fut.
3. **Frontend implementáció:** az AI az API-szerződésből építi fel a képernyőket, majd builddel és kézi reprodukciós lépésekkel ellenőrzi őket.
4. **Hibafeltárás:** az AI létrehozza a szándékosan hibás skontóváltozatot, rögzíti a bukó futást, visszaállítja a javított logikát és rögzíti a sikeres futást.
5. **Változtatási igény:** az oktatói módosítás kézhezvételekor az AI először hatásvizsgálatot és új tesztet készít, ezután módosítja a legkisebb szükséges kódrészt, végül futtatja a teljes regressziós csomagot.

Minden AI-döntési esetet a `docs/AI_DECISIONS.md` rögzít: probléma, használt eszköz/modell, átadott kontextus és utasítás, javaslat, saját döntés, ellenőrzés és korlát.

## 7. Mérföldkövek és git-stratégia

### Első működő verzió

- `milestone/working-version` ág vagy tag;
- backend, frontend, alap adatmodell és fő használati folyamat;
- elfogadási feltételek 1-3 működő tesztekkel;
- README indítási és tesztfuttatási útmutató.

### Végleges verzió

- az első verzióból kiinduló külön változtatási commit;
- az oktatói igényhez tartozó új teszt előbb, implementáció utána;
- korábbi tesztek és adatmegőrzés ellenőrzése;
- frissített specifikáció, `CHANGE_REQUEST.md`, AI-döntési esetek és teszteredmények.

## 8. Bemutatási forgatókönyv

1. Bejelentkezés demo-adminnal.
2. 1 000 000 Ft nettó, 27%-os kimenő számla rögzítése és a 270 000 Ft ÁFA megmutatása.
3. Skontós bejövő számla rögzítése, az APR és az ajánláskártya megtekintése.
4. 30 napos grafikonon a deficitnap és a hiány összegének megmutatása.
5. Hibás számlaadat és token nélküli kérés bemutatása.
6. Egy kijelölt teszt futtatása, majd a tesztelt kódrészlet bemutatása és várható eredményének magyarázata.
7. Az első és a végleges verzió, a változtatási igény és a regressziós bizonyíték összehasonlítása.

## 9. Kockázatok és korlátok

- A pénzügyi képletek jelentik a legnagyobb üzleti kockázatot; ezért minden képletnek külön példatesztje és kerekítési szabálya lesz.
- A demo-auth nem production biztonsági megoldás; ezt a README egyértelműen jelzi.
- Az AI agent külső szolgáltatás nélkül determinisztikus szabálymotor; a specifikációban szereplő agent-szerepet és ajánlási folyamatot így biztosítja.
- A hónapváltás és a 20-i ÁFA-határidő teszteléséhez rögzített dátum-fixture-ek szükségesek.
- A védésen az AI nem magyarázhat a hallgató helyett; a hallgatónak ismernie kell a saját kódjának adatfolyamát és döntési szabályait.