
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    department TEXT NOT NULL,
    designation TEXT NOT NULL,
    joining_date TEXT NOT NULL,
    basic_salary REAL NOT NULL CHECK (basic_salary >= 0),
    employment_status TEXT NOT NULL DEFAULT 'Active'
        CHECK (employment_status IN ('Active', 'Inactive')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    attendance_date TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN (
            'Present', 'Absent', 'Half Day',
            'Weekly Off', 'Holiday'
        )),
    remarks TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id),
    UNIQUE (employee_id, attendance_date)
);

CREATE TABLE IF NOT EXISTS leave_requests (
    leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    leave_type TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    days_requested REAL NOT NULL CHECK (days_requested > 0),
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'Pending'
        CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    reviewed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id),
    CHECK (end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS leave_balances (
    balance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    leave_type TEXT NOT NULL,
    leave_year INTEGER NOT NULL,
    entitled_days REAL NOT NULL DEFAULT 0
        CHECK (entitled_days >= 0),
    used_days REAL NOT NULL DEFAULT 0
        CHECK (used_days >= 0),
    FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id),
    UNIQUE (employee_id, leave_type, leave_year)
);

CREATE TABLE IF NOT EXISTS salary_components (
    component_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    component_name TEXT NOT NULL,
    component_type TEXT NOT NULL
        CHECK (component_type IN ('Allowance', 'Deduction')),
    amount REAL NOT NULL CHECK (amount >= 0),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),
    FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id),
    CHECK (
        effective_to IS NULL OR effective_to >= effective_from
    )
);

CREATE TABLE IF NOT EXISTS payroll (
    payroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    pay_month TEXT NOT NULL,
    working_days INTEGER NOT NULL CHECK (working_days >= 0),
    payable_days REAL NOT NULL CHECK (payable_days >= 0),
    gross_salary REAL NOT NULL CHECK (gross_salary >= 0),
    total_deductions REAL NOT NULL CHECK (total_deductions >= 0),
    net_salary REAL NOT NULL CHECK (net_salary >= 0),
    payment_status TEXT NOT NULL DEFAULT 'Draft'
        CHECK (payment_status IN ('Draft', 'Processed', 'Paid')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id)
        REFERENCES employees(employee_id),
    UNIQUE (employee_id, pay_month),
    CHECK (payable_days <= working_days),
    CHECK (net_salary = ROUND(gross_salary - total_deductions, 2))
);

CREATE TABLE IF NOT EXISTS payroll_details (
    detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    payroll_id INTEGER NOT NULL,
    component_name TEXT NOT NULL,
    component_type TEXT NOT NULL
        CHECK (component_type IN ('Earning', 'Deduction')),
    amount REAL NOT NULL CHECK (amount >= 0),
    FOREIGN KEY (payroll_id)
        REFERENCES payroll(payroll_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_attendance_employee_date
ON attendance(employee_id, attendance_date);

CREATE INDEX IF NOT EXISTS idx_leave_employee_dates
ON leave_requests(employee_id, start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_payroll_month
ON payroll(pay_month);
