import math, datetime, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from fpdf import FPDF

# >>>> SET THESE <<<<
SENDGRID_API_KEY = "PASTE_YOUR_SENDGRID_API_KEY"
SENDER_EMAIL     = "you@yourdomain.com"  # must be a verified sender in SendGrid

# Try SendGrid import (keeps app working even if not installed/configured)
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
    SG_OK = True
except Exception:
    SG_OK = False

last = None  # holds last computed quote

def build_pdf_bytes(q, ts):
    pdf = FPDF(); pdf.add_page()
    pdf.set_font("Helvetica","B",16); pdf.cell(0,10,"QuoteGenie",ln=1)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0,8,f"Quote #: Q-{ts}   Date: {datetime.date.today()}",ln=1)
    pdf.cell(0,8,f"Room: {q['L']}x{q['W']}x{q['H']} ft  Ceiling: {'Yes' if q['ceil'] else 'No'}",ln=1); pdf.ln(3)
    def row(k,v): pdf.set_font("Helvetica","B",11); pdf.cell(70,7,k); pdf.set_font("Helvetica","",11); pdf.cell(0,7,v,ln=1)
    row("Area (sqft)", f"{q['area']:.1f}")
    row("Sheets", str(q['sheets']))
    row("Labor (hrs)", f"{q['labor_hrs']:.1f}")
    row("Labor", f"${q['labor']:,.2f}")
    row("Materials", f"${q['materials']:,.2f}")
    row("Subtotal", f"${q['subtotal']:,.2f}")
    row("Markup", f"${q['markup_amt']:,.2f}")
    row("TOTAL", f"${q['total']:,.2f}")
    pdf.ln(3); pdf.set_font("Helvetica","",9)
    pdf.multi_cell(0,6,"Note: This is an estimate. Final price may vary after on-site review.")
    return pdf.output(dest="S").encode("latin-1")

def compute():
    global last
    try:
        L=float(l_var.get()); W=float(w_var.get()); H=float(h_var.get())
        hourly=float(hourly_var.get()); sheet_cost=float(sheet_var.get()); markup=float(markup_var.get())
        ceil = (ceil_var.get()==1)

        area = 2*(L+W)*H + (L*W if ceil else 0)
        sheets = max(1, math.ceil(area/32))
        labor_hrs = max(1.0, area/120.0)
        labor = labor_hrs*hourly
        materials = sheets*sheet_cost + area*(0.20+0.08)
        subtotal = labor + materials
        m = subtotal*(markup/100.0)
        total = subtotal + m

        last = dict(L=L,W=W,H=H,ceil=ceil,hourly=hourly,sheet_cost=sheet_cost,markup=markup,
                    area=area,sheets=sheets,labor_hrs=labor_hrs,labor=labor,
                    materials=materials,subtotal=subtotal,markup_amt=m,total=total)

        out=(f"Area: {area:.1f} sqft | Sheets: {sheets} | Labor: {labor_hrs:.1f} hrs\n"
             f"Labor ${labor:,.2f} | Materials ${materials:,.2f}\n"
             f"Subtotal ${subtotal:,.2f} | Markup ${m:,.2f}\n"
             f"TOTAL ${total:,.2f}")
        result_var.set(out)
        save_btn.config(state="normal")
        email_btn.config(state="normal")
    except ValueError:
        messagebox.showerror("Input error","Please enter numbers only.")

def save_pdf():
    if not last: return messagebox.showwarning("No quote","Click Calculate first.")
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = filedialog.asksaveasfilename(defaultextension=".pdf",
                                         initialfile=f"Q-{ts}.pdf",
                                         filetypes=[("PDF","*.pdf")])
    if not fname: return
    data = build_pdf_bytes(last, ts)
    with open(fname,"wb") as f: f.write(data)
    messagebox.showinfo("Saved", f"PDF saved:\n{fname}")

