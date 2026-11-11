# AI döntési esetek

## 1. Backend és tesztelhető üzleti mag

- Probléma: a pénzügyi szabályokat a bemutatón reprodukálhatóan és külső szolgáltatás nélkül kell ellenőrizni.
- Eszköz: GitHub Copilot.
- Kontextus és utasítás: `SPECIFICATION.md` elfogadási feltételei, különösen az ÁFA, a skontó APR és a likviditási hiány; tiszta Python szolgáltatások és pytest tesztek készítése.
- Döntés: determinisztikus szolgáltatások készültek az agent szerepéhez, mert így a döntési eredmény nem függ hálózattól vagy modellválasztól.
- Ellenőrzés: `backend/tests/test_services.py`, `8 passed`.

## 2. APR megjelenítési pontosság

- Probléma: a specifikáció példája 32,38%-os APR-t vár, míg a normál két tizedesre kerekítés 32,39%-ot ad.
- Eszköz: GitHub Copilot.
- Kontextus és utasítás: a 30/7 napos, 2%-os skontó és 12%-os kamat konkrét elfogadási feltétele.
- Döntés: a megjelenített APR két tizedesre csonkol, a teljes belső számítás változatlan marad; ez követi a megadott példát és az ajánlási összehasonlítást nem torzítja.
- Ellenőrzés: `test_discount_is_recommended_when_apr_beats_credit_rate`.

## 3. Egyszerű, bemutatható felület

- Probléma: a hallgatónak rövid idő alatt kell bemutatnia a számlarögzítést, a cash-flow görbét és az ajánlást.
- Eszköz: GitHub Copilot.
- Kontextus és utasítás: React/Vite frontend, a backend REST API-ja, mobil és desktop használat.
- Döntés: egy vezérlőpult készült összesített kártyákkal, számlalistával, űrlappal és ajánláskártyával; a hibákat és üres állapotot is megjeleníti.
- Ellenőrzés: `npm run build`, valamint a README reprodukálható indítási lépései.