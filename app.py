from flask import Flask, render_template, request, redirect, session
import json
from datetime import datetime
from urllib.parse import quote

app = Flask(__name__)
app.secret_key = "admin-secret"

DATA_FILE = "data.json"
ORDERS_FILE = "orders.json"
WA_NUMBER = "6281290305857"

# =====================
# HELPER
# =====================
def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_orders():
    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_orders(data):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# =====================
# USER PAGE
# =====================
@app.route("/")
def index():
    data = load_data()
    return render_template("index.html", data=data)

# =====================
# ORDER + WA
# =====================
@app.route("/order/<transport>/<int:tiket_id>")
def order_ticket(transport, tiket_id):
    data = load_data()
    orders = load_orders()

    tiket = None
    if transport == "kereta":
        tiket = next((t for t in data["train_tickets"] if t["id"] == tiket_id), None)
    elif transport == "bus":
        tiket = next((t for t in data["bus_tickets"] if t["id"] == tiket_id), None)
    elif transport == "perahu":
        tiket = next((t for t in data["boat_tickets"] if t["id"] == tiket_id), None)

    if not tiket:
        return redirect("/")

    waktu_order = datetime.now().strftime("%d-%m-%Y %H:%M")
    kode_tiket = f"TKT{len(orders)+1:04d}"

    orders.append({
        "transport": tiket["transport_name"],
        "rute": f'{tiket["origin"]} - {tiket["destination"]}',
        "kelas": tiket["class"],
        "harga": tiket["price"],
        "status": "MENUNGGU PEMBAYARAN",
        "waktu": waktu_order,
        "kode": kode_tiket
    })
    save_orders(orders)

    pesan = f"""
🧾 *PESANAN TIKET BARU*

🚆 Transport : {tiket['transport_name']}
📍 Rute      : {tiket['origin']} ➝ {tiket['destination']}
📅 Tanggal   : {tiket['date']}
⏰ Jam       : {tiket['time']}
🎟️ Kelas     : {tiket['class']}
💰 Harga     : Rp {format(tiket['price'], ',')}

📅 Order     : {waktu_order}
🎫 Kode Tiket : {kode_tiket}

Saya ingin memesan tiket ini, mohon info pembayaran 🙏
"""
    pesan_encoded = quote(pesan)
    return redirect(f"https://wa.me/{WA_NUMBER}?text={pesan_encoded}")

# =====================
# LOGIN ADMIN
# =====================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin")
    return render_template("login.html")

# =====================
# ADMIN DASHBOARD
# =====================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")
    orders = load_orders()
    return render_template("admin.html", orders=orders)

# =====================
# ADMIN - TAMBAH / EDIT TIKET
# =====================
@app.route("/admin/tickets", methods=["GET","POST"])
def admin_tickets():
    if not session.get("admin"):
        return redirect("/login")

    data = load_data()

    # POST: Tambah tiket baru
    if request.method == "POST":
        new_ticket = {
            "id": int(request.form["id"]),
            "origin": request.form["origin"],
            "destination": request.form["destination"],
            "date": request.form["date"],
            "time": request.form["time"],
            "class": request.form["class"],
            "price": int(request.form["price"]),
            "availability": int(request.form["availability"]),
            "transport_name": request.form["transport_name"]
        }

        transport = request.form["transport"]
        if transport == "kereta":
            data["train_tickets"].append(new_ticket)
        elif transport == "bus":
            data["bus_tickets"].append(new_ticket)
        elif transport == "perahu":
            data["boat_tickets"].append(new_ticket)

        save_data(data)
        return redirect("/admin/tickets")

    return render_template("admin_tickets.html", data=data)

# =====================
# EDIT TIKET
# =====================
@app.route("/admin/edit/<transport>/<int:tiket_id>", methods=["GET","POST"])
def edit_ticket(transport, tiket_id):
    if not session.get("admin"):
        return redirect("/login")

    data = load_data()
    ticket = None

    if transport == "kereta":
        ticket = next((t for t in data["train_tickets"] if t["id"]==tiket_id), None)
    elif transport == "bus":
        ticket = next((t for t in data["bus_tickets"] if t["id"]==tiket_id), None)
    elif transport == "perahu":
        ticket = next((t for t in data["boat_tickets"] if t["id"]==tiket_id), None)

    if not ticket:
        return redirect("/admin/tickets")

    if request.method == "POST":
        ticket["origin"] = request.form["origin"]
        ticket["destination"] = request.form["destination"]
        ticket["date"] = request.form["date"]
        ticket["time"] = request.form["time"]
        ticket["class"] = request.form["class"]
        ticket["price"] = int(request.form["price"])
        ticket["availability"] = int(request.form["availability"])
        ticket["transport_name"] = request.form["transport_name"]
        save_data(data)
        return redirect("/admin/tickets")

    return render_template("edit_ticket.html", transport=transport, ticket=ticket)

# =====================
# DELETE TIKET
# =====================
@app.route("/admin/delete/<transport>/<int:tiket_id>")
def delete_ticket(transport, tiket_id):
    if not session.get("admin"):
        return redirect("/login")
    data = load_data()
    if transport == "kereta":
        data["train_tickets"] = [t for t in data["train_tickets"] if t["id"] != tiket_id]
    elif transport == "bus":
        data["bus_tickets"] = [t for t in data["bus_tickets"] if t["id"] != tiket_id]
    elif transport == "perahu":
        data["boat_tickets"] = [t for t in data["boat_tickets"] if t["id"] != tiket_id]
    save_data(data)
    return redirect("/admin/tickets")

# =====================
# UPDATE STATUS PEMBAYARAN
# =====================
@app.route("/update/<int:index>")
def update_status(index):
    if not session.get("admin"):
        return redirect("/login")
    orders = load_orders()
    orders[index]["status"] = "LUNAS"
    save_orders(orders)
    return redirect("/admin")

# =====================
# LOGOUT
# =====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =====================
# CEK STATUS TIKET PUBLIK
# =====================
@app.route("/cek_tiket", methods=["GET","POST"])
def cek_tiket():
    ticket = None
    if request.method == "POST":
        kode = request.form.get("kode")
        orders = load_orders()
        ticket = next((o for o in orders if o.get("kode") == kode), None)
    return render_template("cek_tiket.html", ticket=ticket)

if __name__ == "__main__":
    app.run(debug=True)
