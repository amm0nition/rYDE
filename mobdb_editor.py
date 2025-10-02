import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog, ttk
import yaml
import os

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

MOB_TEMPLATE = {
    'Id': 0, 'AegisName': 'NEW_MOB', 'Name': 'New Mob', 'JapaneseName': 'New Mob',
    'Level': 1, 'Hp': 1, 'Sp': 1, 'BaseExp': 0, 'JobExp': 0, 'MvpExp': 0,
    'Attack': 0, 'Attack2': 0, 'Defense': 0, 'MagicDefense': 0,
    'Resistance': 0, 'MagicResistance': 0, 'Str': 1, 'Agi': 1, 'Vit': 1,
    'Int': 1, 'Dex': 1, 'Luk': 1, 'AttackRange': 0, 'SkillRange': 0,
    'ChaseRange': 0, 'Size': 'Small', 'Race': 'Formless',
    'RaceGroups': {}, 'Element': 'Neutral', 'ElementLevel': 1,
    'WalkSpeed': 'DEFAULT_WALK_SPEED', 'AttackDelay': 0, 'AttackMotion': 0,
    'ClientAttackMotion': 0, 'DamageMotion': 0, 'DamageTaken': 100,
    'GroupId': 0, 'Title': 'None', 'Ai': '06', 'Class': 'Normal',
    'Modes': {}, 'MvpDrops': [], 'Drops': []
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("rAthena Mob DB YML Editor")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")

        self.file_path = None
        self.header_data = {}
        self.mob_data = []
        self.current_mob_index = None
        
        self.sort_by_column = "ID"
        self.sort_reverse_order = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(1, weight=1)

        self.menu_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.btn_open = ctk.CTkButton(self.menu_frame, text="Open", command=self.load_file)
        self.btn_open.pack(side="left", padx=5, pady=5)
        self.btn_save = ctk.CTkButton(self.menu_frame, text="Save", command=self.save_file, state="disabled")
        self.btn_save.pack(side="left", padx=5, pady=5)
        self.btn_save_as = ctk.CTkButton(self.menu_frame, text="Save As...", command=self.save_file_as, state="disabled")
        self.btn_save_as.pack(side="left", padx=5, pady=5)

        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.left_frame.grid_rowconfigure(2, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.left_frame, text="Monsters", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(5,0))
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.filter_mob_list)
        self.search_entry = ctk.CTkEntry(self.left_frame, textvariable=self.search_var, placeholder_text="Search by ID or AegisName...")
        self.search_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f6aa5')])
        style.configure("Treeview.Heading", background="#242424", foreground="white", relief="flat")
        style.map("Treeview.Heading", background=[('active', '#343434')])

        self.mob_list_tree = ttk.Treeview(self.left_frame, columns=("ID", "AegisName"), show="headings")
        self.mob_list_tree.heading("ID", text="ID ▼", command=lambda: self.sort_treeview_column("ID"))
        self.mob_list_tree.heading("AegisName", text="AegisName", command=lambda: self.sort_treeview_column("AegisName"))
        self.mob_list_tree.column("ID", width=80)
        self.mob_list_tree.column("AegisName", width=200)
        self.mob_list_tree.grid(row=2, column=0, sticky="nsew", padx=(5,0))
        self.mob_list_tree.bind("<<TreeviewSelect>>", self.on_mob_select)

        self.mob_list_scrollbar = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.mob_list_tree.yview)
        self.mob_list_tree.configure(yscrollcommand=self.mob_list_scrollbar.set)
        self.mob_list_scrollbar.grid(row=2, column=1, sticky="ns", padx=(0,5))

        self.btn_frame = ctk.CTkFrame(self.left_frame)
        self.btn_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=1)
        self.btn_add_mob = ctk.CTkButton(self.btn_frame, text="Add New Mob", command=self.add_mob, state="disabled")
        self.btn_add_mob.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.btn_delete_mob = ctk.CTkButton(self.btn_frame, text="Delete Selected", command=self.delete_mob, state="disabled")
        self.btn_delete_mob.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.editor_outer_frame = ctk.CTkFrame(self)
        self.editor_outer_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 10), pady=10)
        self.editor_outer_frame.grid_rowconfigure(1, weight=1)
        self.editor_outer_frame.grid_columnconfigure(0, weight=1)
        
        self.editor_label = ctk.CTkLabel(self.editor_outer_frame, text="Mob Editor", font=ctk.CTkFont(size=16, weight="bold"))
        self.editor_label.grid(row=0, column=0, pady=5, sticky="w", padx=5)
        self.btn_save_mob = ctk.CTkButton(self.editor_outer_frame, text="Save Mob Changes", command=self.save_current_mob, state="disabled")
        self.btn_save_mob.grid(row=0, column=1, pady=5, padx=10, sticky="e")

        self.editor_frame = ctk.CTkScrollableFrame(self.editor_outer_frame, label_text="Select a mob to edit")
        self.editor_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.editor_frame.grid_columnconfigure(1, weight=1)
        self.entry_widgets = {}

    def sort_treeview_column(self, col):
        if self.sort_by_column == col:
            self.sort_reverse_order = not self.sort_reverse_order
        else:
            self.sort_by_column = col
            self.sort_reverse_order = False

        if col == "ID":
            self.mob_data.sort(key=lambda mob: int(mob.get('Id', 0)), reverse=self.sort_reverse_order)
        elif col == "AegisName":
            self.mob_data.sort(key=lambda mob: mob.get('AegisName', '').lower(), reverse=self.sort_reverse_order)

        for c in ("ID", "AegisName"):
            text = c
            if c == self.sort_by_column:
                text += " ▼" if not self.sort_reverse_order else " ▲"
            self.mob_list_tree.heading(c, text=text)
        
        self.filter_mob_list()

    def filter_mob_list(self, *args):
        search_term = self.search_var.get().lower()
        self.mob_list_tree.unbind("<<TreeviewSelect>>")
        self.mob_list_tree.delete(*self.mob_list_tree.get_children())
        
        for i, mob in enumerate(self.mob_data):
            mob_id_str = str(mob.get('Id', ''))
            mob_name_str = mob.get('AegisName', '').lower()
            
            if search_term in mob_id_str or search_term in mob_name_str:
                self.mob_list_tree.insert("", "end", iid=i, values=(mob_id_str, mob.get('AegisName', '')))
        
        self.mob_list_tree.bind("<<TreeviewSelect>>", self.on_mob_select)
        
    def load_file(self):
        path = filedialog.askopenfilename(title="Open mob_db.yml", filetypes=(("YAML files", "*.yml"), ("All files", "*.*")))
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as f: data = yaml.safe_load(f)
            if data.get('Header', {}).get('Type') != 'MOB_DB':
                messagebox.showerror("Error", "This does not appear to be a valid MOB_DB YAML file.")
                return
            
            self.file_path = path
            self.header_data = data['Header']
            self.mob_data = data['Body']
            self.populate_mob_list()
            
            self.btn_save.configure(state="normal")
            self.btn_save_as.configure(state="normal")
            self.btn_add_mob.configure(state="normal")
            self.btn_delete_mob.configure(state="normal")
            self.title(f"rAthena Mob DB YML Editor - {os.path.basename(path)}")
        except Exception as e: messagebox.showerror("Error Loading File", str(e))

    def populate_mob_list(self):
        self.sort_by_column = "ID"
        self.sort_reverse_order = False
        self.mob_data.sort(key=lambda mob: int(mob.get('Id', 0)), reverse=False)
        self.search_var.set("")
        
        self.mob_list_tree.heading("ID", text="ID ▼")
        self.mob_list_tree.heading("AegisName", text="AegisName")
        self.filter_mob_list()

    def on_mob_select(self, event=None):
        if not (selected_items := self.mob_list_tree.selection()): return
        selected_iid = int(selected_items[0])
        self.current_mob_index = selected_iid
        mob = self.mob_data[selected_iid]
        self.display_mob_details(mob)
        self.btn_save_mob.configure(state="normal")

    def display_mob_details(self, mob):
        for widget in self.editor_frame.winfo_children(): widget.destroy()
        self.entry_widgets = {}
        self.editor_frame.configure(label_text=f"Editing: {mob.get('Id')} - {mob.get('AegisName')}")
        full_mob_data = MOB_TEMPLATE.copy(); full_mob_data.update(mob)
        row_counter = 0
        for key, value in full_mob_data.items():
            lbl = ctk.CTkLabel(self.editor_frame, text=key); lbl.grid(row=row_counter, column=0, padx=10, pady=5, sticky="w")
            if isinstance(value, list):
                widget = self._create_list_editor(self.editor_frame, key, value)
            elif isinstance(value, dict):
                widget = self._create_dict_editor(self.editor_frame, key, value)
            else:
                widget = ctk.CTkEntry(self.editor_frame); widget.insert(0, str(value))
            widget.grid(row=row_counter, column=1, padx=5, pady=5, sticky="ew")
            self.entry_widgets[key] = widget
            row_counter += 1

    def _create_list_editor(self, parent, key, items):
        frame = ctk.CTkFrame(parent); frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=("Item", "Rate"), show="headings", height=max(3, len(items)))
        tree.heading("Item", text="Item"); tree.heading("Rate", text="Rate")
        tree.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        for item in items: tree.insert("", "end", values=(item.get("Item", ""), item.get("Rate", "")))
        def add_item():
            item_name = simpledialog.askstring("Input", "Enter Item Name:", parent=self)
            if not item_name: return
            rate = simpledialog.askinteger("Input", "Enter Rate:", parent=self, minvalue=1, maxvalue=10000)
            if rate is not None: tree.insert("", "end", values=(item_name, rate))
        def remove_item():
            if selected := tree.selection(): tree.delete(selected)
        ctk.CTkButton(frame, text="Add", width=60, command=add_item).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ctk.CTkButton(frame, text="Remove", width=60, command=remove_item).grid(row=1, column=1, padx=5, pady=2, sticky="w")
        frame.tree = tree
        return frame

    def _create_dict_editor(self, parent, key, items):
        frame = ctk.CTkFrame(parent); frame.columnconfigure(0, weight=1)
        text_widget = ctk.CTkTextbox(frame, height=max(60, len(items) * 25))
        text_content = "\n".join([f"{k}: {v}" for k, v in items.items()])
        if text_content: text_widget.insert("1.0", text_content)
        text_widget.grid(row=0, column=0, sticky="ew")
        frame.textbox = text_widget
        return frame
        
    def save_current_mob(self):
        if self.current_mob_index is None: return
        new_mob_data = {}
        try:
            for key, widget in self.entry_widgets.items():
                if isinstance(widget, ctk.CTkEntry):
                    value = widget.get()
                    if key in ['Id', 'Level', 'Hp', 'Sp', 'BaseExp', 'JobExp', 'MvpExp', 'Attack', 'Attack2', 'Defense', 'MagicDefense', 'Resistance', 'MagicResistance', 'Str', 'Agi', 'Vit', 'Int', 'Dex', 'Luk', 'AttackRange', 'SkillRange', 'ChaseRange', 'ElementLevel', 'AttackDelay', 'AttackMotion', 'ClientAttackMotion', 'DamageMotion', 'DamageTaken', 'GroupId']:
                        new_mob_data[key] = int(value) if value.isdigit() else 0
                    else: new_mob_data[key] = value
                elif isinstance(widget, ctk.CTkFrame) and hasattr(widget, 'tree'):
                    items = [{'Item': widget.tree.item(c)['values'][0], 'Rate': int(widget.tree.item(c)['values'][1])} for c in widget.tree.get_children()]
                    new_mob_data[key] = items
                elif isinstance(widget, ctk.CTkFrame) and hasattr(widget, 'textbox'):
                    items = {}
                    if text_content := widget.textbox.get("1.0", "end-1c").strip():
                        for line in text_content.split('\n'):
                            if ':' in line:
                                k, v = (s.strip() for s in line.split(':', 1))
                                if v.lower() == 'true': items[k] = True
                                elif v.lower() == 'false': items[k] = False
                                else: items[k] = v
                    new_mob_data[key] = items
            clean_mob_data = {}
            for key, value in new_mob_data.items():
                if key in MOB_TEMPLATE and value == MOB_TEMPLATE[key] and key not in ['Id', 'AegisName', 'Name']: continue
                if key in ['MvpDrops', 'Drops', 'Modes', 'RaceGroups'] and not value: continue
                clean_mob_data[key] = value
            self.mob_data[self.current_mob_index] = clean_mob_data
            self.filter_mob_list()
            self.mob_list_tree.selection_set(str(self.current_mob_index))
            messagebox.showinfo("Success", f"Mob '{clean_mob_data['AegisName']}' updated.")
        except Exception as e: messagebox.showerror("Save Error", f"An error occurred: {e}")

    def add_mob(self):
        new_mob = {'Id': 1001, 'AegisName': 'NEW_MOB_1001', 'Name': 'New Mob'}
        if self.mob_data: new_mob['Id'] = max(m.get('Id', 0) for m in self.mob_data) + 1
        new_mob['AegisName'] = f"MOB_{new_mob['Id']}"
        self.mob_data.append(new_mob)
        self.sort_treeview_column(self.sort_by_column)
        self.filter_mob_list()
        for i, item in enumerate(self.mob_list_tree.get_children()):
             if self.mob_data[int(item)].get('Id') == new_mob['Id']:
                 self.mob_list_tree.selection_set(item)
                 self.mob_list_tree.see(item)
                 break

    def delete_mob(self):
        if not (selected_items := self.mob_list_tree.selection()):
            messagebox.showwarning("Warning", "Please select a mob to delete.")
            return
        selected_iid = int(selected_items[0])
        mob_name = self.mob_data[selected_iid].get('AegisName', 'N/A')
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {mob_name}?"):
            self.mob_data.pop(selected_iid)
            self.filter_mob_list()
            for widget in self.editor_frame.winfo_children(): widget.destroy()
            self.editor_frame.configure(label_text="Select a mob to edit")
            self.current_mob_index = None
            self.btn_save_mob.configure(state="disabled")

    def _get_full_data_dict(self): return {'Header': self.header_data, 'Body': self.mob_data}

    def save_file(self):
        if not self.file_path: self.save
