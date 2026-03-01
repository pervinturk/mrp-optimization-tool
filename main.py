import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from pulp import LpMinimize, LpProblem, LpVariable, lpSum
from collections import defaultdict
import json
import os
import matplotlib.pyplot as plt

class MRPApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Material Requirements Planning (MRP) & Optimization")
        self.root.geometry("1150x750")
        self.root.configure(bg="#1e1e1e")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background="#2e2e2e")
        style.configure("TNotebook.Tab", background="#3c3f41", foreground="white", padding=10)
        style.map("TNotebook.Tab", background=[("selected", "#1e90ff")])

        self.tab_control = ttk.Notebook(self.root)
        
        # Tabs
        self.tab1 = tk.Frame(self.tab_control, bg="#2e2e2e")
        self.tab5 = tk.Frame(self.tab_control, bg="#2e2e2e")
        self.tab2 = tk.Frame(self.tab_control, bg="#2e2e2e")
        self.tab6 = tk.Frame(self.tab_control, bg="#2e2e2e")
        self.tab3 = tk.Frame(self.tab_control, bg="#2e2e2e")
        self.tab4 = tk.Frame(self.tab_control, bg="#2e2e2e")
        
        self.tab_control.add(self.tab1, text='BOM Setup')
        self.tab_control.add(self.tab5, text='BOM Visualizer')
        self.tab_control.add(self.tab2, text='Matrix Calculation')
        self.tab_control.add(self.tab6, text='T-Matrix Steps')
        self.tab_control.add(self.tab3, text='MRP Generation')
        self.tab_control.add(self.tab4, text='LP Optimization Model')
        self.tab_control.pack(expand=1, fill='both')

        self.setup_tab1()
        self.setup_tab2()
        self.setup_tab3()
        self.setup_tab4()
        self.setup_tab5()
        self.setup_tab6()
        
        self.bom_data = []
        self.X_matrix = None
        self.sorted_parts = []

    def setup_tab1(self):
        cols = ("Parent", "Component", "Usage Quantity", "Lead Time (Weeks)")
        self.tree = ttk.Treeview(self.tab1, columns=cols, show='headings')
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='center')
        self.tree.pack(expand=True, fill='both', padx=10, pady=10)
    
        self.selected_product = tk.StringVar()
        self.product_menu = ttk.Combobox(self.tab1, textvariable=self.selected_product)
        self.product_menu.pack(pady=10)
        self.product_menu.bind("<<ComboboxSelected>>", self.load_json_for_product)
        self.refresh_product_menu()
    
        entry_frame = tk.Frame(self.tab1, bg="#2e2e2e")
        entry_frame.pack(pady=10)
    
        self.parent_var = tk.StringVar()
        self.child_var = tk.StringVar()
        self.qty_var = tk.DoubleVar()
        self.lead_var = tk.IntVar()
    
        tk.Label(entry_frame, text="Parent Item:", bg="#2e2e2e", fg="white").grid(row=0, column=0)
        tk.Entry(entry_frame, textvariable=self.parent_var).grid(row=0, column=1, padx=5)
        tk.Label(entry_frame, text="Component:", bg="#2e2e2e", fg="white").grid(row=0, column=2)
        tk.Entry(entry_frame, textvariable=self.child_var).grid(row=0, column=3, padx=5)
        tk.Label(entry_frame, text="Quantity:", bg="#2e2e2e", fg="white").grid(row=0, column=4)
        tk.Entry(entry_frame, textvariable=self.qty_var, width=8).grid(row=0, column=5, padx=5)
        tk.Label(entry_frame, text="Lead Time:", bg="#2e2e2e", fg="white").grid(row=0, column=6)
        tk.Entry(entry_frame, textvariable=self.lead_var, width=8).grid(row=0, column=7, padx=5)
        tk.Button(entry_frame, text="Add Node", command=self.add_row, bg="#1e90ff", fg="white").grid(row=0, column=8, padx=10)
        tk.Button(entry_frame, text="Save JSON", command=self.save_json, bg="#28a745", fg="white").grid(row=0, column=9, padx=10)

    def refresh_product_menu(self):
        # Uses the existing folder name to prevent errors
        if not os.path.exists("urun_agaclari"):
            os.makedirs("urun_agaclari")
        files = [f[:-5] for f in os.listdir("urun_agaclari") if f.endswith(".json")]
        self.product_menu["values"] = files
        if files:
            self.product_menu.current(0)
            self.load_json_for_product()

    def load_json_for_product(self, event=None):
        product = self.selected_product.get()
        if not product:
            return
        try:
            with open(f"urun_agaclari/{product}.json", "r", encoding="utf-8-sig") as f:
                data = json.load(f)
    
            self.bom_data = []
            for item in data:
                self.bom_data.append({
                    "parent": item.get("parent", ""),
                    "child": item.get("child", ""),
                    "qty": float(item.get("qty", 1)),
                    "lead_time": int(item.get("lead_time", 0))
                })
    
            self.tree.delete(*self.tree.get_children())
            for item in self.bom_data:
                self.tree.insert('', 'end', values=(item["parent"], item["child"], item["qty"], item["lead_time"]))
    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load {product}.json: {e}")

    def save_json(self):
        product = self.selected_product.get()
        if not product:
            messagebox.showwarning("Warning", "Please select or type a product name.")
            return
        data = []
        for item in self.tree.get_children():
            parent, child, qty, lead_time = self.tree.item(item)['values']
            data.append({
                "parent": parent,
                "child": child,
                "qty": float(qty),
                "lead_time": int(lead_time)
            })
        try:
            with open(f"urun_agaclari/{product}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Success", f"{product}.json saved successfully.")
            self.bom_data = data
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")

    def add_row(self):
        parent = self.parent_var.get()
        child = self.child_var.get()
        qty = self.qty_var.get()
        lead_time = self.lead_var.get()
        if parent and child and qty > 0:
            self.tree.insert('', 'end', values=(parent, child, qty, lead_time))
            self.bom_data.append({"parent": parent, "child": child, "qty": qty, "lead_time": lead_time})

    def setup_tab2(self):
        self.tab2.configure(bg="#2e2e2e")
    
        frame = tk.Frame(self.tab2, bg="#2e2e2e")
        frame.pack(pady=10, anchor="w")
    
        tk.Label(frame, text="Target Demand:", bg="#2e2e2e", fg="white", font=("Arial", 11)).grid(row=0, column=0, padx=10)
        self.demand_var = tk.IntVar(value=1000)
        tk.Entry(frame, textvariable=self.demand_var, width=15).grid(row=0, column=1, padx=10)
        self.calc_btn = tk.Button(frame, text="Calculate Matrices", command=self.calculate_matrix, bg="#1e90ff", fg="white")
        self.calc_btn.grid(row=0, column=2, padx=10)
    
        content_frame = tk.Frame(self.tab2, bg="#2e2e2e")
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
        self.result_text = tk.Text(content_frame, height=35, width=50, bg="black", fg="lime", font=("Consolas", 10))
        self.result_text.pack(side="left", fill="both", expand=True, padx=(0, 10))
    
        right_frame = tk.Frame(content_frame, bg="#2e2e2e")
        right_frame.pack(side="right", fill="both", expand=True)
    
        self.matrix_text = tk.Text(right_frame, height=18, width=130, bg="black", fg="cyan", font=("Consolas", 10), wrap="none")
        self.matrix_text.pack(side="top", fill="both", expand=True)
        
        x_scroll = tk.Scrollbar(right_frame, orient="horizontal", command=self.matrix_text.xview)
        x_scroll.pack(side="bottom", fill="x")
        self.matrix_text.config(xscrollcommand=x_scroll.set)
    
    def calculate_matrix(self):
        selected = self.selected_product.get()
        if not selected:
            messagebox.showerror("Error", "Please select a product.")
            return
    
        try:
            with open(f"urun_agaclari/{selected}.json", "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON: {e}")
            return
    
        tree = defaultdict(list)
        qty_map = {}
        parts = set()
    
        for item in data:
            p, c, q = item["parent"], item["child"], item["qty"]
            tree[p].append(c)
            qty_map[(p, c)] = q
            parts.update([p, c])
    
        root = list(set(i["parent"] for i in data) - set(i["child"] for i in data))[0]
    
        visited, order = set(), []
        def dfs(n):
            if n in visited: return
            visited.add(n)
            for ch in tree[n]: dfs(ch)
            order.append(n)
    
        dfs(root)
        order.reverse()
    
        idx = {part: i for i, part in enumerate(order)}
        n = len(order)
    
        N = np.zeros((n, n))
        for (p, c), q in qty_map.items():
            if p in idx and c in idx:
                N[idx[c], idx[p]] = q
    
        T = np.identity(n)
        calc_log = "T-MATRIX CALCULATION STEPS (V Vector Logic)\n" + "="*100 + "\n\n"
        step_T_log = "INTERMEDIATE T-MATRICES\n" + "="*100 + "\n\n"
    
        for j in reversed(range(n)):
            V = np.zeros((n, 1))
            V[j, 0] = 1
            calc_log += f"Calculating for column [{order[j]}]:\n"
            calc_log += f"{'Initial V':<20}: {np.round(V.T[0], 5)}\n"
    
            for i in reversed(range(j + 1, n)):
                if N[i, j] != 0:
                    calc_log += f"{'Action':<20}: N[{order[i]}, {order[j]}] = {N[i, j]}\n"
                    calc_log += f"{'Product':<20}: {np.round(N[i, j] * T[:, i], 5)} ← {N[i, j]} × T[:, {order[i]}]\n"
                    V += N[i, j] * T[:, [i]]
                    calc_log += f"{'Updated V':<20}: {np.round(V.T[0], 5)}\n"
    
            T[:, j] = V[:, 0]
            calc_log += f"{'Final V':<20}: {np.round(V.T[0], 5)}\n" + "-"*100 + "\n\n"
    
            df_T_step = pd.DataFrame(T.copy(), index=order, columns=order)
            step_T_log += f"--- T-Matrix after column {order[j]} ---\n"
            step_T_log += df_T_step.to_string()
            step_T_log += "\n\n"
    
        b = np.zeros((n, 1))
        b[0] = self.demand_var.get()
        X = T @ b
    
        df = pd.DataFrame({"Component": order, "Total Requirement (X)": X.flatten()})
        self.X_matrix = df
        self.sorted_parts = order
    
        df_N = pd.DataFrame(N, index=order, columns=order)
        df_T = pd.DataFrame(T, index=order, columns=order)
    
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, df.to_string(index=False))
    
        self.matrix_text.delete("1.0", tk.END)
        self.matrix_text.insert(tk.END, "Direct Requirements Matrix (N):\n")
        self.matrix_text.insert(tk.END, self.format_matrix(df_N))
        self.matrix_text.insert(tk.END, "\n\nTotal Requirements Matrix (T):\n")
        self.matrix_text.insert(tk.END, self.format_matrix(df_T))
    
        self.update_mrp_inputs()

        if hasattr(self, 't_steps_output'):
            self.t_steps_output.delete("1.0", tk.END)
            self.t_steps_output.insert(tk.END, calc_log)
            self.t_matrix_steps_output.delete("1.0", tk.END)
            self.t_matrix_steps_output.insert(tk.END, step_T_log)
        
    def setup_tab6(self):
        self.tab6.configure(bg="#2e2e2e")
    
        frame = tk.Frame(self.tab6, bg="#2e2e2e")
        frame.pack(fill="both", expand=True)
    
        left_text_frame = tk.Frame(frame, bg="#2e2e2e")
        left_text_frame.pack(side="left", fill="both", expand=True)
    
        self.t_steps_output = tk.Text(left_text_frame, bg="black", fg="yellow", font=("Consolas", 10), wrap="none")
        self.t_steps_output.pack(fill="both", expand=True, padx=5, pady=10)
    
        x_scroll_left = tk.Scrollbar(left_text_frame, orient="horizontal", command=self.t_steps_output.xview)
        x_scroll_left.pack(side="bottom", fill="x")
        self.t_steps_output.config(xscrollcommand=x_scroll_left.set)
    
        right_text_frame = tk.Frame(frame, bg="#2e2e2e")
        right_text_frame.pack(side="left", fill="both", expand=True)
    
        self.t_matrix_steps_output = tk.Text(right_text_frame, bg="black", fg="cyan", font=("Consolas", 10), wrap="none")
        self.t_matrix_steps_output.pack(fill="both", expand=True, padx=5, pady=10)
    
        x_scroll_right = tk.Scrollbar(right_text_frame, orient="horizontal", command=self.t_matrix_steps_output.xview)
        x_scroll_right.pack(side="bottom", fill="x")
        self.t_matrix_steps_output.config(xscrollcommand=x_scroll_right.set)

    def setup_tab3(self):
        self.tab3.configure(bg="#2e2e2e")
    
        top_frame = tk.Frame(self.tab3, bg="#2e2e2e")
        top_frame.pack(pady=10, fill="x")
    
        tk.Label(top_frame, text="Delivery Month (1-12):", bg="#2e2e2e", fg="white").pack(side="left", padx=5)
        self.demand_month = tk.IntVar(value=6)
        tk.Entry(top_frame, textvariable=self.demand_month, width=5).pack(side="left", padx=10)
        tk.Button(top_frame, text="Run Single-Period MRP", command=self.calculate_mrp, bg="#28a745", fg="white").pack(side="left", padx=5)
        tk.Button(top_frame, text="Run 52-Week Yearly MRP", command=self.calculate_yearly_mrp, bg="#17a2b8", fg="white").pack(side="left", padx=5)
    
        main_frame = tk.Frame(self.tab3, bg="#2e2e2e")
        main_frame.pack(fill="both", expand=True)
    
        left_frame = tk.Frame(main_frame, bg="#2e2e2e")
        left_frame.pack(side="left", fill="y", padx=10)
    
        header = tk.Frame(left_frame, bg="#2e2e2e")
        header.pack()
        tk.Label(header, text="Component", bg="#2e2e2e", fg="white", width=20).grid(row=0, column=0)
        tk.Label(header, text="On-Hand Inventory", bg="#2e2e2e", fg="white", width=20).grid(row=0, column=1)
        tk.Label(header, text="Safety Stock", bg="#2e2e2e", fg="white", width=20).grid(row=0, column=2)
    
        self.mrp_inputs_frame = tk.Frame(left_frame, bg="#2e2e2e")
        self.mrp_inputs_frame.pack()
    
        right_frame = tk.Frame(main_frame, bg="#2e2e2e")
        right_frame.pack(side="left", fill="both", expand=True)
    
        self.mrp_output = tk.Text(right_frame, height=25, bg="black", fg="orange", font=("Consolas", 10))
        self.mrp_output.pack(side="left", fill="both", expand=True, padx=(0, 5))
    
        self.mrp_year_output = tk.Text(right_frame, height=25, bg="black", fg="cyan", font=("Consolas", 10))
        self.mrp_year_output.pack(side="left", fill="both", expand=True, padx=(0, 10))
    
        self.inventory_entries = {}
        self.safety_entries = {}
                
    def update_mrp_inputs(self):
        for widget in self.mrp_inputs_frame.winfo_children():
            widget.destroy()
    
        self.inventory_entries.clear()
        self.safety_entries.clear()
    
        for idx, part in enumerate(self.sorted_parts, start=1):
            inv_var = tk.IntVar(value=0)
            ss_var = tk.IntVar(value=0)
    
            tk.Label(self.mrp_inputs_frame, text=part, bg="#2e2e2e", fg="white", width=20).grid(row=idx, column=0)
            tk.Entry(self.mrp_inputs_frame, textvariable=inv_var, width=20).grid(row=idx, column=1)
            tk.Entry(self.mrp_inputs_frame, textvariable=ss_var, width=20).grid(row=idx, column=2)
    
            self.inventory_entries[part] = inv_var
            self.safety_entries[part] = ss_var

    # ---- RECURSIVE BOM EXPLOSION ALGORITHM (ERP STANDARD) ----
    def recursive_gross_requirements(self, root, demand):
        G = defaultdict(lambda: [0])  
        G[root][0] = demand
    
        tree = defaultdict(list)
        usage = {}
        for item in self.bom_data:
            tree[item["parent"]].append(item["child"])
            usage[(item["parent"], item["child"])] = item["qty"]
    
        def distribute_demand(parent_node):
            for child_node in tree[parent_node]:
                G[child_node][0] += G[parent_node][0] * usage[(parent_node, child_node)]
                distribute_demand(child_node)
    
        distribute_demand(root)
        return G
            
    def calculate_mrp(self):
        if self.X_matrix is None:
            messagebox.showerror("Error", "Please calculate matrices first!")
            return
    
        selected = self.selected_product.get()
        if not selected:
            messagebox.showerror("Error", "Please select a product.")
            return
    
        try:
            with open(f"urun_agaclari/{selected}.json", "r", encoding="utf-8-sig") as f:
                self.bom_data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load BOM: {e}")
            return
    
        lead_times = defaultdict(int)
        for item in self.bom_data:
            lead_times[item["child"]] = max(lead_times[item["child"]], item.get("lead_time", 0))
    
        num_periods = 1
        
        # Using Recursive Function for pure ERP logic
        root_urun = self.sorted_parts[0]
        demand = self.demand_var.get()
        G = self.recursive_gross_requirements(root_urun, demand)
    
        initial_inventory = {part: self.inventory_entries[part].get() for part in self.sorted_parts}
        safety_stock = {part: self.safety_entries[part].get() for part in self.sorted_parts}
    
        mrp_result = []
        
        self.mrp_output.delete("1.0", tk.END)
        self.mrp_output.insert(tk.END, f"{'Component':<15} | {'G(t)':<8} | {'H(t)':<8} | {'S(t)':<8} | {'N(t)':<8} | {'P(t)':<8} | {'R(t)':<8}\n")
        self.mrp_output.insert(tk.END, "-"*80 + "\n")
    
        for part in self.sorted_parts:
            stock = initial_inventory[part]
            ss = safety_stock[part]
            lt = lead_times.get(part, 0)
    
            h = [stock]
            s = [0] * (num_periods + lt + 1)
            n = [0] * num_periods
            p = [0] * num_periods
            r = [0] * num_periods
    
            for t in range(num_periods):
                requirement = G[part][t] + ss
                available = h[t] + s[t]
                n[t] = max(0, requirement - available)
    
                if n[t] > 0:
                    p[t] = n[t]
                    order_period = t - lt
                    if order_period >= 0:
                        r[order_period] = p[t]
                    else:
                        r[0] = p[t]
                    s[t + lt] = p[t]
    
                h.append(h[t] + s[t] - G[part][t])
    
            mrp_result.append({
                "Component": part,
                "Gross": G[part],
                "Net": n,
                "Planned": p,
                "Released": r,
                "LeadTime": lt
            })
            
            self.mrp_output.insert(tk.END, f"{part:<15} | {G[part][0]:<8.1f} | {stock:<8.1f} | {ss:<8.1f} | {n[0]:<8.1f} | {p[0]:<8.1f} | {r[0]:<8.1f}\n")
        
        df_plan = pd.DataFrame({
            "Component": [e["Component"] for e in mrp_result],
            "Order Amount": [e["Released"][0] for e in mrp_result],
            "Order Month": [1 - e["LeadTime"] if 1 - e["LeadTime"] > 0 else 1 for e in mrp_result]
        })
    
        fig, ax = plt.subplots(figsize=(12, len(df_plan)*0.5 + 1.5))
        ax.axis('off')
        table = ax.table(cellText=df_plan.values, colLabels=df_plan.columns, loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        plt.title("Purchasing / Production Plan (Single Period)", fontsize=14, pad=20)
        plt.tight_layout()
        plt.show()
        
    def compute_total_lead_times(self, root):
        tree = defaultdict(list)
        lead_map = {}
    
        for item in self.bom_data:
            tree[item['parent']].append(item['child'])
            lead_map[item['child']] = item.get('lead_time', 0)
    
        total_leads = {}
    
        def dfs(node, acc):
            if node in total_leads:
                total_leads[node] = max(total_leads[node], acc)
            else:
                total_leads[node] = acc
            for child in tree.get(node, []):
                dfs(child, acc + lead_map.get(child, 0))
    
        dfs(root, 0)
        return total_leads

    def calculate_yearly_mrp(self):
        if self.X_matrix is None:
            messagebox.showerror("Error", "Please calculate matrices first!")
            return
    
        delivery_month = self.demand_month.get()
        if delivery_month < 1 or delivery_month > 12:
            messagebox.showerror("Error", "Delivery month must be between 1 and 12.")
            return
    
        delivery_week = delivery_month * 4
        root = self.sorted_parts[0]
        total_leads = self.compute_total_lead_times(root)
        
        demand = self.demand_var.get()
        G_totals = self.recursive_gross_requirements(root, demand)

        weeks = 52 # Robust 52-week cycle logic
        result = []
    
        for b in self.sorted_parts:
            amount = G_totals[b][0]
            weekly_plan = [0] * weeks
            actual_delivery_week = delivery_week - total_leads.get(b, 0)
            
            if actual_delivery_week < 1:
                weekly_plan[0] = amount
            else:
                weekly_plan[actual_delivery_week - 1] = amount
        
            stock = self.inventory_entries[b].get()
            safety = self.safety_entries[b].get()
        
            lead_times = defaultdict(int)
            for item in self.bom_data:
                lead_times[item["child"]] = max(lead_times[item["child"]], item.get("lead_time", 0))
        
            lt = lead_times.get(b, 0)
        
            h = [stock]
            s = [0] * (weeks + lt + 1)
            n = [0] * weeks
            p = [0] * weeks
            r = [0] * weeks
        
            for t in range(weeks):
                gross = weekly_plan[t]
                if weekly_plan[t] > 0:
                    gross += safety
                available = h[t] + s[t]
                net = max(0, gross - available)
                n[t] = net
        
                if net > 0:
                    p[t] = net
                    order_t = t - lt
                    if order_t >= 0:
                        r[order_t] += net  
                    else:
                        r[0] += net
                    s[t + lt] = net
        
                h.append(h[t] + s[t] - weekly_plan[t])
        
            order_weeks = [t for t, qty in enumerate(r) if qty > 0]
            if order_weeks:
                first_week = min(order_weeks) + 1
                total_qty = sum(r[t] for t in order_weeks)
            else:
                first_week = "-"
                total_qty = 0
        
            result.append({
                'Component': b,
                'First Order Week': first_week,
                'Total Order Quantity': round(total_qty, 2)
            })
    
        df = pd.DataFrame(result)
    
        self.mrp_year_output.delete("1.0", tk.END)
        if df.empty:
            self.mrp_year_output.insert(tk.END, "No orders required in any week.\n")
        else:
            self.mrp_year_output.insert(tk.END, df.to_string(index=False))
    
        if not df.empty:
            fig, ax = plt.subplots(figsize=(12, len(df) * 0.3 + 1.5))
            ax.axis("off")
            table = ax.table(cellText=df.values, colLabels=df.columns, loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.1, 1.3)
            plt.title(f"52-Week Order Schedule (Delivery Month: {delivery_month})", fontsize=14, pad=20)
            plt.tight_layout()
            plt.show()
    
    def setup_tab4(self):
        self.tab4.configure(bg="#2e2e2e")
    
        tk.Label(self.tab4, text="Linear Programming (LP) Model Inputs", bg="#2e2e2e", fg="white", font=("Arial", 10, "bold")).pack(pady=(3, 2))
    
        main_frame = tk.Frame(self.tab4, bg="#2e2e2e")
        main_frame.pack(fill="both", expand=True)
    
        left_frame = tk.Frame(main_frame, bg="#2e2e2e", width=340)
        left_frame.pack(side="left", padx=(8, 4), anchor="n")
    
        right_frame = tk.Frame(main_frame, bg="#2e2e2e")
        right_frame.pack(side="left", fill="both", expand=True)
    
        self.lp_entries = []
        tk.Label(left_frame, text="Month", bg="#2e2e2e", fg="white", font=("Arial", 8), width=5).grid(row=0, column=0)
        tk.Label(left_frame, text="Demand", bg="#2e2e2e", fg="white", font=("Arial", 8), width=10).grid(row=0, column=1)
        tk.Label(left_frame, text="Working Days", bg="#2e2e2e", fg="white", font=("Arial", 8), width=12).grid(row=0, column=2)
    
        default_demand = [1199, 1247, 1700, 3571, 3987, 4316, 4195, 3862, 3402, 2586, 1840, 1513]
        default_days = [22, 20, 23, 21, 23, 22, 21, 22, 23, 22, 21, 22]
    
        for i in range(12):
            tk.Label(left_frame, text=f"{i+1}", bg="#2e2e2e", fg="white", font=("Arial", 8), width=5).grid(row=i+1, column=0)
            demand_var = tk.IntVar(value=default_demand[i])
            days_var = tk.IntVar(value=default_days[i])
            tk.Entry(left_frame, textvariable=demand_var, width=10).grid(row=i+1, column=1)
            tk.Entry(left_frame, textvariable=days_var, width=12).grid(row=i+1, column=2)
            self.lp_entries.append((demand_var, days_var))
    
        row = 14
    
        self.lp_hiring = tk.IntVar(value=6000)
        self.lp_firing = tk.IntVar(value=10000)
        self.lp_inventory = tk.IntVar(value=5)
        self.lp_regular = tk.IntVar(value=50)
        self.lp_overtime = tk.IntVar(value=80)
        self.lp_idle = tk.IntVar(value=20)
        self.lp_sub = tk.IntVar(value=100)
    
        tk.Label(left_frame, text="Cost Parameters ($/TL)", bg="#2e2e2e", fg="white", font=("Arial", 8, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", pady=(5, 0))
        row += 1
        for text, var in [
            ("Hiring Cost:", self.lp_hiring),
            ("Firing Cost:", self.lp_firing),
            ("Holding Cost:", self.lp_inventory),
            ("Regular Prod Cost:", self.lp_regular),
            ("Overtime Cost:", self.lp_overtime),
            ("Idle Time Cost:", self.lp_idle),
            ("Subcontract Cost:", self.lp_sub)
        ]:
            tk.Label(left_frame, text=text, bg="#2e2e2e", fg="white", font=("Arial", 8)).grid(row=row, column=0, columnspan=2, sticky="w")
            tk.Entry(left_frame, textvariable=var, width=10).grid(row=row, column=2)
            row += 1
    
        self.lp_K = tk.IntVar(value=4)
        self.lp_W0 = tk.IntVar(value=25)
        self.lp_I0 = tk.IntVar(value=1000)
    
        tk.Label(left_frame, text="Production Parameters", bg="#2e2e2e", fg="white", font=("Arial", 8, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", pady=(5, 0))
        row += 1
        for text, var in [
            ("Daily Capacity (units):", self.lp_K),
            ("Initial Workforce:", self.lp_W0),
            ("Initial Inventory:", self.lp_I0)
        ]:
            tk.Label(left_frame, text=text, bg="#2e2e2e", fg="white", font=("Arial", 8)).grid(row=row, column=0, columnspan=2, sticky="w")
            tk.Entry(left_frame, textvariable=var, width=10).grid(row=row, column=2)
            row += 1
    
        self.lp_max_overtime = tk.IntVar(value=500)
        self.lp_max_sub = tk.IntVar(value=3000)
        self.lp_min_worker = tk.IntVar(value=25)
        self.lp_max_worker = tk.IntVar(value=35)
        self.lp_min_inv = tk.IntVar(value=500)
        self.lp_max_inv = tk.IntVar(value=5000)
        self.lp_max_idle = tk.IntVar(value=2000)
    
        tk.Label(left_frame, text="System Constraints", bg="#2e2e2e", fg="white", font=("Arial", 8, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", pady=(5, 0))
        row += 1
        for text, var in [
            ("Max Overtime (units):", self.lp_max_overtime),
            ("Max Subcontract (units):", self.lp_max_sub),
            ("Min Workforce:", self.lp_min_worker),
            ("Max Workforce:", self.lp_max_worker),
            ("Min Inventory:", self.lp_min_inv),
            ("Max Inventory:", self.lp_max_inv),
            ("Max Idle Time:", self.lp_max_idle)
        ]:
            tk.Label(left_frame, text=text, bg="#2e2e2e", fg="white", font=("Arial", 8)).grid(row=row, column=0, columnspan=2, sticky="w")
            tk.Entry(left_frame, textvariable=var, width=10).grid(row=row, column=2)
            row += 1
    
        tk.Button(left_frame, text="Run Optimization", command=self.run_lp_model, bg="#1e90ff", fg="white", font=("Arial", 8, "bold")).grid(row=row+1, column=0, columnspan=3, pady=(8, 3))
    
        self.lp_output = tk.Text(right_frame, height=45, bg="black", fg="cyan", font=("Consolas", 10), wrap="none")
        self.lp_output.pack(fill="both", expand=True, padx=10, pady=10)
                            
    def run_lp_model(self):
        months = list(range(12))
        demand = [entry[0].get() for entry in self.lp_entries]
        working_days = [entry[1].get() for entry in self.lp_entries]
        K = self.lp_K.get()
        W0 = self.lp_W0.get()
        I0 = self.lp_I0.get()
    
        cost = {
            "hiring": self.lp_hiring.get(),
            "firing": self.lp_firing.get(),
            "inventory": self.lp_inventory.get(),
            "regular": self.lp_regular.get(),
            "overtime": self.lp_overtime.get(),
            "idle": self.lp_idle.get(),
            "sub": self.lp_sub.get()
        }

        max_ot = self.lp_max_overtime.get()
        max_sub = self.lp_max_sub.get()
        min_w = self.lp_min_worker.get()
        max_w = self.lp_max_worker.get()
        min_inv = self.lp_min_inv.get()
        max_inv = self.lp_max_inv.get()
        max_idle = self.lp_max_idle.get()
    
        prob = LpProblem("Aggregate_Planning_LP", LpMinimize)
    
        W = {t: LpVariable(f"W_{t}", min_w, max_w, cat="Integer") for t in months}
        H = {t: LpVariable(f"H_{t}", 0, None, cat="Integer") for t in months}
        F = {t: LpVariable(f"F_{t}", 0, None, cat="Integer") for t in months}
        P = {t: LpVariable(f"P_{t}", 0) for t in months}
        O = {t: LpVariable(f"O_{t}", 0, max_ot) for t in months}
        U = {t: LpVariable(f"U_{t}", 0, max_idle) for t in months}
        S = {t: LpVariable(f"S_{t}", 0, max_sub) for t in months}
        I = {t: LpVariable(f"I_{t}", min_inv, max_inv) for t in months}
    
        prob += lpSum(
            cost["hiring"] * H[t] + cost["firing"] * F[t] + cost["inventory"] * I[t] +
            cost["regular"] * P[t] + cost["overtime"] * O[t] +
            cost["idle"] * U[t] + cost["sub"] * S[t]
            for t in months
        )
    
        prob += W[0] == W0 + H[0] - F[0]
        prob += I[0] == I0 + P[0] + S[0] - demand[0]
    
        for t in months[1:]:
            prob += W[t] == W[t - 1] + H[t] - F[t]
            prob += I[t] == I[t - 1] + P[t] + S[t] - demand[t]
            prob += P[t] <= K * working_days[t] * W[t] + O[t] - U[t]
            prob += P[t] + S[t] + I[t - 1] >= demand[t]
    
        prob.solve()
    
        self.lp_output.delete('1.0', tk.END)
        self.lp_output.insert(tk.END, f"*** MINIMIZED TOTAL COST: {prob.objective.value():,.2f} ***\n\n", "highlight")
    
        months_names = ["January", "February", "March", "April", "May", "June",
                        "July", "August", "September", "October", "November", "December"]
    
        col_width = 45
        for block in range(0, 12, 3):
            lines = [""] * 8
            for i in range(3):
                t = block + i
                if t >= 12:
                    continue
                lines[0] += f"{months_names[t]}:".ljust(col_width)
                lines[1] += f"  Workforce:        {W[t].value():.1f} workers".ljust(col_width)
                lines[2] += f"  Production Qty:   {P[t].value():.1f} units".ljust(col_width)
                lines[3] += f"  Inventory Qty:    {I[t].value():.1f} units".ljust(col_width)
                lines[4] += f"  Overtime Prod:    {O[t].value():.1f} units".ljust(col_width)
                lines[5] += f"  Subcontracting:   {S[t].value():.1f} units".ljust(col_width)
                lines[6] += f"  Hired Workers:    {H[t].value():.1f} workers".ljust(col_width)
                lines[7] += f"  Fired Workers:    {F[t].value():.1f} workers".ljust(col_width)
            for line in lines:
                self.lp_output.insert(tk.END, line + "\n")
            self.lp_output.insert(tk.END, "\n\n")
    
        self.lp_output.tag_config("highlight", foreground="yellow", font=("Consolas", 11, "bold"))
            
    def setup_tab5(self):
        self.canvas = tk.Canvas(self.tab5, bg="#1e1e1e", scrollregion=(0, 0, 2000, 1000))
        self.canvas.pack(fill="both", expand=True)
        self.draw_btn = tk.Button(self.tab5, text="Render Precedence Diagram", command=self.draw_tree_canvas, bg="#1e90ff", fg="white")
        self.draw_btn.pack(pady=10)
        self.save_btn = tk.Button(self.tab5, text="Save Node Data to JSON", command=self.save_canvas_to_json, bg="#28a745", fg="white")
        self.save_btn.pack(pady=5)
        
    def draw_tree_canvas(self):
        self.load_json_for_product()
        self.canvas.delete("all")
        self.node_coords = {}
        self.node_items = {}
        self.connections = []  # BUG FIXED: List instead of dictionary
    
        if not self.bom_data:
            messagebox.showwarning("Warning", "BOM is empty. Please load or add a product.")
            return
    
        tree = defaultdict(list)
        for item in self.bom_data:
            tree[item["parent"]].append((item["child"], item["qty"]))
    
        levels = defaultdict(list)
        visited = set()
    
        def assign_levels(node, level=0):
            if node in visited:
                return
            visited.add(node)
            levels[level].append(node)
            for child, _ in tree.get(node, []):
                assign_levels(child, level + 1)
    
        all_parents = set(item["parent"] for item in self.bom_data)
        all_children = set(item["child"] for item in self.bom_data)
        roots = list(all_parents - all_children)
        if not roots:
            messagebox.showerror("Error", "Root node not found.")
            return
    
        root = roots[0]
        assign_levels(root)
    
        y_gap = 140
        node_radius = 55
        canvas_width = self.canvas.winfo_width() or 1400
    
        for level in sorted(levels):
            nodes = levels[level]
            count = len(nodes)
            x_gap = 160
            total_width = (count - 1) * x_gap
            x_start = (canvas_width - total_width) // 2
    
            for i, node in enumerate(nodes):
                x = x_start + i * x_gap
                y = 70 + level * y_gap
    
                qty = next((item["qty"] for item in self.bom_data if item["child"] == node), 1)
                lead = next((item["lead_time"] for item in self.bom_data if item["child"] == node), 0)
    
                oval = self.canvas.create_oval(
                    x - node_radius, y - node_radius, x + node_radius, y + node_radius,
                    fill="#4a90e2", outline="white"
                )
                label = self.canvas.create_text(x, y - 35, text=node, fill="white", font=("Arial", 9, "bold"))
    
                self.canvas.create_text(x - 20, y - 8, text="Qty:", fill="white", anchor="e", font=("Arial", 7))
                self.canvas.create_text(x - 20, y + 12, text="Lead:", fill="white", anchor="e", font=("Arial", 7))
    
                qty_var = tk.StringVar(value=str(qty))
                lead_var = tk.StringVar(value=str(lead))
    
                qty_entry = tk.Entry(self.canvas, textvariable=qty_var, width=5, justify="center")
                lead_entry = tk.Entry(self.canvas, textvariable=lead_var, width=5, justify="center")
    
                self.canvas.create_window(x + 10, y - 8, window=qty_entry)
                self.canvas.create_window(x + 10, y + 12, window=lead_entry)
    
                def save_vars(node_name=node, qv=qty_var, lv=lead_var):
                    try:
                        new_qty = float(qv.get())
                        new_lead = int(lv.get())
                    except ValueError:
                        return
                    for item in self.bom_data:
                        if item["child"] == node_name:
                            item["qty"] = new_qty
                            item["lead_time"] = new_lead
                            break
                    self.draw_tree_canvas()
    
                qty_entry.bind("<Return>", lambda e: save_vars())
                lead_entry.bind("<Return>", lambda e: save_vars())
    
                self.node_coords[node] = (x, y)
                self.node_items[node] = (oval, label, qty_entry, lead_entry)
    
        for parent, children in tree.items():
            x1, y1 = self.node_coords[parent]
            for child, qty in children:
                x2, y2 = self.node_coords[child]
                line = self.canvas.create_line(x1, y1 + node_radius, x2, y2 - node_radius, fill="white", arrow=tk.LAST)
                qty_text = self.canvas.create_text((x1 + x2) // 2, (y1 + y2) // 2, text=str(qty), fill="orange", font=("Arial", 9, "bold"))
                self.connections.append((parent, child, qty, line, qty_text))  # BUG FIXED: list append method
    
    def format_matrix(self, df):
        labels = list(df.columns) + list(df.index)
        max_label_len = max(len(str(x)) for x in labels)
        cell_width = max(8, max_label_len + 1) 
        
        header = f"{'':<{cell_width}}" + "".join(f"{col:>{cell_width}}" for col in df.columns) + "\n\n"
        
        body = ""
        for idx, row in df.iterrows():
            body += f"{idx:<{cell_width}}" + "".join(f"{val:>{cell_width}.1f}" for val in row.values) + "\n\n"
        
        return header + body

    def save_canvas_to_json(self):
        product = self.selected_product.get()
        if not product:
            messagebox.showwarning("Warning", "No product selected.")
            return
    
        data = []
        for parent, child, qty, *_ in self.connections:
            x, y = self.node_coords.get(child, (0, 0))
    
            _, _, qty_entry, lead_entry = self.node_items[child]
            try:
                qty_val = float(qty_entry.get())
                lead_val = int(lead_entry.get())
            except ValueError:
                qty_val = 1
                lead_val = 0
    
            data.append({
                "parent": parent,
                "child": child,
                "qty": qty_val,
                "x": x,
                "y": y,
                "lead_time": lead_val
            })
    
        try:
            if not os.path.exists("urun_agaclari"):
                os.makedirs("urun_agaclari")
            with open(f"urun_agaclari/{product}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Success", f"{product}.json node data saved.")
            self.bom_data = data
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")

if __name__ == "__main__":
    app_root = tk.Tk()
    app = MRPApp(app_root)
    app_root.mainloop()