"""Histórico mensual (Shiller): precio, EPS, PER, earnings yield, bono 10a y ERP -> history.json"""
import io, json, pathlib, sys
import pandas as pd
import requests

OUT = pathlib.Path("history.json")
URLS = ["http://www.econ.yale.edu/~shiller/data/ie_data.xls"]
LOCAL = ["ie_data.xls", "ie_data.xlsx"]   # alternativa: súbelo tú al repositorio


def obtener():
    for u in URLS:
        try:
            r = requests.get(u, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
            if r.ok and len(r.content) > 100_000:
                print("Descargado de", u)
                return r.content
        except Exception as e:
            print("Fallo", u, e)
    for n in LOCAL:
        if pathlib.Path(n).exists():
            print("Usando archivo local", n)
            return pathlib.Path(n).read_bytes()
    return None


def main():
    raw = obtener()
    if raw is None:
        print("No se pudo obtener el Excel de Shiller.")
        sys.exit(0 if OUT.exists() else 1)
    df = pd.read_excel(io.BytesIO(raw), sheet_name="Data", header=None)
    i = df.index[df[0].astype(str).str.strip().eq("Date")][0]
    d = df.iloc[i + 1:, [0, 1, 3, 6]].apply(pd.to_numeric, errors="coerce")
    d.columns = ["date", "p", "e", "rf"]
    d = d.dropna()
    rows = []
    for x in d.itertuples():
        y = int(x.date); m = int(round((x.date - y) * 100))
        if not 1 <= m <= 12 or x.e <= 0:
            continue
        ey = 100 * x.e / x.p
        rows.append({"date": f"{y}-{m:02d}", "close": round(x.p, 2), "eps": round(x.e, 2),
                     "per": round(x.p / x.e, 2), "ey": round(ey, 2),
                     "us10y": round(x.rf, 2), "erp": round(ey - x.rf, 2)})
    OUT.write_text(json.dumps(rows))
    print(len(rows), "meses; último:", rows[-1]["date"])


main()
