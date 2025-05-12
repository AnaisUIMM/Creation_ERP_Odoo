import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import xmlrpc.client
import base64
from io import BytesIO
from PIL import Image, ImageTk

# Connexion à l'ERP Odoo
ODOO_URL = "http://x.x.x.x"
ODOO_DB = "YOURT"
ODOO_USER = "x" #Mail
ODOO_PASSWORD = "x"

class OdooConnector:
    def __init__(self, username, password):
        self.common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        self.uid = self.common.authenticate(ODOO_DB, username, password, {})
        self.models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        if not self.uid:
            raise Exception("Échec de la connexion à Odoo")

    def get_company_info(self):
        result = self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD, 'res.company', 'search_read', [[]], {'fields': ['name', 'street', 'city', 'logo']})
        if result:
            return result[0]  # Retourne la première entreprise
        return None

    def get_all_products(self):
        products = self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD, 'product.product', 'search_read', [[]], 
            {'fields': ['name', 'image_1920', 'qty_available', 'list_price']})
        return products

    def get_manufacturing_orders(self, filter_state=None):
        domain = []
        if filter_state:
            domain = [('state', '=', filter_state)]
        manufacturing_orders = self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD, 'mrp.production', 'search_read', [domain], 
            {'fields': ['id', 'name', 'state', 'product_qty', 'date_planned_start']})
        return manufacturing_orders

    def update_manufacturing_order_qty(self, order_id, new_qty):
        self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD, 'mrp.production', 'write', [[order_id], {'product_qty': new_qty}])

    def update_manufacturing_order_state(self, order_id, new_state):
        self.models.execute_kw(
            ODOO_DB, self.uid, ODOO_PASSWORD, 'mrp.production', 'write', [[order_id], {'state': new_state}])

class LoginPage:
    def __init__(self, root):
        self.root = root
        self.root.title("Connexion à Odoo")
        self.root.geometry("400x300")
        self.root.config(bg="#f3f8ff")
        
        self.username_label = tk.Label(root, text="Identifiant", font=("Helvetica", 12), bg="#f3f8ff")
        self.username_label.pack(pady=10)

        self.username_entry = tk.Entry(root, font=("Helvetica", 12), width=25)
        self.username_entry.pack(pady=10)

        self.password_label = tk.Label(root, text="Mot de passe", font=("Helvetica", 12), bg="#f3f8ff")
        self.password_label.pack(pady=10)

        self.password_entry = tk.Entry(root, font=("Helvetica", 12), width=25, show="*")
        self.password_entry.pack(pady=10)

        self.login_button = tk.Button(root, text="Se connecter", font=("Helvetica", 12, "bold"), bg="#a8d8f0", fg="black", bd=0, relief="flat", width=25, height=2, activebackground="#9fd3e3", activeforeground="black", command=self.login)
        self.login_button.pack(pady=20)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Erreur", "Veuillez entrer un identifiant et un mot de passe.")
            return

        try:
            self.odoo = OdooConnector(username, password)
            messagebox.showinfo("Connexion réussie", "Vous êtes connecté à Odoo.")
            self.root.destroy()  # Ferme la fenêtre de connexion après la réussite de la connexion
            self.open_main_page()  # Ouvre la fenêtre principale
        except Exception as e:
            messagebox.showerror("Erreur de connexion", str(e))

    def open_main_page(self):
        main_window = tk.Tk()
        MainPage(main_window, self.odoo)
        main_window.mainloop()

