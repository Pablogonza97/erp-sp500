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
    eps = None
    hist_f = pathlib.Path("history.json")
    if hist_f.exists():                  # EPS "as reported" 12 meses (Shiller), como multpl
        eps = json.loads(hist_f.read_text())[-1]["eps"]
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

main()