def send_email():
    if not last: return messagebox.showwarning("No quote","Click Calculate first.")
    if not SG_OK: return messagebox.showerror("SendGrid not installed","Run: python -m pip install sendgrid")
    if not SENDGRID_API_KEY or not SENDER_EMAIL:
        return messagebox.showerror("Missing settings","Set SENDGRID_API_KEY and SENDER_EMAIL at the top of the file.")
    to = client_email_var.get().strip()
    name = client_name_var.get().strip()
    if "@" not in to: return messagebox.showerror("Email error","Enter a valid client email.")

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    pdf_bytes = build_pdf_bytes(last, ts)
    filename = f"Q-{ts}.pdf"
    subject = f"Your drywall quote {filename[:-4]}"
    body = (f"Hello {name or 'there'},\n\n"
            f"Please find your estimate attached.\n"
            f"Total: ${last['total']:,.2f}\n\n"
            f"Thank you!")

    try:
        msg = Mail(from_email=SENDER_EMAIL, to_emails=to, subject=subject, plain_text_content=body)
        att = Attachment()
        att.file_content = FileContent(pdf_bytes)
        att.file_type = FileType("application/pdf")
        att.file_name = FileName(filename)
        att.disposition = Disposition("attachment")
        msg.attachment = att
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        resp = sg.send(msg)
        if resp.status_code in (200,202):
            messagebox.showinfo("Sent", f"Email sent to {to}")
        else:
            messagebox.showerror("Send failed", f"Status: {resp.status_code}\nCheck sender verification.")
    except Exception as e:
        messagebox.showerror("Send failed", f"{e}\nTip: verify your sender in SendGrid.")

# ---- UI ----
root = tk.Tk(); root.title("QuoteGenie — Simple UI (PDF + Email)")
frm = ttk.Frame(root, padding=12); frm.grid()

l_var=tk.StringVar(value="12"); w_var=tk.StringVar(value="10"); h_var=tk.StringVar(value="8")
hourly_var=tk.StringVar(value="65"); sheet_var=tk.StringVar(value="18"); markup_var=tk.StringVar(value="20")
ceil_var=tk.IntVar(value=1); result_var=tk.StringVar()
client_name_var=tk.StringVar(value="John Doe")
client_email_var=tk.StringVar(value="john@example.com")

for i,(label,var) in enumerate([("Length (ft)",l_var),("Width (ft)",w_var),("Height (ft)",h_var),
                                ("Labor $/hr",hourly_var),("Sheet cost (4x8)",sheet_var),("Markup %",markup_var)]):
    ttk.Label(frm, text=label).grid(row=i, column=0, sticky="e", padx=6, pady=4)
    ttk.Entry(frm, textvariable=var, width=14).grid(row=i, column=1, sticky="w")

ttk.Checkbutton(frm, text="Include ceiling", variable=ceil_var).grid(row=6, column=0, columnspan=2, pady=4)

ttk.Label(frm, text="Client name").grid(row=7, column=0, sticky="e", padx=6, pady=4)
ttk.Entry(frm, textvariable=client_name_var, width=22).grid(row=7, column=1, sticky="w")
ttk.Label(frm, text="Client email").grid(row=8, column=0, sticky="e", padx=6, pady=4)
ttk.Entry(frm, textvariable=client_email_var, width=22).grid(row=8, column=1, sticky="w")

ttk.Button(frm, text="Calculate", command=compute).grid(row=9, column=0, columnspan=2, pady=6)
save_btn  = ttk.Button(frm, text="Save PDF",  command=save_pdf,  state="disabled"); save_btn.grid(row=10, column=0, columnspan=2, pady=4)
email_btn = ttk.Button(frm, text="Send Email", command=send_email, state="disabled"); email_btn.grid(row=11, column=0, columnspan=2, pady=4)

ttk.Label(frm, textvariable=result_var, justify="left").grid(row=12, column=0, columnspan=2, sticky="w", pady=6)

root.mainloop()
