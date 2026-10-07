#!/usr/bin/env python3
"""Generate fully synthetic demo data for Yarn Dispatch Desk.

Nothing here is derived from any real business. Names are invented, volumes are
drawn from a seeded RNG, so the same --seed always produces the same file.

    python tools/make_demo_data.py                 # writes sample-data/demo-db.json
    python tools/make_demo_data.py --seed 7 --months 36
"""
import argparse, json, random, datetime as dt
from collections import defaultdict

KG_TO_LBS = 2.20462

CLIENTS = ["ALPHA WEAVING MILLS","BRIGHTON FABRICS","CEDAR TEXTILE","DELTA KNITTING","EASTERN LOOMS",
 "FALCON FABRICS","GRANITE WEAVERS","HARBOUR TEXTILE","IVORY DENIM WORKS","JUNIPER FABRICS",
 "KESTREL KNITS","LUMEN TEXTILE","MERIDIAN WEAVING","NORTHGATE FABRICS","ORCHARD LOOMS",
 "PIONEER TEXTILE","QUARTZ WEAVERS","RIVERSIDE FABRICS","SUMMIT KNITTING","TIMBER TEXTILE",
 "UNITY WEAVING","VALLEY FABRICS","WILLOW LOOMS","ZENITH TEXTILE","ARBOR FABRICS"]
# client weight: a few anchors take most volume, long tail the rest
CLIENT_W = [10,9,8]+[4]*6+[2]*16

ITEMS = ["17/1 FLEX","17/1 RICE SLUB","20/1 SLUB","30/1 SLUB","40/1 COTTON CRYSTAL YARN","20/1 AYUDIYA",
 "AMC-20","AMC-40","10/1 DHANAK","16/1 KEKRA","24/1 FANCY SLUB","30/2 DOUBLED","40/2 DOUBLED",
 "EMBROIDERY THREAD 120D","EMBROIDERY THREAD 150D","VISCOSE FLAMME 20/1","POLYESTER CORE 150D","METALLIC GOLD COVERED","METALLIC SILVER COVERED","LUREX RAINBOW"]
ITEM_W = [14,10,9,8,7,7,5,5,4,4,4,3,3,3,2,2,2,1,1,1]

SUPPLIERS = ["APEX YARN TRADERS","BLUEWAVE FIBRES","CRESCENT SPINNING","DAWN POLYMERS","EVEREST FILAMENT",
 "FORTUNE SPINNERS","GLOBAL FIBRE IMPORTS","HORIZON YARNS","INDUS COTTON MILLS","JADE SYNTHETICS",
 "KEYSTONE FIBRES","LOTUS SPINNING"]
PITEMS = ["30/1 COMBED COTTON","40/1 COMBED COTTON","20/1 CARDED COTTON","150/48 POLYESTER DTY","75/36 POLYESTER DTY",
 "150/144 POLYESTER FDY","100% VISCOSE 30/1","VISCOSE FILAMENT 120D","NYLON 70D","SPANDEX 40D",
 "LUREX ZARI","ACRYLIC 2/32","POLYESTER SPUN 40/1","COTTON SLUB BASE 20/1","MERCERISED COTTON 60/2"]
COLORS = ["BLACK","WHITE","GOLDEN","SILVER","BLUE","GREEN","RED","YELLOW","PINK","BROWN","RAINBOW"]
LOTS = ["", "", "", "A","B","C","P","S","M","F"]

def months_back(end, n):
    y, m = end.year, end.month
    out = []
    for _ in range(n):
        out.append((y, m)); m -= 1
        if m == 0: y, m = y-1, 12
    return out[::-1]

