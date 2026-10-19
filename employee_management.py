
import sqlite3
import pandas as pd
import streamlit as st

from database import get_connection


def get_employees(active_only=False):
    """Fetch employee records from SQLite."""
    with get_connection() as conn:
        query = "SELECT * FROM employees"

        if active_only:
            query += " WHERE employment_status = 'Active'"

        query += " ORDER BY employee_id DESC"
        return pd.read_sql_query(query, conn)


def add_employee(name, email, phone, department,
                 designation, joining_date, basic_salary):
    """Insert a new employee record."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO employees
            (full_name, email, phone, department, designation,
             joining_date, basic_salary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name.strip(),
                email.strip() or None,
                phone.strip(),
                department,
                designation.strip(),
                joining_date.isoformat(),
                basic_salary,
            ),
        )


def update_employee(employee_id, name, email, phone,
                    department, designation,
                    joining_date, basic_salary):
    """Update an existing employee."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE employees
            SET full_name = ?, email = ?, phone = ?,
                department = ?, designation = ?,
                joining_date = ?, basic_salary = ?
            WHERE employee_id = ?
            """,
            (
                name.strip(),
                email.strip() or None,
                phone.strip(),
                department,
                designation.strip(),
                joining_date.isoformat(),
                basic_salary,
                employee_id,
            ),
        )


def deactivate_employee(employee_id):
    """Deactivate an employee without deleting their history."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE employees
            SET employment_status = 'Inactive'
            WHERE employee_id = ?
            """,
            (employee_id,),
        )


def render_employee_management():
    st.header("Employee Management")
    st.caption("Add, view, search, edit and deactivate employee records.")

    tab_add, tab_view, tab_edit, tab_deactivate = st.tabs(
        [
            "➕ Add Employee",
            "👥 View Employees",
            "✏️ Edit Employee",
            "🔒 Deactivate Employee",
        ]
    )

    # ADD EMPLOYEE
    with tab_add:
        st.subheader("Register a New Employee")

        with st.form("add_employee_form"):
            name = st.text_input("Full Name *")
            email = st.text_input("Email Address")
            phone = st.text_input("Phone Number")

            department = st.selectbox(
                "Department *",
                [
                    "Human Resources",
                    "Finance",
                    "IT",
                    "Sales",
                    "Marketing",
                    "Operations",
                    "Other",
                ],
            )

            designation = st.text_input("Designation *")
            joining_date = st.date_input("Joining Date")
            basic_salary = st.number_input(
                "Monthly Basic Salary (₹)",
                min_value=0.0,
                value=15000.0,
                step=1000.0,
            )

            submitted = st.form_submit_button(
                "Save Employee",
                type="primary",
            )

        if submitted:
            if not name.strip() or not designation.strip():
                st.error("Please enter the employee name and designation.")
            elif email.strip() and (
                "@" not in email or "." not in email.split("@")[-1]
            ):
                st.error("Please enter a valid email address.")
            elif phone.strip() and not phone.strip().replace("+", "").replace("-", "").replace(" ", "").isdigit():
                st.error("Please enter a valid phone number.")
            else:
                try:
                    add_employee(
                        name,
                        email,
                        phone,
                        department,
                        designation,
                        joining_date,
                        basic_salary,
                    )
                    st.success(f"Employee '{name.strip()}' added successfully!")
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.error(
                        "This email address is already registered. "
                        "Please use a different email."
                    )

    # VIEW AND SEARCH EMPLOYEES
    with tab_view:
        st.subheader("Employee Directory")

        employees = get_employees()

        if employees.empty:
            st.info("No employees found. Add your first employee above.")
        else:
            search = st.text_input(
                "Search by name, ID, department or designation",
                key="employee_search",
            )

            if search.strip():
                term = search.strip()
                mask = (
                    employees["full_name"].str.contains(
                        term, case=False, na=False
                    )
                    | employees["department"].str.contains(
                        term, case=False, na=False
                    )
                    | employees["designation"].str.contains(
                        term, case=False, na=False
                    )
                    | employees["employee_id"].astype(str).str.contains(
                        term, case=False, na=False
                    )
                )
                employees = employees[mask]

            st.metric("Matching Employees", len(employees))

            display_columns = [
                "employee_id",
                "full_name",
                "email",
                "department",
                "designation",
                "joining_date",
                "basic_salary",
                "employment_status",
            ]

            st.dataframe(
                employees[display_columns],
                use_container_width=True,
                hide_index=True,
            )

    # EDIT EMPLOYEE
    with tab_edit:
        st.subheader("Update Employee Details")

        employees = get_employees(active_only=True)

        if employees.empty:
            st.info("There are no active employees to edit.")
        else:
            employee_ids = employees["employee_id"].tolist()
            employee_id = st.selectbox(
                "Select Employee",
                employee_ids,
                format_func=lambda eid: (
                    f"EMP-{eid:04d} — "
                    f"{employees.loc[employees['employee_id'] == eid, 'full_name'].iloc[0]}"
                ),
                key="edit_employee_id",
            )

            employee = employees[
                employees["employee_id"] == employee_id
            ].iloc[0]

            with st.form("edit_employee_form"):
                name = st.text_input(
                    "Full Name *", value=employee["full_name"]
                )
                email = st.text_input(
                    "Email Address",
                    value=employee["email"] or "",
                )
                phone = st.text_input(
                    "Phone Number",
                    value=employee["phone"] or "",
                )

                departments = [
                    "Human Resources", "Finance", "IT", "Sales",
                    "Marketing", "Operations", "Other",
                ]
                current_department = employee["department"]
                if current_department not in departments:
                    departments.append(current_department)

                department = st.selectbox(
                    "Department",
                    departments,
                    index=departments.index(current_department),
                )

                designation = st.text_input(
                    "Designation *", value=employee["designation"]
                )
                joining_date = st.date_input(
                    "Joining Date",
                    value=pd.to_datetime(
                        employee["joining_date"]
                    ).date(),
                )
                basic_salary = st.number_input(
                    "Monthly Basic Salary (₹)",
                    min_value=0.0,
                    value=float(employee["basic_salary"]),
                    step=1000.0,
                )

                save_changes = st.form_submit_button(
                    "Update Employee",
                    type="primary",
                )

            if save_changes:
                if not name.strip() or not designation.strip():
                    st.error("Name and designation are required.")
                elif email.strip() and (
                    "@" not in email
                    or "." not in email.split("@")[-1]
                ):
                    st.error("Please enter a valid email address.")
                else:
                    try:
                        update_employee(
                            employee_id,
                            name,
                            email,
                            phone,
                            department,
                            designation,
                            joining_date,
                            basic_salary,
                        )
                        st.success("Employee updated successfully!")
                        st.rerun()

                    except sqlite3.IntegrityError:
                        st.error(
                            "This email is already used by another employee."
                        )

    # DEACTIVATE EMPLOYEE
    with tab_deactivate:
        st.subheader("Deactivate an Employee")
        st.caption(
            "Deactivation preserves the employee record and its history."
        )

        employees = get_employees(active_only=True)

        if employees.empty:
            st.info("There are no active employees to deactivate.")
        else:
            employee_ids = employees["employee_id"].tolist()

            selected_id = st.selectbox(
                "Select Employee to Deactivate",
                employee_ids,
                format_func=lambda eid: (
                    f"EMP-{eid:04d} — "
                    f"{employees.loc[employees['employee_id'] == eid, 'full_name'].iloc[0]}"
                ),
                key="deactivate_employee_id",
            )

            confirm = st.checkbox(
                "I confirm that I want to deactivate this employee."
            )

            if st.button(
                "Deactivate Employee",
                type="primary",
                disabled=not confirm,
            ):
                deactivate_employee(selected_id)
                st.success("Employee deactivated successfully.")
                st.rerun()
