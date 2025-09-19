import sys, math
# usage: python quote.py L W H [hourly=65] [sheet_cost=18] [markup_pct=20]
L=float(sys.argv[1]); W=float(sys.argv[2]); H=float(sys.argv[3])
hourly=float(sys.argv[4]) if len(sys.argv)>4 else 65
sheet_cost=float(sys.argv[5]) if len(sys.argv)>5 else 18
markup=float(sys.argv[6]) if len(sys.argv)>6 else 20
area = 2*(L+W)*H + (L*W)              # sqft, with ceiling
sheets = max(1, math.ceil(area/32))   # 4x8 sheets
labor_hrs = max(1.0, area/120.0)
labor = labor_hrs*hourly
materials = sheets*sheet_cost + area*(0.20+0.08)  # mud+tape approx
subtotal = labor + materials
m = subtotal*(markup/100.0)
total = subtotal + m
print(f"Area: {area:.1f} sqft | Sheets: {sheets} | Labor: {labor_hrs:.1f} hrs")
print(f"Labor ${labor:,.2f} | Materials ${materials:,.2f} | Subtotal ${subtotal:,.2f} | Markup ${m:,.2f}")
print(f"TOTAL ${total:,.2f}")
