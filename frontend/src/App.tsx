import { FormEvent, useEffect, useState } from "react";

type Recommendation = { status: string; apr: string; saving: string; reason: string } | null;
type Invoice = { id: number; direction: string; amount: string; vat_rate: number; vat_amount: string; due_date: string; partner_name: string };
type Forecast = { days: { date: string; balance: string; deficit: string }[]; status: string; deficit: string };

const api = async (path: string, options: RequestInit = {}, token = "") => {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers }
  });
  if (!response.ok) throw new Error((await response.json()).detail ?? "A kérés sikertelen.");
  return response.json();
};

function formatHuf(value: string) {
  return `${Number(value).toLocaleString("hu-HU")} Ft`;
}

export function App() {
  const [token, setToken] = useState("");
  const [email, setEmail] = useState("admin@demo.hu");
  const [password, setPassword] = useState("admin");
  const [error, setError] = useState("");
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [recommendation, setRecommendation] = useState<Recommendation>(null);
  const [form, setForm] = useState({ direction: "OUTGOING", amount: "1000000", vat_rate: "27", issue_date: new Date().toISOString().slice(0, 10), due_date: new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10), partner_name: "Demo partner", discount_days: "", discount_rate: "" });

  const refresh = async (activeToken = token) => {
    const [invoiceData, forecastData] = await Promise.all([api("/api/invoices", {}, activeToken), api("/api/forecast", {}, activeToken)]);
    setInvoices(invoiceData);
    setForecast(forecastData);
  };

  useEffect(() => { if (token) refresh().catch((cause: Error) => setError(cause.message)); }, [token]);

  const login = async (event: FormEvent) => {
    event.preventDefault();
    try { setError(""); const result = await api("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }); setToken(result.access_token); }
    catch (cause) { setError((cause as Error).message); }
  };

  const addInvoice = async (event: FormEvent) => {
    event.preventDefault();
    try {
      setError("");
      const result = await api("/api/invoices", { method: "POST", body: JSON.stringify({ ...form, amount: form.amount, vat_rate: Number(form.vat_rate), due_date: form.due_date || form.issue_date, discount_days: form.discount_days ? Number(form.discount_days) : null, discount_rate: form.discount_rate || null }) }, token);
      setRecommendation(result.recommendation); await refresh();
    } catch (cause) { setError((cause as Error).message); }
  };

  if (!token) return <main className="login-shell"><section className="login-panel"><p className="eyebrow">CASHLINE / 01</p><h1>Legyen látható, mi jön a következő 30 napban.</h1><p className="muted">KKV pénzügyi áttekintő számlákhoz, ÁFA-fedezethez és döntéstámogató ajánlásokhoz.</p><form onSubmit={login}><label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} /></label><label>Jelszó<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label><button type="submit">Belépés <span>→</span></button></form>{error && <p className="error">{error}</p>}<p className="hint">Demo hozzáférés: admin@demo.hu / admin</p></section><aside className="login-aside"><span>30 nap</span><strong>pénzügyi<br />előrelátás</strong><p>Az adatok helyben, determinisztikus szabályokkal számolódnak.</p></aside></main>;

  const lowestBalance = forecast?.days.reduce((lowest, point) => Number(point.balance) < Number(lowest.balance) ? point : lowest, forecast.days[0]);
  return <main className="app-shell"><header className="topbar"><div><p className="eyebrow">CASHLINE / VEZÉRLŐPULT</p><h1>Jó reggelt, admin.</h1></div><button className="quiet-button" onClick={() => setToken("")}>Kilépés</button></header><section className="summary-grid"><article className="summary-card dark"><span>30 napos státusz</span><strong>{forecast?.status === "LIQUIDITY_DEFICIT" ? "Figyelmet kér" : "Stabil pálya"}</strong><small>{forecast?.status === "LIQUIDITY_DEFICIT" ? `Legnagyobb hiány: ${formatHuf(forecast.deficit)}` : "Nincs jelzett likviditási hiány"}</small></article><article className="summary-card"><span>Legkisebb egyenleg</span><strong>{lowestBalance ? formatHuf(lowestBalance.balance) : "..."}</strong><small>{lowestBalance?.date ?? "Előkészítés alatt"}</small></article><article className="summary-card accent"><span>Rögzített számlák</span><strong>{invoices.length}</strong><small>Helyi adatbázisban</small></article></section><section className="content-grid"><div className="main-column"><article className="panel forecast-panel"><div className="panel-heading"><div><p className="eyebrow">ELŐREJELZÉS</p><h2>Cash-flow pálya</h2></div><span className="badge">{forecast?.days.length ?? 0} nap</span></div><div className="chart">{forecast?.days.map((point) => <div className={`bar ${Number(point.balance) < 0 ? "negative" : ""}`} style={{ height: `${Math.min(100, Math.max(12, Math.abs(Number(point.balance)) / 25000))}%` }} title={`${point.date}: ${formatHuf(point.balance)}`} key={point.date} />)}</div><div className="chart-labels"><span>ma</span><span>+15 nap</span><span>+30 nap</span></div></article><article className="panel"><div className="panel-heading"><div><p className="eyebrow">NAPLÓ</p><h2>Legutóbbi számlák</h2></div></div>{invoices.length === 0 ? <p className="muted">Még nincs rögzített számla.</p> : <div className="invoice-list">{invoices.map((invoice) => <div className="invoice-row" key={invoice.id}><span className={`direction ${invoice.direction === "OUTGOING" ? "out" : "in"}`}>{invoice.direction === "OUTGOING" ? "Kimenő" : "Bejövő"}</span><div><strong>{invoice.partner_name}</strong><small>Esedékes: {invoice.due_date}</small></div><strong>{formatHuf(invoice.amount)}</strong></div>)}</div>}</article></div><aside className="side-column"><article className="panel form-panel"><p className="eyebrow">ÚJ TÉTEL</p><h2>Számla rögzítése</h2><form onSubmit={addInvoice}><div className="form-row"><label>Irány<select value={form.direction} onChange={(event) => setForm({ ...form, direction: event.target.value })}><option value="OUTGOING">Kimenő</option><option value="INCOMING">Bejövő</option></select></label><label>Nettó összeg<input type="number" min="1" value={form.amount} onChange={(event) => setForm({ ...form, amount: event.target.value })} /></label></div><label>Partner<input value={form.partner_name} onChange={(event) => setForm({ ...form, partner_name: event.target.value })} /></label><div className="form-row"><label>ÁFA-kulcs<select value={form.vat_rate} onChange={(event) => setForm({ ...form, vat_rate: event.target.value })}><option>27</option><option>18</option><option>5</option><option>0</option></select></label><label>Esedékesség<input type="date" value={form.due_date} onChange={(event) => setForm({ ...form, due_date: event.target.value })} /></label></div><details><summary>Skontó beállítások</summary><div className="form-row"><label>Korai nap<input type="number" min="0" value={form.discount_days} onChange={(event) => setForm({ ...form, discount_days: event.target.value })} /></label><label>Kedvezmény %<input type="number" min="0" step="0.01" value={form.discount_rate} onChange={(event) => setForm({ ...form, discount_rate: event.target.value })} /></label></div></details><button type="submit">Mentés és elemzés <span>↗</span></button></form>{error && <p className="error">{error}</p>}</article>{recommendation && <article className={`panel recommendation ${recommendation.status === "RECOMMENDED" ? "good" : "warn"}`}><p className="eyebrow">AGENT AJÁNLÁSA</p><h2>{recommendation.status === "RECOMMENDED" ? "Érdemes megfontolni" : "Most ne gyorsíts"}</h2><strong>{recommendation.apr}% APR</strong><p>{recommendation.reason}</p><small>Számított megtakarítás: {formatHuf(recommendation.saving)}</small></article>}</aside></section></main>;
}