# Yarn Dispatch Desk

A single-file, no-build web app for a yarn manufacturer's sales dispatch and purchase ledger:
delivery challans (bag-by-bag), open sales orders with contracted-vs-delivered tracking, incoming
yarn receipts, purchase orders, client statements and Excel/HTML reports.

Built for a family-run specialty yarn mill (twisting, doubling, covering, fancy yarn) and
generalised for publication. **All data in this repository is synthetic.**

![Dashboard](docs/screenshot-dashboard.png)

## Try it

Live demo (GitHub Pages): _add your Pages URL here after enabling it_

Or locally:

```bash
python -m http.server 8000      # from this folder
# open http://localhost:8000
```

On first load the app seeds your browser's IndexedDB from `sample-data/demo-db.json`
(~1,400 deliveries, ~530 receipts, 18 sales orders, 8 purchase orders over 24 months).
Edits stay in your browser only. To reset, clear the site's data.

## Features

- **Challan builder** — header + per-bag table (machine / weight / cones), live totals in bags, cones, kg, lbs; auto-numbering; duplicate-challan warning
- **Printable challan** — two copies (head office + driver) on one A4 sheet with a tear line
- **Order book** — contracted vs delivered vs open in bags *and* lbs; click an order to see every delivery counted against it; printable client statement
- **Purchase side** — receipts, purchase orders, supplier/item/colour lists
- **Reference data manager** — renaming a client or item rewrites every record that used it
- **Exports** — Excel (.xlsx, built in-browser, no libraries) and standalone HTML reports

## How it works

| File | Role |
|---|---|
| `index.html` | the whole app (HTML, CSS, JS) |
| `local-db.js` | storage shim: implements the document-store API the app expects on top of IndexedDB |
| `sample-data/demo-db.json` | synthetic seed data |
| `tools/make_demo_data.py` | seeded generator for that file |

Data model — documents keyed by path, chunked by month so no document grows unbounded:

```
deliveries/YYYY-MM   {month, rows:[{id,date,client,item,lot,bags,kg,lbs,challan,bl?,cones?,vehicle?,po?}], count}
purchases/YYYY-MM    {month, rows:[{id,date,supplier,item,color,lot,qty,unit,uw,kg,lbs,ref}], count}
orders/ORD-0001      {client,item,lot,po,contractedBags,contractedLbs,dateOpened,status,closingDate,notes}
porders/PO-0001      purchase-side equivalent
refs/{clients,items,suppliers,pitems,colors}   {list:[...]}
meta/info            counters (nextOrderSeq, lastChallanNo, ...)
```

A delivery's `bl` is the bag ledger `[{m: machine, k: kg, c: cones}]`; when present it is the source of
truth for bags, kg and cones.

**Order ↔ delivery matching rule:** client and item equal, order lot blank = any lot (otherwise the delivery's
lot *contains* the order lot), delivery date ≥ order opened and ≤ closing date when set.

## Regenerate demo data

```bash
python tools/make_demo_data.py --seed 7 --months 36 --end 2026-09
```

Same seed, same output. Names are invented; nothing is derived from real records.

## Limitations (read before using for real work)

- **Single browser, single machine.** IndexedDB lives inside the browser profile; clearing site data
  deletes the ledger. For real use, add file-folder storage or a server and keep backups.
- **No stock balance.** The dashboard shows yarn purchased vs yarn dispatched side by side. Raw yarn in and
  twisted yarn out are different materials, so the gap is stock + work-in-progress + waste, not a stock figure.
  A proper finished-goods ledger needs a production register (bags packed per item/lot); that is not in this build.
- No authentication or multi-user sync.
- Native `alert/confirm/print` are avoided so the app also works inside sandboxed frames; challans print by
  downloading a standalone HTML file and printing it from the browser.

## License

MIT — see `LICENSE`.
