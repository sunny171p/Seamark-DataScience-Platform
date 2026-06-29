import sqlite3
import urllib.parse
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = 8081
DB_FILE = "../automation/seamark_inventory.db"

def get_inventory_metrics():
    """Calculates summary statistics from live warehouse stock data."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT cost_usd, retail_gbp, stock FROM inventory")
    rows = cursor.fetchall()
    conn.close()
    return {
        "unique_skus": len(rows),
        "total_units": sum(row[2] for row in rows),
        "tied_capital": sum(row[0] * row[2] for row in rows),
        "gross_revenue": sum(row[1] * row[2] for row in rows)
    }

def get_all_products():
    """Fetches full item details for web table compilation."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT sku, item_name, category, cost_usd, retail_gbp, stock FROM inventory")
    products = cursor.fetchall()
    conn.close()
    return products

def update_product_stock(sku, new_stock):
    """Saves stock adjustments directly into the database file."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE inventory SET stock = ? WHERE sku = ?", (new_stock, sku))
    conn.commit()
    conn.close()

class SeamarkDashboardHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        """Processes immediate warehouse inventory level overrides."""
        if self.path == "/update-stock":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            parsed_data = urllib.parse.parse_qs(post_data)
            try:
                sku = parsed_data.get('sku')[0]
                stock_val = int(parsed_data.get('stock')[0])
                if stock_val >= 0:
                    update_product_stock(sku, stock_val)
            except (IndexError, ValueError, TypeError):
                pass
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()

    def do_GET(self):
        """Generates the interactive visual administrative center."""
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            stats = get_inventory_metrics()
            products = get_all_products()
            table_body = ""
            for item in products:
                sku, name, cat, cost, retail, stock = item
                table_body += f"""
                <tr class="item-row">
                    <td><b>{sku}</b></td>
                    <td class="search-field">{name}</td>
                    <td>{cat}</td>
                    <td class="val-cost">${cost:.2f}</td>
                    <td class="val-retail">&pound;{retail:.2f}</td>
                    <td>
                        <form action="/update-stock" method="POST" class="inline-form">
                            <input type="hidden" name="sku" value="{sku}">
                            <input type="number" name="stock" value="{stock}" min="0" class="input-stock">
                            <button type="submit" class="btn-save">Update</button>
                        </form>
                    </td>
                </tr>"""
            html_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Seamark Hub</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #1e293b; margin: 0; padding: 40px; }}
        .workspace {{ max-width: 1200px; margin: 0 auto; background: #ffffff; padding: 32px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.04); }}
        h1 {{ color: #0f172a; margin: 0 0 4px 0; font-size: 28px; }}
        .subtitle {{ color: #64748b; font-size: 14px; margin: 0 0 24px 0; }}
        .deck {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 32px; }}
        .card {{ background: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; border-top: 4px solid #475569; }}
        .card.success {{ border-top-color: #16a34a; }}
        .card.primary {{ border-top-color: #2563eb; }}
        .card-title {{ font-size: 12px; font-weight: 600; text-transform: uppercase; color: #64748b; margin-bottom: 6px; letter-spacing: 0.5px; }}
        .card-stat {{ font-size: 24px; font-weight: 700; color: #0f172a; }}
        .search-bar {{ width: 100%; box-sizing: border-box; padding: 12px 16px; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 15px; margin-bottom: 24px; outline: none; transition: border-color 0.15s; }}
        .search-bar:focus {{ border-color: #2563eb; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 15px; margin-top: 10px; }}
        th {{ background: #0f172a; color: #ffffff; padding: 14px; text-align: left; font-weight: 500; }}
        td {{ padding: 14px; border-bottom: 1px solid #edf2f7; vertical-align: middle; }}
        .val-cost {{ color: #16a34a; font-weight: 500; }}
        .val-retail {{ font-weight: 600; color: #0f172a; }}
        .inline-form {{ display: flex; align-items: center; gap: 8px; margin: 0; }}
        .input-stock {{ width: 70px; padding: 6px; border: 1px solid #cbd5e1; border-radius: 6px; font-weight: 600; text-align: center; }}
        .btn-save {{ background: #2563eb; color: #ffffff; border: none; padding: 7px 14px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.15s; }}
        .btn-save:hover {{ background: #1d4ed8; }}
    </style>
    <script>
        function executeClientFilter() {{
            let input = document.getElementById('filterInput').value.toLowerCase();
            let rows = document.getElementsByClassName('item-row');
            for (let row of rows) {{
                let sku = row.cells[0].textContent.toLowerCase();
                let description = row.querySelector('.search-field').textContent.toLowerCase();
                row.style.display = (sku.includes(input) || description.includes(input)) ? "" : "none";
            }}
        }}
    </script>
</head>
<body>
    <div class="workspace">
        <h1>The Seamark Control Center</h1>
        <p class="subtitle">Internal Operations Dashboard - Sunday Emmanuel Azeez</p>
        <div class="deck">
            <div class="card">
                <div class="card-title">Unique Index</div>
                <div class="card-stat">{stats['unique_skus']} SKUs</div>
            </div>
            <div class="card">
                <div class="card-title">Total Units Available</div>
                <div class="card-stat">{stats['total_units']} units</div>
            </div>
            <div class="card success">
                <div class="card-title">Invested Capital (USD)</div>
                <div class="card-stat">${stats['tied_capital']:,.2f}</div>
            </div>
            <div class="card primary">
                <div class="card-title">Projected Revenue (GBP)</div>
                <div class="card-stat">&pound;{stats['gross_revenue']:,.2f}</div>
            </div>
        </div>
        <input type="text" id="filterInput" onkeyup="executeClientFilter()" placeholder="Search by SKU or product name..." class="search-bar">
        <table>
            <thead>
                <tr>
                    <th>SKU</th>
                    <th>Product Name</th>
                    <th>Category</th>
                    <th>Cost (USD)</th>
                    <th>Retail (GBP)</th>
                    <th>Stock Management</th>
                </tr>
            </thead>
            <tbody>
                {table_body if table_body else "<tr><td colspan='6' style='text-align:center; color:#94a3b8;'>No products logged.</td></tr>"}
            </tbody>
        </table>
    </div>
</body>
</html>"""
            self.wfile.write(html_document.encode("utf-8"))
        else:
            super().do_GET()

if __name__ == "__main__":
    print("Initializing Seamark full-stack local portal service...")
    print(f"Connection interface ready at: http://localhost:{PORT}")
    server = HTTPServer(("localhost", PORT), SeamarkDashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Terminating local server node cleanly.]")
        server.server_close()
