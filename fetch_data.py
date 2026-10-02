"""Cierre S&P 500, PER y bono 10Y -> data.json ; rentabilidades por periodos -> returns.json"""
import json, pathlib
import pandas as pd
import yfinance as yf

FILE = pathlib.Path("data.json")
HIST = pathlib.Path("history.json")


def ultimo(ticker):
    s = yf.Ticker(ticker).history(period="7d")["Close"].dropna()
    return s.index[-1].date().isoformat(), float(s.iloc[-1])


def cpi_en(rows, ym):
    ok = [r for r in rows if r.get("cpi") and r["date"] <= ym]
    return ok[-1]["cpi"] if ok else None


def rentabilidades(dia):
    h = yf.Ticker("^GSPC").history(period="max")["Close"].dropna()
    h.index = pd.to_datetime(h.index.date)
    fin = pd.Timestamp(dia)
    rows = json.loads(HIST.read_text()) if HIST.exists() else []
    cpi_fin = cpi_en(rows, dia[:7])
    p_fin = float(h.loc[:fin].iloc[-1])
    periodos = [("En el año (YTD)", pd.Timestamp(fin.year - 1, 12, 31), None),
                ("1 año", fin - pd.DateOffset(years=1), None),
                ("5 años", fin - pd.DateOffset(years=5), 5),
                ("10 años", fin - pd.DateOffset(years=10), 10)]
    out = []
    for nombre, ini, n in periodos:
        nom = p_fin / float(h.loc[:ini].iloc[-1]) - 1
        c_ini = cpi_en(rows, ini.strftime("%Y-%m"))
        real = (1 + nom) * c_ini / cpi_fin - 1 if c_ini and cpi_fin else None
        fila = {"n": nombre, "nom": round(nom * 100, 2),
                "real": None if real is None else round(real * 100, 2)}
        if n:
            fila["ann_nom"] = round(((1 + nom) ** (1 / n) - 1) * 100, 2)
            if real is not None:
                fila["ann_real"] = round(((1 + real) ** (1 / n) - 1) * 100, 2)
        out.append(fila)
    return {"date": dia, "periodos": out}


def main():
    dia, cierre = ultimo("^GSPC")
    _, bono = ultimo("^TNX")            # ya viene en %, p. ej. 4.15
    eps = None
    if HIST.exists():                    # EPS "as reported" 12 meses (Shiller), como multpl
        eps = json.loads(HIST.read_text())[-1]["eps"]
    if eps:
        per = cierre / eps
    else:                                # alternativa: PER de SPY vía Yahoo
        info = yf.Ticker("SPY").info
        per = info.get("trailingPE") or info.get("forwardPE")
    if not per:
        raise SystemExit("No hay PER hoy")
    ey = 100 / per                       # earnings yield en %
    fila = {"date": dia, "close": round(cierre, 2), "per": round(per, 2), "eps": round(cierre / per, 2),
            "ey": round(ey, 2), "us10y": round(bono, 2), "erp": round(ey - bono, 2)}
    hist = json.loads(FILE.read_text()) if FILE.exists() else []
    hist = [h for h in hist if h["date"] != dia] + [fila]
    FILE.write_text(json.dumps(hist[-500:], indent=1))
    print(fila)
    try:
        r = rentabilidades(dia)
        pathlib.Path("returns.json").write_text(json.dumps(r, ensure_ascii=False, indent=1))
        print(r)
    except Exception as e:
        print("No se pudieron calcular las rentabilidades:", e)


if __name__ == "__main__":
    main()