def r2(x): return round(x + 0.0, 2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--months", type=int, default=24)
    ap.add_argument("--end", default="2026-09", help="last month, YYYY-MM")
    ap.add_argument("--out", default="sample-data/demo-db.json")
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    ey, em = map(int, a.end.split("-"))
    end = dt.date(ey, em, 1)
    docs = {}

    # ---------- deliveries ----------
    challan = 1000
    drows = defaultdict(list)
    ms = months_back(end, a.months)
    for idx, (y, m) in enumerate(ms):
        season = 1 + 0.25 * __import__("math").sin((m - 3) / 12 * 2 * 3.14159)   # gentle seasonality
        growth = 0.8 + 0.4 * idx / max(1, len(ms) - 1)
        n = int(rnd.gauss(70, 10) * season * growth)
        last = (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)).day
        days = sorted(rnd.randint(1, last) for _ in range(n))
        for d in days:
            date = dt.date(y, m, d)
            if date.weekday() == 6: continue                              # no Sunday dispatch
            client = rnd.choices(CLIENTS, CLIENT_W)[0]
            item = rnd.choices(ITEMS, ITEM_W)[0]
            lot = rnd.choice(LOTS)
            bags = rnd.choice([2,4,5,6,8,10,10,12,15,18,20,25])
            challan += 1
            row = {"id": f"d{challan}", "date": date.isoformat(), "client": client, "item": item, "lot": lot,
                   "challan": str(challan), "billty": "", "note": "", "src": "demo"}
            if idx >= len(ms) - 3:                                       # recent rows carry a bag ledger
                bl, mach = [], rnd.choice(["5-B","7-C","13-B","2-D","9-10-C"])
                for _ in range(bags):
                    if rnd.random() < .15: mach = rnd.choice(["5-B","7-C","13-B","2-D","9-10-C"])
                    bl.append({"m": mach, "k": r2(rnd.uniform(36, 46)), "c": rnd.randint(36, 70)})
                kg = r2(sum(b["k"] for b in bl))
                row.update(bags=len(bl), kg=kg, lbs=r2(kg * KG_TO_LBS), bl=bl, cones=sum(b["c"] for b in bl),
                           vehicle=f"{rnd.choice(['KHI','LEA','ABC'])}-{rnd.randint(1000,9999)}",
                           cone=rnd.choice(["GREEN","WHITE","BLUE","RED"]), po=f"PO-{rnd.randint(100,999)}")
            else:
                kg = r2(bags * rnd.uniform(36, 46))
                row.update(bags=bags, kg=kg, lbs=r2(kg * KG_TO_LBS))
            drows[f"{y}-{m:02d}"].append(row)
    for k, rows in drows.items():
        docs[f"deliveries/{k}"] = {"month": k, "rows": rows, "count": len(rows)}

    # ---------- sales orders ----------
    all_d = [r for rs in drows.values() for r in rs]
    orders = []
    for i in range(1, 19):
        base = rnd.choice(all_d[-600:])
        opened = (dt.date.fromisoformat(base["date"]) - dt.timedelta(days=rnd.randint(5, 60))).isoformat()
        lot = base["lot"] if rnd.random() < .5 else ""
        cb = rnd.choice([100, 150, 200, 300, 400, 500])
        closed = i <= 5
        o = {"id": f"ORD-{i:04d}", "createdAt": opened, "client": base["client"], "item": base["item"], "lot": lot,
             "po": f"PO-{rnd.randint(100,999)}", "contractedBags": cb, "contractedLbs": int(cb * 42 * KG_TO_LBS),
             "dateOpened": opened, "status": "Closed" if closed else "Open",
             "closingDate": (dt.date.fromisoformat(opened) + dt.timedelta(days=90)).isoformat() if closed else "",
             "notes": "Payment 30 days from delivery. Pack in 25 kg bags." if i % 3 == 0 else ""}
        orders.append(o); docs[f"orders/{o['id']}"] = o

    # ---------- purchases ----------
    prows = defaultdict(list); ref = 5000
    for (y, m) in ms:
        for _ in range(int(rnd.gauss(22, 5))):
            d = dt.date(y, m, rnd.randint(1, 28)); ref += 1
            item = rnd.choice(PITEMS); unit = rnd.choice(["BAG","BAG","CARTON","CONE"])
            qty = rnd.choice([10,20,30,40,50,60,80,100]); uw = rnd.choice([25,25,30,40,45])
            kg = r2(qty * uw)
            prows[f"{y}-{m:02d}"].append({"id": f"p{ref}", "date": d.isoformat(), "supplier": rnd.choice(SUPPLIERS),
              "item": item, "color": rnd.choice(COLORS) if "LUREX" in item or "POLYESTER" in item else "",
              "lot": rnd.choice(["","","LOT-"+str(rnd.randint(1,40))]), "qty": qty, "unit": unit, "uw": str(uw),
              "kg": kg, "lbs": r2(kg * KG_TO_LBS), "ref": str(ref), "notes": "", "src": "demo", "raw": ""})
    for k, rows in prows.items():
        docs[f"purchases/{k}"] = {"month": k, "rows": rows, "count": len(rows)}

    porders = []
    for i in range(1, 9):
        o = {"id": f"PO-{i:04d}", "createdAt": f"{a.end}-01", "supplier": rnd.choice(SUPPLIERS), "item": rnd.choice(PITEMS),
             "color": "", "lot": "", "po": f"SUP-{rnd.randint(100,999)}", "dateOpened": f"{a.end}-01", "closingDate": "",
             "contractedQty": rnd.choice([100, 200, 400]), "unit": "BAG", "contractedKg": rnd.choice([4000, 8000, 16000]),
             "status": "Open" if i > 3 else "Closed", "notes": ""}
        porders.append(o); docs[f"porders/{o['id']}"] = o

    # ---------- reference lists + meta ----------
    docs["refs/clients"] = {"list": sorted(CLIENTS), "updatedAt": a.end + "-01"}
    docs["refs/items"] = {"list": sorted(ITEMS), "updatedAt": a.end + "-01"}
    docs["refs/suppliers"] = {"list": sorted(SUPPLIERS), "updatedAt": a.end + "-01"}
    docs["refs/pitems"] = {"list": sorted(PITEMS), "updatedAt": a.end + "-01"}
    docs["refs/colors"] = {"list": sorted(COLORS), "updatedAt": a.end + "-01"}
    docs["meta/info"] = {"seededAt": "synthetic", "pSeededAt": "synthetic",
        "deliveryRows": len(all_d), "purchaseRows": sum(len(v) for v in prows.values()),
        "nextOrderSeq": len(orders) + 1, "nextPOrderSeq": len(porders) + 1, "lastChallanNo": challan}

    with open(a.out, "w", encoding="utf8") as f:
        json.dump({"generated": "synthetic", "seed": a.seed, "docs": docs}, f, separators=(",", ":"))
    print(f"{len(all_d)} deliveries, {sum(len(v) for v in prows.values())} receipts, "
          f"{len(orders)} sales orders, {len(porders)} purchase orders -> {a.out}")

if __name__ == "__main__":
    main()
