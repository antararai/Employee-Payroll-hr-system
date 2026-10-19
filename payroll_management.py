
import sqlite3
import calendar
from datetime import date

import pandas as pd
import streamlit as st

from database import get_connection


def get_active_employees():
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT employee_id, full_name, basic_salary
            FROM employees
            WHERE employment_status = 'Active'
            ORDER BY full_name
            """,
            conn
        )


def get_payroll_records():
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT
                p.payroll_id AS 'Payroll ID',
                e.full_name AS 'Employee',
                p.pay_month AS 'Pay Month',
                p.working_days AS 'Working Days',
                p.payable_days AS 'Payable Days',
                p.gross_salary AS 'Gross Salary',
                p.total_deductions AS 'Deductions',
                p.net_salary AS 'Net Salary',
                p.payment_status AS 'Payment Status'
            FROM payroll p
            JOIN employees e
                ON p.employee_id = e.employee_id
            ORDER BY p.pay_month DESC, e.full_name
            """,
            conn
        )


def get_attendance_days(employee_id, month, year):
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    with get_connection() as conn:
        attendance = pd.read_sql_query(
            """
            SELECT attendance_date, status
            FROM attendance
            WHERE employee_id = ?
              AND attendance_date BETWEEN ? AND ?
            """,
            conn,
            params=(
                employee_id,
                start_date.isoformat(),
                end_date.isoformat()
            )
        )

    # Count weekdays, excluding Sundays and Saturdays.
    working_days = sum(
        1
        for day in range(1, last_day + 1)
        if date(year, month, day).weekday() < 5
    )

    # Pay Present days fully, Half Day at 50%, and weekly offs/holidays
    # at full pay when they fall on a scheduled working day.
    payable_days = 0.0

    for _, record in attendance.iterrows():
        status = record["status"]
        attendance_date = date.fromisoformat(record["attendance_date"])

        if attendance_date.weekday() >= 5:
            continue

        if status in ("Present", "Weekly Off", "Holiday"):
            payable_days += 1
        elif status == "Half Day":
            payable_days += 0.5

    # If no attendance was entered, assume the employee worked
    # all scheduled working days. This avoids generating zero salary
    # for months whose attendance has not been recorded.
    if attendance.empty:
        payable_days = float(working_days)

    return working_days, min(payable_days, working_days)


