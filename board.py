import tkinter as tk
from tkinter import ttk, messagebox
import time
from algorithms import BFSSolver, CSPSolver

BOARD_SIZE = 8
CELL_SIZE = 60

# ==========================================
# 3. UI APPLICATION
# ==========================================
class QueensApp(tk.Tk):
    def __init__(self, n=8):
        super().__init__()
        self.geometry("900x760")
        self.title(f"{n}-Queens Solver")
        self.resizable(False, False)

        self.n = n
        self.solver = BFSSolver(n)
        
        # Animation settings
        self.delay = 200       
        self.anim_speed = 15   
        self.anim_steps = 15   
        
        self.default_initial_1based = [1, 5, 8, 6, 3, 7, 2, 4] 

        self.running = False
        self.is_animating = False
        self._run_job = None 

        self._create_widgets()
        self._load_default() 

    def _create_widgets(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(main, width=CELL_SIZE * self.n, height=CELL_SIZE * self.n, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nw')

        cfg = ttk.Frame(main)
        cfg.grid(row=0, column=1, sticky='nw', padx=12)

        # Algo Selection
        ttk.Label(cfg, text="Algorithm:", font="bold").grid(row=0, column=0, sticky='w', pady=(0, 5))
        self.algo_var = tk.StringVar(value="BFS")
        self.algo_combo = ttk.Combobox(cfg, textvariable=self.algo_var, 
                                       values=["BFS", "CSP (Backtracking)"], state="readonly", width=22)
        self.algo_combo.grid(row=1, column=0, sticky='w', pady=(0, 15))
        self.algo_combo.bind("<<ComboboxSelected>>", self.on_algo_change)

        # Config Modes
        ttk.Label(cfg, text="Configuration Mode:", font="bold").grid(row=2, column=0, sticky='w', pady=(0, 5))
        self.mode_var = tk.StringVar(value='default')
        ttk.Radiobutton(cfg, text='Default configuration', variable=self.mode_var, value='default',
                                command=self.on_mode_change).grid(row=3, column=0, sticky='w')
        ttk.Radiobutton(cfg, text='Custom configuration', variable=self.mode_var, value='custom',
                                command=self.on_mode_change).grid(row=4, column=0, sticky='w')
        
        ttk.Separator(cfg, orient='horizontal').grid(row=5, column=0, sticky='ew', pady=10)

        # Custom Inputs
        self.custom_frame = ttk.Frame(cfg)
        self.custom_frame.grid(row=6, column=0, sticky='w', pady=(0, 8))
        ttk.Label(self.custom_frame, text='Enter 8 row numbers (1-8):').grid(row=0, column=0, columnspan=self.n, sticky='w')
        self.entries = []
        for i in range(self.n):
            e = ttk.Entry(self.custom_frame, width=3, justify='center')
            e.grid(row=1, column=i, padx=2, pady=4)
            self.entries.append(e)
            e.insert(0, str(self.default_initial_1based[i]))

        # Buttons
        btns = ttk.Frame(cfg)
        btns.grid(row=7, column=0, sticky='nw', pady=(10, 0))
        self.start_btn = ttk.Button(btns, text='Start', command=self.on_start)
        self.start_btn.grid(row=0, column=0, sticky='ew', padx=2)
        self.step_btn = ttk.Button(btns, text='Step', command=self.on_step, state='disabled')
        self.step_btn.grid(row=0, column=1, sticky='ew', padx=2)
        self.run_btn = ttk.Button(btns, text='Run', command=self.on_run, state='disabled')
        self.run_btn.grid(row=0, column=2, sticky='ew', padx=2)
        self.reset_btn = ttk.Button(btns, text='Reset', command=self.on_reset)
        self.reset_btn.grid(row=1, column=0, columnspan=3, sticky='ew', pady=4)

        ttk.Separator(cfg, orient='horizontal').grid(row=8, column=0, sticky='ew', pady=10)

        # Status
        status_frame = ttk.Frame(cfg)
        status_frame.grid(row=9, column=0, sticky='nw')
        ttk.Label(status_frame, text="Status:", font="bold").grid(row=0, column=0, sticky='w')
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground='blue')
        self.status_label.grid(row=0, column=1, sticky='w', padx=5)

        self.stats_var = tk.StringVar(value="Nodes: 0 | Time: 0.00s")
        self.stats_label = ttk.Label(cfg, textvariable=self.stats_var)
        self.stats_label.grid(row=10, column=0, sticky='w', pady=(5, 0))

        self.on_mode_change() 

    def _draw_board(self):
        self.canvas.delete("all")
        for r in range(self.n):
            for c in range(self.n):
                color = '#DDBB88' if (r + c) % 2 == 0 else '#AA6633'
                self.canvas.create_rectangle(c * CELL_SIZE, r * CELL_SIZE, 
                                           (c+1) * CELL_SIZE, (r+1) * CELL_SIZE, 
                                           fill=color, tags="square")

    def _ensure_active_queen(self, col, row):
        target_x = col * CELL_SIZE + CELL_SIZE / 2
        target_y = row * CELL_SIZE + CELL_SIZE / 2
        
        item = self.canvas.find_withtag("active_queen")
        
        if not item:
            self.canvas.create_text(target_x, target_y, text='♕', font=('Arial', int(CELL_SIZE * 0.7)), 
                                    fill='black', tags="active_queen")
        else:
            current_coords = self.canvas.coords(item)
            current_x = current_coords[0]
            current_y = current_coords[1]

            # Only teleport X if column changed significantly
            if abs(current_x - target_x) > 5: 
                self.canvas.coords(item, target_x, target_y)
            else:
                # Leave Y alone for animation
                self.canvas.coords(item, target_x, current_y)

            self.canvas.lift(item) 

    def animate_active_queen(self, target_row, on_complete=None):
        self.is_animating = True
        item = self.canvas.find_withtag("active_queen")
        if not item:
            if on_complete: on_complete()
            self.is_animating = False
            return

        coords = self.canvas.coords(item)
        current_y = coords[1]
        target_y = target_row * CELL_SIZE + CELL_SIZE / 2
        dist = target_y - current_y
        
        if abs(dist) < 1:
            if on_complete: on_complete()
            self.is_animating = False
            return

        steps = self.anim_steps
        dy = dist / steps

        def _anim_step(s):
            if s > 0:
                self.canvas.move(item, 0, dy)
                self.after(self.anim_speed, lambda: _anim_step(s - 1))
            else:
                current_x = self.canvas.coords(item)[0]
                self.canvas.coords(item, current_x, target_y)
                self.is_animating = False
                if on_complete: on_complete()

        _anim_step(steps)

    def _update_board_state(self, fixed_queen_rows, current_col, trial_row, show_ghost_in_current=False):
        # Clear non-active/non-board items
        for item in self.canvas.find_all():
            tags = self.canvas.gettags(item)
            if "active_queen" in tags or "square" in tags:
                continue
            self.canvas.delete(item)

        # Highlight
        if current_col is not None and current_col < self.n:
            self.canvas.create_rectangle(current_col * CELL_SIZE, 0, 
                                       (current_col+1) * CELL_SIZE, self.n * CELL_SIZE, 
                                       outline='blue', width=2, tags="highlight")
            self.canvas.tag_lower("highlight")

        # Fixed Queens
        for col, row in enumerate(fixed_queen_rows):
            x_center = col * CELL_SIZE + CELL_SIZE / 2
            y_center = row * CELL_SIZE + CELL_SIZE / 2
            self.canvas.create_text(x_center, y_center, text='♕', font=('Arial', int(CELL_SIZE * 0.7)), 
                                    fill='black', tags="fixed_queen")

        # Ghost Queens
        start_col = len(fixed_queen_rows)
        for col in range(start_col, self.n):
            # Only hide ghost in current col if we are NOT asked to show it
            if col == current_col and not show_ghost_in_current:
                continue
            
            row = self.solver.initial[col]
            x_center = col * CELL_SIZE + CELL_SIZE / 2
            y_center = row * CELL_SIZE + CELL_SIZE / 2
            self.canvas.create_text(x_center, y_center, text='♕', font=('Arial', int(CELL_SIZE * 0.7)), 
                                    fill='gray', tags="ghost_queen")

    def _update_stats(self):
        elapsed = time.time() - self.solver.start_time if self.solver.start_time else 0
        self.stats_var.set(f"Nodes: {self.solver.nodes} | Time: {elapsed:.2f}s")

    def _update_controls(self, is_running=False):
        if is_running:
             self.start_btn.config(state='disabled')
             self.step_btn.config(state='disabled')
             self.run_btn.config(state='disabled')
             self.algo_combo.config(state='disabled')
        elif self.solver.finished or not self.solver.valid:
             self.start_btn.config(state='disabled')
             self.step_btn.config(state='disabled')
             self.run_btn.config(state='disabled')
             self.algo_combo.config(state='readonly')
        else:
             self.start_btn.config(state='disabled') 
             self.step_btn.config(state='normal')
             self.run_btn.config(state='normal')
             self.algo_combo.config(state='readonly')

    def _load_default(self):
        for i, val in enumerate(self.default_initial_1based):
            self.entries[i].delete(0, tk.END)
            self.entries[i].insert(0, str(val))
        self.on_reset()

    def on_algo_change(self, event=None):
        self.on_reset()

    def on_mode_change(self):
        mode = self.mode_var.get()
        state = 'normal' if mode == 'custom' else 'disabled'
        for e in self.entries:
            e.config(state=state)
        self.on_reset()

    def on_reset(self):
        self.running = False
        self.is_animating = False
        if self._run_job is not None:
            self.after_cancel(self._run_job)
            self._run_job = None
        
        algo = self.algo_var.get()
        if algo.startswith("BFS"):
            self.solver = BFSSolver(self.n)
        else:
            self.solver = CSPSolver(self.n)

        try:
            rows_1based = [int(e.get()) for e in self.entries]
            if any(r < 1 or r > self.n for r in rows_1based):
                 rows_1based = self.default_initial_1based
        except:
            rows_1based = self.default_initial_1based

        self.solver.set_initial(rows_1based)
        self._draw_board()
        
        self._update_board_state([], current_col=-1, trial_row=None, show_ghost_in_current=True)
        
        self.status_var.set(f"Ready ({algo}). Press Start.")
        self.stats_var.set("Nodes: 0 | Time: 0.00s")
        self.start_btn.config(state='normal')
        self.step_btn.config(state='disabled')
        self.run_btn.config(state='disabled')
        self.algo_combo.config(state='readonly')
        
    def on_start(self):
        self.step_btn.config(state='normal')
        self.run_btn.config(state='normal')
        self.start_btn.config(state='disabled')
        self.on_step()

    def on_step(self):
        if self.running or self.is_animating: return
        self.running = True 
        self.run_solver(single_step=True)
        
    def on_run(self):
        if self.running or self.is_animating: return
        self.running = True
        self._update_controls(is_running=True)
        self.run_solver()

    def run_solver(self, single_step=False):
        if not self.running and not single_step:
            self._update_controls(is_running=False)
            return
        
        if self.solver.finished or not self.solver.valid:
            self.running = False
            self._update_controls(is_running=False)
            return

        result, data = self.solver.step()
        self._update_stats()

        def schedule_next():
            if single_step:
                self.running = False
                self._update_controls(is_running=False)
            elif self.running:
                self._run_job = self.after(self.delay, self.run_solver)

        if result == 'searching':
            col = data['col']
            row = data['row']
            self._update_board_state(self.solver.fixed, current_col=col, trial_row=row, show_ghost_in_current=False)
            self._ensure_active_queen(col, row)
            self.status_var.set(f"Checking column {col + 1}, row {row + 1}...")
            self.animate_active_queen(row, on_complete=schedule_next)

        elif result == 'backtracking':
            col = data['col']
            self._update_board_state(self.solver.fixed, current_col=col, trial_row=None, show_ghost_in_current=False)
            self.canvas.delete("active_queen")
            self._ensure_active_queen(col, data['row'])
            self.status_var.set(f"Backtracking to column {col + 1}...")
            self.after(self.delay, schedule_next)

        elif result == 'fixed':
            col = data['col']
            row = data['row']
            self._update_board_state(data['state'], current_col=self.solver.col, trial_row=None, show_ghost_in_current=True)
            self.canvas.delete("active_queen")
            self.status_var.set(f"Fixed column {col + 1}. Moving to next...")
            schedule_next()
            
        elif result == 'solution':
            self.running = False
            self.canvas.delete("active_queen")
            self.status_var.set(f"Solution found! Time: {time.time() - self.solver.start_time:.2f}s")
            self._update_board_state(data['state'], current_col=self.n, trial_row=None)
            messagebox.showinfo("Result", "Solution found!")
            self._update_controls(is_running=False)

        elif result == 'invalid':
            self.running = False
            self.status_var.set(f"Invalid configuration! No solution found.")
            messagebox.showerror("Result", f"Invalid configuration! No solution found.")
            self._update_controls(is_running=False)
            
        elif result == 'done':
            self.running = False

            self._update_controls(is_running=False)
