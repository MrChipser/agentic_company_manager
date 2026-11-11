# AI fejlesztési szabályok

- A pénzügyi képletek módosítása előtt vagy azzal együtt célzott unit tesztet kell létrehozni.
- API-változás esetén a backend integrációs tesztjeit és a frontend buildet is futtatni kell.
- Pénzösszegeknél `Decimal` vagy egész HUF használata kötelező; lebegőpontos üzleti számítás nem kerülhet a kódba.
- Az AI által javasolt módosítás csak futtatási eredmény és ember által ellenőrizhető indoklás után tekinthető elfogadottnak.
- A fejlesztési állapotot és a döntési eseteket a `docs/AI_DECISIONS.md` fájlban kell vezetni.