class MainPage:
    def __init__(self, root, odoo_connector):
        self.root = root
        self.root.title("ERP Odoo - Yaourts")
        self.root.geometry("800x600")
        self.root.config(bg="#f3f8ff")
        self.odoo = odoo_connector

        self.create_buttons()

    def create_buttons(self):
        # Style des boutons : arrondis avec couleurs pastels
        button_style = {"font": ("Helvetica", 12, "bold"), "bg": "#a8d8f0", "fg": "black", "bd": 0, "relief": "flat", "width": 25, "height": 2, "activebackground": "#9fd3e3", "activeforeground":"black"}
        
        tk.Button(self.root, text="Afficher la fiche entreprise", command=self.show_company_info, **button_style).pack(pady=20)
        tk.Button(self.root, text="Afficher tous les produits", command=self.show_all_products, **button_style).pack(pady=20)
        tk.Button(self.root, text="Afficher les ordres de fabrication", command=self.show_manufacturing_orders, **button_style).pack(pady=20)

    def show_company_info(self):
        company_info = self.odoo.get_company_info()
        if not company_info:
            messagebox.showerror("Erreur", "Impossible de récupérer les informations de l'entreprise.")
            return

        company_window = tk.Toplevel(self.root)
        company_window.title("Fiche Entreprise")
        company_window.config(bg="#f3f8ff")

        label_style = {"font": ("Helvetica", 12), "bg": "#f3f8ff"}

        tk.Label(company_window, text=f"Nom: {company_info['name']}", font=("Helvetica", 14, "bold"), bg="#f3f8ff").pack(pady=5)
        tk.Label(company_window, text=f"Adresse: {company_info['street']}, {company_info['city']}", **label_style).pack(pady=5)

        if company_info.get("logo"):
            logo_data = base64.b64decode(company_info["logo"])
            image = Image.open(BytesIO(logo_data))
            image = image.resize((150, 150), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)

            label_logo = tk.Label(company_window, image=photo, bg="#f3f8ff")
            label_logo.image = photo
            label_logo.pack(pady=10)

    def show_all_products(self):
        products = self.odoo.get_all_products()
        if not products:
            messagebox.showerror("Erreur", "Aucun produit trouvé.")
            return

        products_window = tk.Toplevel(self.root)
        products_window.title("Liste des Produits")
        products_window.config(bg="#f3f8ff")

        for product in products:
            product_name = product['name']
            image_base64 = product.get('image_1920')
            qty_available = product.get('qty_available', 0)
            list_price = product.get('list_price', 0)

            frame = tk.Frame(products_window, bg="white", bd=2, relief="groove", padx=10, pady=10)
            frame.pack(pady=10, fill="x")

            if image_base64:
                image_data = base64.b64decode(image_base64)
                image = Image.open(BytesIO(image_data))
                image.thumbnail((100, 100))
                photo = ImageTk.PhotoImage(image)
                
                label_image = tk.Label(frame, image=photo)
                label_image.image = photo
                label_image.pack(side=tk.LEFT)

            tk.Label(frame, text=product_name, font=("Helvetica", 12, "bold"), bg="white").pack(side=tk.LEFT, padx=10)
            tk.Label(frame, text=f"Qté: {qty_available}", font=("Helvetica", 10), bg="white").pack(side=tk.LEFT, padx=10)
            tk.Label(frame, text=f"Prix: {list_price} €", font=("Helvetica", 10), bg="white").pack(side=tk.LEFT, padx=10)

    def show_manufacturing_orders(self):
        self.manufacturing_orders = self.odoo.get_manufacturing_orders()
        if not self.manufacturing_orders:
            messagebox.showerror("Erreur", "Aucun ordre de fabrication trouvé.")
            return

        if hasattr(self, 'manufacturing_window') and self.manufacturing_window.winfo_exists():
            self.manufacturing_window.lift()
        else:
            self.manufacturing_window = tk.Toplevel(self.root)
            self.manufacturing_window.title("Ordres de Fabrication")
            self.manufacturing_window.config(bg="#f3f8ff")

            self.tree = ttk.Treeview(self.manufacturing_window, columns=("ID", "Nom", "État", "Quantité", "Date Début"), show="headings", height=10)
            self.tree.pack(pady=20, padx=10, fill="x")

            self.tree.heading("ID", text="ID")
            self.tree.heading("Nom", text="Nom")
            self.tree.heading("État", text="État")
            self.tree.heading("Quantité", text="Quantité")
            self.tree.heading("Date Début", text="Date Début")

            self.tree.column("ID", width=50, anchor="center")
            self.tree.column("Nom", width=200, anchor="w")
            self.tree.column("État", width=100, anchor="center")
            self.tree.column("Quantité", width=100, anchor="center")
            self.tree.column("Date Début", width=150, anchor="center")

            self.populate_orders()

            modify_button = tk.Button(self.manufacturing_window, text="Passer à Fait", font=("Helvetica", 12, "bold"), bg="#a8f0a8", fg="black", command=self.pass_to_done)
            modify_button.pack(pady=10)

            quantity_button = tk.Button(self.manufacturing_window, text="Modifier la Quantité", font=("Helvetica", 12, "bold"), bg="#ffda88", fg="black", command=self.modify_quantity)
            quantity_button.pack(pady=10)

    def pass_to_done(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Erreur", "Veuillez sélectionner un ordre de fabrication.")
            return

        order_id = self.tree.item(selected_item)['values'][0]
        current_state = self.tree.item(selected_item)['values'][2]

        if current_state != "confirmed":
            messagebox.showerror("Erreur", "L'ordre de fabrication sélectionné n'est pas confirmé.")
            return

        self.odoo.update_manufacturing_order_state(order_id, "done")
        messagebox.showinfo("Succès", "L'état de l'ordre a été changé en 'Fait'.")
        self.refresh_orders()

    def modify_quantity(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Erreur", "Veuillez sélectionner un ordre de fabrication.")
            return

        order_id = self.tree.item(selected_item)['values'][0]
        current_qty = self.tree.item(selected_item)['values'][3]

        new_qty = simpledialog.askinteger("Modifier la quantité", "Entrez la nouvelle quantité", initialvalue=current_qty)

        if new_qty is not None:
            self.odoo.update_manufacturing_order_qty(order_id, new_qty)
            messagebox.showinfo("Succès", "La quantité a été mise à jour.")
            self.refresh_orders()

    def populate_orders(self):
        for order in self.manufacturing_orders:
            order_name = order['name']
            state = order['state']
            product_qty = order['product_qty']
            start_date = order['date_planned_start']
            order_id = order['id']

            self.tree.insert("", "end", values=(order_id, order_name, state, product_qty, start_date))

    def refresh_orders(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.manufacturing_orders = self.odoo.get_manufacturing_orders()
        self.populate_orders()

if __name__ == "__main__":
    root = tk.Tk()
    login_page = LoginPage(root)
    root.mainloop()
