"""Descarga cierre S&P 500, PER y bono 10Y y añade una fila a data.json."""
import json, pathlib
import yfinance as yf

FILE = pathlib.Path("data.json")

def ultimo(ticker):
    s = yf.Ticker(ticker).history(period="7d")["Close"].dropna()
    return s.index[-1].date().isoformat(), float(s.iloc[-1])

def main():
    dia, cierre = ultimo("^GSPC")
    _, bono = ultimo("^TNX")            # ya viene en %, p. ej. 4.15
    info = yf.Ticker("SPY").info         # PER del S&P 500 vía SPY (proxy)
    per = info.get("trailingPE") or info.get("forwardPE")
    if not per:
        raise SystemExit("Yahoo no devolvió PER hoy")
    ey = 100 / per                       # earnings yield en %
    fila = {"date": dia, "close": round(cierre, 2), "per": round(per, 2), "eps": round(cierre / per, 2),
            "ey": round(ey, 2), "us10y": round(bono, 2), "erp": round(ey - bono, 2)}
    hist = json.loads(FILE.read_text()) if FILE.exists() else []
    hist = [h for h in hist if h["date"] != dia] + [fila]
    FILE.write_text(json.dumps(hist[-500:], indent=1))
    print(fila)

main()
