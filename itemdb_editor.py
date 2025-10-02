import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog, ttk
import yaml
import os

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

ITEM_TEMPLATE = {
    'Id': 0, 'AegisName': 'NEW_ITEM', 'Name': 'New Item', 'Type': 'Etc',
    'SubType': None, 'Buy': 0, 'Sell': 0, 'Weight': 0, 'Attack': 0,
    'MagicAttack': 0, 'Defense': 0, 'Range': 0, 'Slots': 0,
    'Jobs': {'All': True}, 'Classes': {'All': True}, 'Gender': 'Both',
    'Locations': None, 'WeaponLevel': 0, 'ArmorLevel': 0,
    'EquipLevelMin': 0, 'EquipLevelMax': 0, 'Refineable': False,
    'Gradable': False, 'View': 0, 'AliasName': None,
    'Flags': {}, 'Delay': {}, 'Stack': {}, 'NoUse': {}, 'Trade': {},
    'Script': None, 'EquipScript': None, 'UnEquipScript': None
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("rAthena Item DB YML Editor")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")

        self.file_path = None
        self.header_data = {}
        self.item_data = []
        self.current_item_index = None
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

        ctk.CTkLabel(self.left_frame, text="Items", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(5,0))
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.filter_item_list)
        self.search_entry = ctk.CTkEntry(self.left_frame, textvariable=self.search_var, placeholder_text="Search by ID or AegisName...")
        self.search_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f6aa5')])
        style.configure("Treeview.Heading", background="#242424", foreground="white", relief="flat")
        style.map("Treeview.Heading", background=[('active', '#343434')])

        self.item_list_tree = ttk.Treeview(self.left_frame, columns=("ID", "AegisName"), show="headings")
        self.item_list_tree.heading("ID", text="ID ▼", command=lambda: self.sort_treeview_column("ID"))
        self.item_list_tree.heading("AegisName", text="AegisName", command=lambda: self.sort_treeview_column("AegisName"))
        self.item_list_tree.column("ID", width=80)
        self.item_list_tree.column("AegisName", width=200)
        self.item_list_tree.grid(row=2, column=0, sticky="nsew", padx=(5,0))
        self.item_list_tree.bind("<<TreeviewSelect>>", self.on_item_select)

        self.item_list_scrollbar = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.item_list_tree.yview)
        self.item_list_tree.configure(yscrollcommand=self.item_list_scrollbar.set)
        self.item_list_scrollbar.grid(row=2, column=1, sticky="ns", padx=(0,5))

        self.btn_frame = ctk.CTkFrame(self.left_frame)
        self.btn_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=1)
        self.btn_add_item = ctk.CTkButton(self.btn_frame, text="Add New Item", command=self.add_item, state="disabled")
        self.btn_add_item.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.btn_delete_item = ctk.CTkButton(self.btn_frame, text="Delete Selected", command=self.delete_item, state="disabled")
        self.btn_delete_item.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.editor_outer_frame = ctk.CTkFrame(self)
        self.editor_outer_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 10), pady=10)
        self.editor_outer_frame.grid_rowconfigure(1, weight=1)
        self.editor_outer_frame.grid_columnconfigure(0, weight=1)
        
        self.editor_label = ctk.CTkLabel(self.editor_outer_frame, text="Item Editor", font=ctk.CTkFont(size=16, weight="bold"))
        self.editor_label.grid(row=0, column=0, pady=5, sticky="w", padx=5)
        self.btn_save_item = ctk.CTkButton(self.editor_outer_frame, text="Save Item Changes", command=self.save_current_item, state="disabled")
        self.btn_save_item.grid(row=0, column=1, pady=5, padx=10, sticky="e")

        self.editor_frame = ctk.CTkScrollableFrame(self.editor_outer_frame, label_text="Select an item to edit")
        self.editor_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.editor_frame.grid_columnconfigure(1, weight=1)
        self.entry_widgets = {}

    def sort_treeview_column(self, col):
        if self.sort_by_column == col: self.sort_reverse_order = not self.sort_reverse_order
        else: self.sort_by_column = col; self.sort_reverse_order = False
        
        if col == "ID": self.item_data.sort(key=lambda item: int(item.get('Id', 0)), reverse=self.sort_reverse_order)
        elif col == "AegisName": self.item_data.sort(key=lambda item: item.get('AegisName', '').lower(), reverse=self.sort_reverse_order)
        
        for c in ("ID", "AegisName"):
            text = c; text += " ▼" if c == self.sort_by_column and not self.sort_reverse_order else (" ▲" if c == self.sort_by_column else "")
            self.item_list_tree.heading(c, text=text)
        
        self.filter_item_list()

    def filter_item_list(self, *args):
        search_term = self.search_var.get().lower()
        self.item_list_tree.unbind("<<TreeviewSelect>>")
        self.item_list_tree.delete(*self.item_list_tree.get_children())
        for i, item in enumerate(self.item_data):
            if search_term in str(item.get('Id', '')) or search_term in item.get('AegisName', '').lower():
                self.item_list_tree.insert("", "end", iid=i, values=(item.get('Id', ''), item.get('AegisName', '')))
        self.item_list_tree.bind("<<TreeviewSelect>>", self.on_item_select)

    def load_file(self):
        path = filedialog.askopenfilename(title="Open item_db.yml", filetypes=(("YAML files", "*.yml"), ("All files", "*.*")))
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as f: data = yaml.safe_load(f)
            if data.get('Header', {}).get('Type') != 'ITEM_DB':
                messagebox.showerror("Error", "This does not appear to be a valid ITEM_DB YAML file."); return
            self.file_path = path
            self.header_data = data['Header']; self.item_data = data['Body']
            self.populate_item_list()
            self.btn_save.configure(state="normal"); self.btn_save_as.configure(state="normal")
            self.btn_add_item.configure(state="normal"); self.btn_delete_item.configure(state="normal")
            self.title(f"rAthena Item DB YML Editor - {os.path.basename(path)}")
        except Exception as e: messagebox.showerror("Error Loading File", str(e))

    def populate_item_list(self):
        self.sort_by_column = "ID"; self.sort_reverse_order = False
        self.item_data.sort(key=lambda item: int(item.get('Id', 0)))
        self.search_var.set("")
        self.item_list_tree.heading("ID", text="ID ▼"); self.item_list_tree.heading("AegisName", text="AegisName")
        self.filter_item_list()

    def on_item_select(self, event=None):
        if not (selected := self.item_list_tree.selection()): return
        self.current_item_index = int(selected[0])
        self.display_item_details(self.item_data[self.current_item_index])
        self.btn_save_item.configure(state="normal")

    def display_item_details(self, item):
        for widget in self.editor_frame.winfo_children(): widget.destroy()
        self.entry_widgets = {}
        self.editor_frame.configure(label_text=f"Editing: {item.get('Id')} - {item.get('AegisName')}")
        full_item_data = ITEM_TEMPLATE.copy(); full_item_data.update(item)
        
        for i, (key, value) in enumerate(full_item_data.items()):
            lbl = ctk.CTkLabel(self.editor_frame, text=key); lbl.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            
            if key in ['Script', 'EquipScript', 'UnEquipScript']:
                widget = ctk.CTkTextbox(self.editor_frame, height=100)
                if value: widget.insert("1.0", str(value))
            elif isinstance(value, dict):
                widget = self._create_dict_editor(self.editor_frame, key, value)
            else:
                widget = ctk.CTkEntry(self.editor_frame)
                if value is not None: widget.insert(0, str(value))
            
            widget.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            self.entry_widgets[key] = widget

    def _create_dict_editor(self, parent, key, items):
        frame = ctk.CTkFrame(parent); frame.columnconfigure(0, weight=1)
        text_widget = ctk.CTkTextbox(frame, height=max(60, len(items) * 25))
        if items: text_widget.insert("1.0", "\n".join([f"{k}: {v}" for k, v in items.items()]))
        text_widget.grid(row=0, column=0, sticky="ew")
        frame.textbox = text_widget
        return frame
        
    def save_current_item(self):
        if self.current_item_index is None: return
        new_item_data = {}
        try:
            for key, widget in self.entry_widgets.items():
                if isinstance(widget, ctk.CTkEntry):
                    value = widget.get() if widget.get() not in ["", "None"] else None
                    if value is None: new_item_data[key] = None; continue
                    if key in ['Id','Buy','Sell','Weight','Attack','MagicAttack','Defense','Range','Slots','WeaponLevel','ArmorLevel','EquipLevelMin','EquipLevelMax','View']:
                        new_item_data[key] = int(value) if value.isdigit() else 0
                    elif key in ['Refineable', 'Gradable']:
                        new_item_data[key] = value.lower() == 'true'
                    else: new_item_data[key] = value
                elif isinstance(widget, ctk.CTkTextbox):
                    value = widget.get("1.0", "end-1c").strip()
                    new_item_data[key] = value if value else None
                elif isinstance(widget, ctk.CTkFrame) and hasattr(widget, 'textbox'):
                    items = {}
                    if text_content := widget.textbox.get("1.0", "end-1c").strip():
                        for line in text_content.split('\n'):
                            if ':' in line:
                                k, v = (s.strip() for s in line.split(':', 1))
                                if v.lower() == 'true': items[k] = True
                                elif v.lower() == 'false': items[k] = False
                                else: items[k] = v if not v.isdigit() else int(v)
                    new_item_data[key] = items
            
            clean_item_data = {k: v for k, v in new_item_data.items() if v is not None and v != {}}
            self.item_data[self.current_item_index] = clean_item_data
            self.filter_item_list()
            self.item_list_tree.selection_set(str(self.current_item_index))
            messagebox.showinfo("Success", f"Item '{clean_item_data['AegisName']}' updated.")
        except Exception as e: messagebox.showerror("Save Error", f"An error occurred: {e}")

    def add_item(self):
        new_id = max(item.get('Id', 0) for item in self.item_data) + 1 if self.item_data else 501
        new_item = {'Id': new_id, 'AegisName': f'NEW_ITEM_{new_id}', 'Name': 'New Item'}
        self.item_data.append(new_item)
        self.sort_treeview_column(self.sort_by_column)
        for i, item in enumerate(self.item_list_tree.get_children()):
             if self.item_data[int(item)].get('Id') == new_id:
                 self.item_list_tree.selection_set(item); self.item_list_tree.see(item); break

    def delete_item(self):
        if not (selected := self.item_list_tree.selection()):
            messagebox.showwarning("Warning", "Please select an item to delete."); return
        selected_iid = int(selected[0])
        if messagebox.askyesno("Confirm Delete", f"Delete {self.item_data[selected_iid].get('AegisName', 'N/A')}?"):
            self.item_data.pop(selected_iid)
            self.filter_item_list()
            for widget in self.editor_frame.winfo_children(): widget.destroy()
            self.editor_frame.configure(label_text="Select an item to edit")
            self.current_item_index = None; self.btn_save_item.configure(state="disabled")

    def _get_full_data_dict(self): return {'Header': self.header_data, 'Body': self.item_data}

    def save_file(self):
        if not self.file_path: self.save_file_as(); return
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._get_full_data_dict(), f, Dumper=NoAliasDumper, sort_keys=False, indent=2)
            messagebox.showinfo("Success", f"File saved to {self.file_path}")
        except Exception as e: messagebox.showerror("Save Error", str(e))
    
    def save_file_as(self):
        if not (path := filedialog.asksaveasfilename(defaultextension=".yml", filetypes=(("YAML files", "*.yml"),("All files", "*.*")), initialfile="item_db.yml")): return
        self.file_path = path; self.save_file()
        self.title(f"rAthena Item DB YML Editor - {os.path.basename(path)}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