def generate_payroll(
    employee_id,
    basic_salary,
    pay_month,
    working_days,
    payable_days,
    allowances,
    deductions
):
    if working_days <= 0:
        raise ValueError("Working days must be greater than zero.")

    if payable_days < 0 or payable_days > working_days:
        raise ValueError("Payable days must be between 0 and working days.")

    if allowances < 0 or deductions < 0:
        raise ValueError("Allowances and deductions cannot be negative.")

    payable_basic = round(
        basic_salary * payable_days / working_days, 2
    )

    gross_salary = round(payable_basic + allowances, 2)
    total_deductions = round(deductions, 2)
    net_salary = round(gross_salary - total_deductions, 2)

    if net_salary < 0:
        raise ValueError("Deductions cannot exceed gross salary.")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO payroll (
                employee_id,
                pay_month,
                working_days,
                payable_days,
                gross_salary,
                total_deductions,
                net_salary,
                payment_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Draft')
            """,
            (
                employee_id,
                pay_month,
                working_days,
                payable_days,
                gross_salary,
                total_deductions,
                net_salary
            )
        )

    return payable_basic, gross_salary, net_salary


def render_payroll_management():
    st.title("Payroll Management")
    st.caption("Generate monthly salary records and manage payments.")

    employees = get_active_employees()

    tab1, tab2 = st.tabs(["Generate Payroll", "Payroll Records"])

    with tab1:
        st.subheader("Generate Monthly Payroll")

        if employees.empty:
            st.warning("Add an active employee first.")
        else:
            employee_options = {
                f"{row['full_name']} (ID: {row['employee_id']})":
                row
                for _, row in employees.iterrows()
            }

            with st.form("generate_payroll_form"):
                selected_employee = st.selectbox(
                    "Select Employee",
                    list(employee_options.keys())
                )

                today = date.today()

                col1, col2 = st.columns(2)

                with col1:
                    month = st.selectbox(
                        "Payroll Month",
                        list(range(1, 13)),
                        index=today.month - 1,
                        format_func=lambda m: calendar.month_name[m]
                    )

                with col2:
                    year = st.number_input(
                        "Payroll Year",
                        min_value=2020,
                        max_value=2100,
                        value=today.year,
                        step=1
                    )

                employee = employee_options[selected_employee]
                employee_id = int(employee["employee_id"])
                basic_salary = float(employee["basic_salary"])

                st.info(f"Monthly basic salary: ₹{basic_salary:,.2f}")

                working_days, suggested_payable_days = get_attendance_days(
                    employee_id, month, int(year)
                )

                st.write(f"Scheduled working days: **{working_days}**")

                payable_days = st.number_input(
                    "Payable Days",
                    min_value=0.0,
                    max_value=float(working_days),
                    value=float(suggested_payable_days),
                    step=0.5
                )

                allowances = st.number_input(
                    "Total Allowances (₹)",
                    min_value=0.0,
                    value=0.0,
                    step=500.0
                )

                deductions = st.number_input(
                    "Total Deductions (₹)",
                    min_value=0.0,
                    value=0.0,
                    step=100.0
                )

                submitted = st.form_submit_button("Generate Payroll")

                if submitted:
                    pay_month = f"{int(year):04d}-{int(month):02d}"

                    try:
                        payable_basic = round(
                            basic_salary * payable_days / working_days, 2
                        )
                        gross = round(payable_basic + allowances, 2)
                        net = round(gross - deductions, 2)

                        if net < 0:
                            st.error(
                                "Deductions cannot exceed gross salary."
                            )
                        else:
                            with get_connection() as conn:
                                existing = conn.execute(
                                    """
                                    SELECT payroll_id
                                    FROM payroll
                                    WHERE employee_id = ? AND pay_month = ?
                                    """,
                                    (employee_id, pay_month)
                                ).fetchone()

                            if existing:
                                st.error(
                                    "Payroll already exists for this employee "
                                    "and month. Check Payroll Records."
                                )
                            else:
                                generate_payroll(
                                    employee_id,
                                    basic_salary,
                                    pay_month,
                                    working_days,
                                    payable_days,
                                    allowances,
                                    deductions
                                )

                                st.success(
                                    f"Payroll generated! Net salary: ₹{net:,.2f}"
                                )
                                st.rerun()

                    except (sqlite3.Error, ValueError) as error:
                        st.error(f"Could not generate payroll: {error}")

    with tab2:
        st.subheader("Monthly Payroll Records")

        records = get_payroll_records()

        if records.empty:
            st.info("No payroll records yet. Generate payroll first.")
        else:
            st.dataframe(
                records,
                use_container_width=True,
                hide_index=True
            )

            st.divider()
            st.subheader("Update Payment Status")

            payroll_options = {
                f"{row['Employee']} — {row['Pay Month']} "
                f"(₹{row['Net Salary']:,.2f}, {row['Payment Status']})":
                int(row["Payroll ID"])
                for _, row in records.iterrows()
            }

            selected_payroll = st.selectbox(
                "Select Payroll Record",
                list(payroll_options.keys())
            )

            new_status = st.selectbox(
                "New Payment Status",
                ["Draft", "Processed", "Paid"]
            )

            if st.button("Update Status"):
                try:
                    with get_connection() as conn:
                        conn.execute(
                            """
                            UPDATE payroll
                            SET payment_status = ?
                            WHERE payroll_id = ?
                            """,
                            (
                                new_status,
                                payroll_options[selected_payroll]
                            )
                        )

                    st.success("Payment status updated!")
                    st.rerun()

                except sqlite3.Error as error:
                    st.error(f"Could not update status: {error}")
