#!/usr/bin/env python3
# Descarga las tablas de THE FINALS a data/finals/ (solo usa la libreria estandar).
#   python descargar_finals.py          baja lo que falta y refresca la temporada actual
#   python descargar_finals.py --todo   vuelve a bajar todo
import json, os, sys, time, urllib.request, urllib.error

SIN_PLATAFORMA = {"cb1", "cb2"}   # las betas cerradas no llevan /crossplay en la direccion
ACTUAL = "s12"   # cuando salga otra temporada, cambialo y agrega sus modos abajo
BASE = "https://api.the-finals-leaderboard.com/v1/leaderboard/"
CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "finals")
os.makedirs(CARPETA, exist_ok=True)

MODOS = {
    4: ["World Tour", "Sponsor"],
    5: ["Sponsor", "World Tour", "Terminal Attack", "PowerShift", "Quick Cash", "Bank It"],
    6: ["Sponsor", "World Tour", "Terminal Attack", "PowerShift", "Quick Cash", "Team Deathmatch", "Heavy Hitters"],
    7: ["Sponsor", "World Tour", "Terminal Attack", "PowerShift", "Quick Cash", "Team Deathmatch", "Blast Off", "Cash Ball"],
    8: ["Sponsor", "World Tour", "Head2Head", "PowerShift", "Quick Cash", "Team Deathmatch", "Blast Off", "Ghoul Rush", "Heaven Or Else"],
    9: ["Sponsor", "World Tour", "Head2Head", "PowerShift", "Quick Cash", "Team Deathmatch", "Point Break", "Bank It"],
    10: ["Sponsor", "World Tour", "PowerShift", "Quick Cash", "Team Deathmatch", "Point Break", "Starlight Hollow", "The 24 Hour Gauntlet", "Creator Gauntlet"],
    11: ["Sponsor", "World Tour", "PowerShift", "Quick Cash", "Team Deathmatch", "Point Break", "Orbital Hitters"],
    12: ["Sponsor", "World Tour", "PowerShift", "Quick Cash", "Team Deathmatch", "Point Break", "Solo Showdown"],
}
# (id, temporada, modo). Los ids de s12, s12sponsor y s12worldtour vienen de la documentacion;
# el resto siguen el mismo patron y los que no existan quedaran en no_descargadas.txt
TABLAS = [("cb1", "Closed Beta 1", "Principal"), ("cb2", "Closed Beta 2", "Principal"), ("ob", "Open Beta", "Principal"),
          ("s1", "Season 1", "Principal"), ("s2", "Season 2", "Principal"), ("s3", "Season 3", "Principal"),
          ("s3original", "Season 3", "Original"), ("s3worldtour", "Season 3", "World Tour")]
for n, modos in MODOS.items():
    TABLAS.append(("s%d" % n, "Season %d" % n, "Principal"))
    for m in modos:
        TABLAS.append(("s%d%s" % (n, m.lower().replace(" ", "")), "Season %d" % n, m))


def descargar(id_):
    ultimo = None
    for _ in range(3):
        try:
            req = urllib.request.Request(BASE + id_ + ("" if id_ in SIN_PLATAFORMA else "/crossplay"), headers={"User-Agent": "CruelTracker/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)["data"]
        except urllib.error.HTTPError as e:
            ultimo = "HTTP %d" % e.code
            if e.code == 404:
                break
        except Exception as e:
            ultimo = str(e)
        time.sleep(2)
    raise RuntimeError(ultimo)


todo = "--todo" in sys.argv
indice, fallidas = [], []
for id_, grupo, modo in TABLAS:
    ruta = os.path.join(CARPETA, id_ + ".js")
    entrada = {"id": id_, "group": grupo, "mode": modo}
    if os.path.exists(ruta) and not todo and not id_.startswith(ACTUAL):
        print("ya existe", id_)
        indice.append(entrada)
        continue
    try:
        datos = descargar(id_)
        for d in datos:
            d.pop("clubUuid", None)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("window.FINALS_DATA=window.FINALS_DATA||{};window.FINALS_DATA[%s]=%s;" %
                    (json.dumps(id_), json.dumps(datos, ensure_ascii=False, separators=(",", ":"))))
        print("ok", id_, len(datos), "filas")
        indice.append(entrada)
        time.sleep(1)
    except Exception as e:
        print("FALLO", id_, e)
        fallidas.append("%s\t%s %s\t%s" % (id_, grupo, modo, e))

with open(os.path.join(CARPETA, "index.js"), "w", encoding="utf-8") as f:
    f.write("window.FINALS_INDEX=%s;" % json.dumps(indice, ensure_ascii=False))
if fallidas:
    with open(os.path.join(os.path.dirname(CARPETA), "..", "no_descargadas.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(fallidas))
print("\nListo: %d tablas, %d fallaron%s" % (len(indice), len(fallidas), " (mira no_descargadas.txt)" if fallidas else ""))
