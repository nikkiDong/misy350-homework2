import json
import uuid
from pathlib import Path

import streamlit as st


inventory = [{"id": 1, "name": "Espresso", "price": 2.50, "stock": 40}]

json_file = Path("inventory.json")

if json_file.exists():
    with open(json_file, "r") as f:
        inventory = json.load(f)
else:
    with open(json_file, "w") as f:
        json.dump(inventory, f, indent=4)



def load_inventory():
    if json_file.exists():
        with open(json_file, "r") as f:
            return json.load(f)
    return []


def save_inventory(inventory):
    with open(json_file, "w") as f:
        json.dump(inventory, f, indent=4)


# Session state init
if "inventory" not in st.session_state:
    st.session_state.inventory = load_inventory()

if "orders" not in st.session_state:
    st.session_state.orders = []

#  App layout 

st.title(" Smart Coffee Kiosk")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Place Order", "View Inventory", "Restock", "Manage Orders"]
)

# Tab 1: Place Order (Create)

with tab1:
    st.header("Place an Order")

    inventory = st.session_state.inventory
    item_names = [item["name"] for item in inventory]

    if not item_names:
        st.warning("No items available.")
    else:
        selected_name = st.selectbox("Select Item", item_names, key="order_item")
        quantity = st.number_input("Quantity", min_value=1, step=1, key="order_qty")
        customer = st.text_input("Customer Name", key="order_customer")

        if st.button("Place Order"):
            if not customer.strip():
                st.error("Please enter a customer name.")
            else:
                item = next(i for i in inventory if i["name"] == selected_name)
                if item["stock"] < quantity:
                    st.error(
                        f"Out of Stock! Only {item['stock']} unit(s) of {selected_name} available."
                    )
                else:
                    item["stock"] -= quantity
                    save_inventory(inventory)

                    order = {
                        "order_id": str(uuid.uuid4())[:8].upper(),
                        "customer": customer.strip(),
                        "item": selected_name,
                        "quantity": quantity,
                        "total": round(item["price"] * quantity, 2),
                        "status": "Placed",
                    }
                    st.session_state.orders.append(order)

                    st.success(f"Order placed successfully for {customer.strip()}!")

                    with st.expander("📄 View Receipt"):
                        st.write(f"**Order ID:** {order['order_id']}")
                        st.write(f"**Customer:** {order['customer']}")
                        st.write(f"**Item:** {order['item']} × {order['quantity']}")
                        st.write(f"**Total:** ${order['total']:.2f}")
                        st.write(f"**Status:** {order['status']}")

# Tab 2: View & Search Inventory (Read)

with tab2:
    st.header("View Inventory")

    inventory = st.session_state.inventory
    search = st.text_input("Search by name", placeholder="e.g. Latte", key="search")

    filtered = (
        [i for i in inventory if search.lower() in i["name"].lower()]
        if search
        else inventory
    )

    total_stock = sum(i["stock"] for i in filtered)
    st.metric("Total Units in Stock", total_stock)

    st.divider()

    if not filtered:
        st.info("No items match your search.")
    else:
        for item in filtered:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            col1.write(f"**{item['name']}**")
            col2.write(f"${item['price']:.2f}")
            if item["stock"] < 10:
                col3.write(f"⚠️ {item['stock']} left")
            else:
                col3.write(f"{item['stock']} in stock")
            col4.write(f"ID: {item['id']}")


with tab3:
    st.header("Restock an Item")

    inventory = st.session_state.inventory
    item_names = [item["name"] for item in inventory]

    if not item_names:
        st.warning("No items available.")
    else:
        restock_name = st.selectbox("Select Item to Restock", item_names, key="restock_item")
        add_amount = st.number_input("Amount to Add", min_value=1, step=1, key="restock_qty")

        if st.button("Update Stock"):
            item = next(i for i in inventory if i["name"] == restock_name)
            item["stock"] += add_amount
            save_inventory(inventory)
            st.success(
                f"Restocked {restock_name}! New stock: {item['stock']} unit(s)."
            )

# ── Tab 4: Manage Orders (Delete/Cancel) ──────────────────────────────────────

with tab4:
    st.header("Manage Orders")

    orders = st.session_state.orders
    active_orders = [o for o in orders if o["status"] == "Placed"]

    if not active_orders:
        st.info("No active orders.")
    else:
        for order in active_orders:
            with st.container():
                col1, col2 = st.columns([4, 1])
                col1.write(
                    f"**#{order['order_id']}** — {order['customer']} | "
                    f"{order['item']} × {order['quantity']} | ${order['total']:.2f}"
                )
                if col2.button("Cancel", key=f"cancel_{order['order_id']}"):
                    # Mark order cancelled
                    order["status"] = "Cancelled"

                    # Refund stock
                    inventory = st.session_state.inventory
                    item = next(
                        (i for i in inventory if i["name"] == order["item"]), None
                    )
                    if item:
                        item["stock"] += order["quantity"]
                        save_inventory(inventory)

                    st.success(
                        f"Order #{order['order_id']} cancelled and stock refunded."
                    )
                    st.rerun()
