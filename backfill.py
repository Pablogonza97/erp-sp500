"""Histórico mensual (Shiller): precio, EPS, PER, earnings yield, bono 10a y ERP -> history.json"""
import io, json, pathlib, re, sys
import pandas as pd
import requests

OUT = pathlib.Path("history.json")
UA = {"User-Agent": "Mozilla/5.0"}
WEB = "https://shillerdata.com/"
ENLACE_CONOCIDO = ("https://img1.wsimg.com/blobby/go/e5e77e0b-59d1-44d9-ab25-4763ac982e53/"
                   "downloads/70fec4f5-727f-4e53-b5f1-179af109c5fa/ie_data.xls")
YALE = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"   # versión antigua, se quedó en 2023
LOCAL = ["ie_data.xls", "ie_data.xlsx"]                        # alternativa: súbelo tú al repositorio


def parsear(raw):
    df = pd.read_excel(io.BytesIO(raw), sheet_name="Data", header=None)
    i = df.index[df[0].astype(str).str.strip().eq("Date")][0]
    d = df.iloc[i + 1:, [0, 1, 3, 6]].apply(pd.to_numeric, errors="coerce")
    d.columns = ["date", "p", "e", "rf"]
    rows = []
    for x in d.dropna().itertuples():
        y = int(x.date); m = int(round((x.date - y) * 100))
        if not 1 <= m <= 12 or x.e <= 0:
            continue
        ey = 100 * x.e / x.p
        rows.append({"date": f"{y}-{m:02d}", "close": round(x.p, 2), "eps": round(x.e, 2),
                     "per": round(x.p / x.e, 2), "ey": round(ey, 2),
                     "us10y": round(x.rf, 2), "erp": round(ey - x.rf, 2)})
    return rows


def candidatos():
    urls = []
    try:   # enlace actual publicado en shillerdata.com
        html = requests.get(WEB, timeout=60, headers=UA).text.replace("&amp;", "&")
        urls += re.findall(r'https://img1\.wsimg\.com/blobby/go/[^"\'\s)\\]*?ie_data\.xls[^"\'\s)\\]*', html)
    except Exception as e:
        print("No se pudo leer shillerdata.com:", e)
    urls += [ENLACE_CONOCIDO, YALE]
    for u in dict.fromkeys(urls):
        try:
            r = requests.get(u, timeout=90, headers=UA)
            if r.ok and len(r.content) > 100_000:
                yield u, r.content
        except Exception as e:
            print("Fallo", u, e)
    for n in LOCAL:
        if pathlib.Path(n).exists():
            yield n, pathlib.Path(n).read_bytes()


def main():
    mejor = None
    for nombre, raw in candidatos():
        try:
            rows = parsear(raw)
        except Exception as e:
            print("No se pudo leer", nombre, e)
            continue
        print(nombre[:70], "->", len(rows), "meses, último", rows[-1]["date"])
        if mejor is None or rows[-1]["date"] > mejor[-1]["date"]:
            mejor = rows
    if mejor is None:
        print("No se pudo obtener el Excel de Shiller.")
        sys.exit(0 if OUT.exists() else 1)
    OUT.write_text(json.dumps(mejor))
    print("Guardado: último mes", mejor[-1]["date"])


main()
