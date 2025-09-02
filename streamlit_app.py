import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# -----------------------------
# Dati (riciclati dalla tua app Tkinter)
# -----------------------------
data = {
    "Drone 20-20": [
        {"code": "RCC03FR008", "description": "Two-part ORS clamp 1\" 1/4"},
        {"code": "VTR01VT005", "description": "20lt Glass Reactor"},
        {"code": "VTR01VT004", "description": "50lt Glass Reactor"},
        {"code": "VTR01VT011", "description": "Internal glass adapter for mixer"},
        {"code": "VTR01VT012", "description": "Glass adapter DN25 for GL45 red tap"},
        {"code": "PFO01PL006", "description": "Red tap with hole"},
        {"code": "PFO01PL010", "description": "Seal for red tap D.42x26 mm. x guide"},
    ],
    "OMD S-Series": [
        {"code": "FFS03XX015", "description": "Stirrer holder"},
        {"code": "FFS01CS010", "description": "AC 4 Crucible"},
        {"code": "FFS01GR001", "description": "Crucible graphite S11 jacket and edge"},
        {"code": "FFS01CS001", "description": "Crucible silicon carbide S11 jacket and edge"},
        {"code": "FFS06FF035", "description": "1400grade Paper 450x110"},
        {"code": "FFS06FF036", "description": "Insulating mat 450x110"},
    ],
    "MM 30-50": [
        {"code": "PFO02XX013", "description": "50 lt Electric Heater"},
        {"code": "VTR02VT001", "description": "50 lt Glass Reactor"},
        {"code": "PFO02XX001", "description": "Upper Valve Kit"},
        {"code": "PFO02XX002", "description": "Lower Valve Kit"},
        {"code": "PFO02XX003", "description": "Valve"},
    ],
}

st.set_page_config(page_title="Orostudio Italy Srl - Spare Parts", page_icon="🧩", layout="wide")

# -----------------------------
# Inizializzazione stato
# -----------------------------
if "cart" not in st.session_state:
    # cart: dict con chiave (machine, code) -> {"description": str, "quantity": int}
    st.session_state.cart = {}

st.markdown(
    """
    <style>
        .title { color: black; }
        .help { font-style: italic; color: #222; }
        .machine { font-weight: 600; }
        .orostudio { background:#A6192E11; padding: 0.6rem 1rem; border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Orostudio Italy Srl — Spare Parts Web App")
st.markdown('<div class="orostudio">Any problems? Please write to <b>service@orostudio.com</b></div>', unsafe_allow_html=True)

left, right = st.columns([2,1])

with left:
    machine = st.selectbox("Select Machine", list(data.keys()))
    st.divider()

    st.subheader("Parts")
    selected_quantities = []
    parts = data.get(machine, [])
    for part in parts:
        code = part["code"]
        desc = part["description"]
        c1, c2, c3 = st.columns([2, 6, 2])
        c1.write(f"**{code}**")
        c2.write(desc)
        qty = c3.number_input("Qty", key=f"qty_{machine}_{code}", min_value=0, step=1)
        selected_quantities.append((machine, code, desc, qty))

    add_clicked = st.button("Add Selected Items")
    if add_clicked:
        added = 0
        for machine, code, desc, qty in selected_quantities:
            if qty and qty > 0:
                key = (machine, code)
                if key in st.session_state.cart:
                    st.session_state.cart[key]["quantity"] += int(qty)
                else:
                    st.session_state.cart[key] = {"description": desc, "quantity": int(qty)}
                # reset the number input after adding
                st.session_state[f"qty_{machine}_{code}"] = 0
                added += 1
        if added > 0:
            st.success(f"{added} items added to your order.")
        else:
            st.info("No quantity selected.")

with right:
    st.subheader("Order summary")
    if st.session_state.cart:
        # Show cart
        total_items = 0
        for (m, code), info in sorted(st.session_state.cart.items()):
            row = st.columns([1.5, 5, 1.5])
            row[0].write(f"**{code}**")
            row[1].write(f"{info['description']}  \n_Machine: {m}_")
            # Quantity editor
            new_q = row[2].number_input(
                "Qty",
                key=f"cart_qty_{m}_{code}",
                min_value=0,
                step=1,
                value=int(info["quantity"]),
            )
            if new_q != info["quantity"]:
                if new_q == 0:
                    # remove from cart
                    del st.session_state.cart[(m, code)]
                    st.rerun()
                else:
                    st.session_state.cart[(m, code)]["quantity"] = int(new_q)

            total_items += info["quantity"]

        st.write(f"**Total lines:** {len(st.session_state.cart)} — **Total qty:** {total_items}")
        if st.button("Empty cart"):
            st.session_state.cart.clear()
            st.success("Cart cleared.")
            st.rerun()
    else:
        st.info("Cart is empty.")

st.divider()
st.subheader("Generate PDF")

filename = st.text_input("PDF filename", value="spare_parts_order.pdf")
generate = st.button("Generate PDF")

def generate_pdf_bytes(cart: dict) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica", 16)
    c.drawString(50, height - 50, "Spare Parts Order")

    c.setFont("Helvetica", 12)
    y = height - 90

    current_machine = None

    # Riorganizza per macchina
    for (machine, code), info in sorted(cart.items()):
        if machine != current_machine:
            c.setFont("Helvetica-Bold", 14)
            y -= 30
            c.drawString(50, y, f"Machine: {machine}")
            y -= 20
            c.setFont("Helvetica-Bold", 10)
            c.drawString(60, y, "Code")
            c.drawString(160, y, "Description")
            c.drawString(460, y, "Quantity")
            y -= 15
            current_machine = machine

        c.setFont("Helvetica", 10)
        c.drawString(60, y, code)
        c.drawString(160, y, info["description"][:70])  # truncate a bit to avoid overflow
        c.drawString(460, y, str(info["quantity"]))
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

if generate:
    if not st.session_state.cart:
        st.warning("No items selected!")
    else:
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        pdf_bytes = generate_pdf_bytes(st.session_state.cart)
        st.download_button("Download PDF", data=pdf_bytes, file_name=filename, mime="application/pdf")
        st.success("PDF generated. Use the button above to download.")
