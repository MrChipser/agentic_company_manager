# Házi feladat specifikáció (Bodor Dávid, E73GP8): KKV pénzügyi manager

## Cél és architektúra
A Gránit Bank Agentic AI ötletpályázatának alapjául készített webalkalmazás, amely KKV-knak nyújt 30 napos cash-flow szimulációt, ÁFA-kalkulációt és beszállítói korai fizetési kedvezmény (skontó) arbitrázs-számítást.
* **Backend:** Python (FastAPI) + SQLite/PostgreSQL, különböző pénzügyi algoritmusok és AI agent.
* **Frontend:** Webes UI (Streamlit/React) a görbék, számlák és az agent által ajánlott akciókártyák kezelésére.

## Szerepkörök és forgatókönyvek
* **KKV adminisztrátor (Bejelentkezett):** Számlákat (kimenő/bejövő) rögzít, megtekinti a 30 napos egyenleg-előrejelzést, jóváhagyja vagy elutasítja az optimalizációs javaslatokat.
* **AI Agent:** Új számlánál megbecsüli a partner fizetési késését, ellenőrzi a havi ÁFA-fedezetet, számítja a skontó APR-ét, és akciókártyákat generál.
* **Vendég (Nincs bejelntkezve):** Csak a bejelentkező felületet éri el, a védett API-khoz nem fér hozzá.

## Elfogadási feltételek és ellenőrzések
1. **Számlarögzítés és ÁFA-számítás (Normál eset):** 1 000 000 Ft nettó, 27% ÁFA-s kimenő számla rögzítésekor a backend elmenti az adatot (200 OK), és a fizetendő ÁFA egyenleget 270 000 Ft-tal növeli. (Automata API/egységteszt)
2. **Skontó-arbitrázs (Normál eset):** 30 napos fizetési határidő, 7 napon belül 2% skontó (APR ≈ 32,38%) és 12% hitelkamat esetén a motor RECOMMENDED/AJÁNLOTT skontó-akciót generál (APR > 12%). (Automata egységteszt)
3. **Likviditási hiány észlelése (Normál eset):** Ha a 30 napos szimulációban a napi várható egyenleg 0 Ft alá esik, a rendszer LIQUIDITY_DEFICIT/LIKVIDITÁSI_HIÁNY jelzést és a pontos hiányt adja vissza. (Automatizált integrációs teszt)
4. **Skontó kamat-küszöbértéknél (Határeset):** Ha APR == hitelkamat (0 Ft nyereség), vagy a kifizetés túllépné a hitelkeretet, a rendszer NOT_RECOMMENDED/NEM_AJÁNLOTT státuszt ad. (Automatizált egységteszt)
5. **ÁFA-határidő napján beérkező bevétel (Határeset):** A pontosan hó 20-án beérkező bevételt a szimuláció még beszámítja az aznapi ÁFA-fizetés fedezetébe. (Automatizált egységteszt)
6. **Érvénytelen számlaadatok (Hibás eset):** <= 0 összeg, érvénytelen ÁFA-kulcs (csak bizonyos %-ok engedélyezettek) vagy T_korai >= T_teljes skontó határidő esetén 422 Unprocessable Entity hibát ad, az adatbázis nem változik. (Automatizált API teszt)
7. **Jogosulatlan hozzáférés (Hibás eset):** Token nélküli számlarögzítést vagy jóváhagyást a backend 401 Unauthorized kóddal elutasít. (Automatizált API teszt)

## 4. Bizonytalanságok és feloldásuk
* **Külső API-k:** Rendes banki kapcsolat helyett helyi adatbázisban tárolt (és UI-on bővíthető) számlákkal és szimulált egyenleggel működik.
* **Késedelem-predikció determinizmusa:** A partner várható késése a korábbi számláinak átlagos késedelme, új partnernél 0 nap.
* **Deviza és naptár:** Csak HUF-ot kezel, 365 napos naptári évvel, eltolások nélkül.
