import time

# ==========================================
# 1. BFS SOLVER
# ==========================================
class BFSSolver:
    def __init__(self, n=8):
        self.n = n
        self.reset()

    def reset(self):
        self.start_time = None
        self.nodes = 0  # No nodes expanded at start
        self.initial = [0] * self.n  # Default to 0s
        self.fixed = []  # No fixed queens at start   
        self.col = 0
        self.valid = True
        self.finished = False
        self.trial_step = 0 

    def set_initial(self, rows):
        # 1. Reset first to clear old state
        self.reset()
        
        # 2. Apply User Input (User input is 1-based i.e. 1-8, convert to 0-based i.e. 0-7)
        self.initial = [r - 1 for r in rows[:]] 
        
        # (Note: BFS doesn't pre-calculate domains, it just uses self.initial dynamically in get_current_trial_row)

    def conflict_with_fixed(self, col, row):
        ''' Get column and row for fixed queens 
            and determines conflict with fixed queens. '''
        for c, r in enumerate(self.fixed):
            # Row constraint
            if r == row: 
                return True
            # Diagonal constraint
            if abs(c - col) == abs(r - row): 
                return True
        return False

    def get_current_trial_row(self):
        ''' Gets the row to try in this column.
            Start from user\’s preferred row, then cycle downward. '''
        start_row = self.initial[self.col]  # User initial row configuration
        return (start_row + self.trial_step) % self.n   # Wraps around the board

    def step(self):
        if self.start_time is None: self.start_time = time.time()   # start timer
        self.nodes += 1

        # check for invalid configuration or finished message
        if not self.valid or self.finished:
            return 'done', {'state': self.fixed[:]}

        # when board is finished and solution is found
        if self.col >= self.n:
            self.finished = True
            return 'solution', {'state': self.fixed[:]}

        # when board is not completed and searching for positions
        if self.trial_step < self.n:
            r = self.get_current_trial_row()
            # if no conflict with previously placed queens (add to fixed)
            if not self.conflict_with_fixed(self.col, r):
                self.fixed.append(r)
                self.trial_step = 0
                self.col += 1
                return 'fixed', {'col': self.col - 1, 'state': self.fixed[:], 'row': r}
            # if conflict is found, change row
            else:
                current_r = r
                self.trial_step += 1
                return 'searching', {'col': self.col, 'row': current_r}
        
        # when board is completed and invalid configuration (generate invalid message)
        else: 
            self.valid = False
            return 'invalid', {'col': self.col}



# ==========================================
# 2. CSP SOLVER
# ==========================================
class CSPSolver:
    ''' Constraint propagation and backtracking algorithm '''
    def __init__(self, n=8):
        self.n = n
        self.reset()    # reset board

    def reset(self):
        self.start_time = None
        self.nodes = 0
        self.initial = [0] * self.n  # Default (initial)
        self.fixed = []
        self.col = 0
        self.valid = True
        self.finished = False
        self.stack = []  # to hold past states for backtracking
        self.domains = []   # to hold possible values for each queen

    def set_initial(self, rows):
        # 1. Reset first to clear state (stack, fixed, etc.)
        self.reset()
        
        # 2. Apply User Input AFTER reset, so it doesn't get overwritten
        self.initial = [r - 1 for r in rows[:]]
        
        # 3. Build Domains based on this User Input
        self.domains = []
        # loop for all columns (0-7)
        for c in range(self.n):
            preferred = self.initial[c]    # get user given rows for the column c
            domain = list(range(self.n))    # create a list from 0-7
            # Priority Heuristic: Move the user's preferred row to the front of the list
            if preferred in domain:
                domain.remove(preferred)    # first remove the user given row from domain
                domain.insert(0, preferred)     # then insert back at first position i.e. 0 index
            self.domains.append(domain)   # append domain of that column to self.domains

    def forward_check(self, assigned_col, assigned_row, current_domains):
        ''' Checks if assigning a row allows future placements or not '''
        new_domains = [d[:] for d in current_domains]   # copy of domains
        # loop from assigned column to last
        for c in range(assigned_col + 1, self.n):
            # add values in new_domains of column 'c' if it does not violate row and diagonal constraints
            new_domains[c] = [
                r for r in new_domains[c] 
                if r != assigned_row and abs(c - assigned_col) != abs(r - assigned_row)
            ]
            # if no value available in the domain, return None (means backtracking required)
            if not new_domains[c]:
                return None
        # return domains
        return new_domains

    def step(self):
        ''' Step one time in solution '''
        if self.start_time is None: self.start_time = time.time()   # start timer
        self.nodes += 1

        # return solution
        if self.finished:
            return 'solution', {'state': self.fixed[:]}

        # all columns completed
        if self.col >= self.n:
            self.finished = True
            return 'solution', {'state': self.fixed[:]}

        # Check if we are stuck (domain empty) -> Backtrack
        if not self.domains[self.col]:
            # if no previous state available, return invalid
            if not self.stack:
                self.valid = False
                return 'invalid', {'col': self.col}
            
            # backtracking now
            prev_col, prev_domains, prev_row = self.stack.pop()
            self.col = prev_col   # last column restore
            self.fixed.pop()    # remove last incorrectly placed queen
            self.domains = prev_domains   # restore domain
            return 'backtracking', {'col': self.col, 'row': prev_row}

        # Try next available row in domain (first tried user's row)
        r = self.domains[self.col].pop(0)
        
        # Check forward consistency
        new_domains = self.forward_check(self.col, r, self.domains)

        if new_domains is not None:
            # Valid move
            self.stack.append((self.col, [d[:] for d in self.domains], r))  # add state to stack
            self.fixed.append(r)    # add to fixed queens
            self.domains = new_domains
            self.col += 1
            return 'fixed', {'col': self.col - 1, 'state': self.fixed[:], 'row': r}
        else:
            # Invalid move (causes future conflict)
            return 'searching', {'col': self.col, 'row': r}