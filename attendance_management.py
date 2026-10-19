
import sqlite3
import pandas as pd
import streamlit as st

from database import get_connection


ATTENDANCE_STATUSES = [
    "Present",
    "Absent",
    "Half Day",
    "Weekly Off",
    "Holiday",
]


def get_active_employees():
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT employee_id, full_name, department
            FROM employees
            WHERE employment_status = 'Active'
            ORDER BY full_name
            """,
            conn,
        )


def save_attendance(employee_id, attendance_date, status, remarks):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO attendance
                (employee_id, attendance_date, status, remarks)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(employee_id, attendance_date)
            DO UPDATE SET
                status = excluded.status,
                remarks = excluded.remarks
            """,
            (
                employee_id,
                attendance_date.isoformat(),
                status,
                remarks.strip(),
            ),
        )


def get_attendance(start_date, end_date, employee_id=None):
    query = """
        SELECT
            a.attendance_id,
            a.employee_id,
            e.full_name,
            e.department,
            a.attendance_date,
            a.status,
            a.remarks
        FROM attendance a
        JOIN employees e
            ON a.employee_id = e.employee_id
        WHERE a.attendance_date BETWEEN ? AND ?
    """
    params = [start_date.isoformat(), end_date.isoformat()]

    if employee_id is not None:
        query += " AND a.employee_id = ?"
        params.append(employee_id)

    query += " ORDER BY a.attendance_date DESC, e.full_name"

    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


def render_attendance_management():
    st.header("Attendance Management")
    st.caption("Record and review employee attendance.")

    employees = get_active_employees()

    if employees.empty:
        st.warning(
            "No active employees found. Add an employee first "
            "using Employee Management."
        )
        return

    mark_tab, records_tab, summary_tab = st.tabs(
        ["📝 Mark Attendance", "📋 Attendance Records", "📊 Summary"]
    )

    employee_ids = employees["employee_id"].tolist()

    def employee_label(eid):
        row = employees[employees["employee_id"] == eid].iloc[0]
        return f"EMP-{eid:04d} — {row['full_name']}"

    with mark_tab:
        st.subheader("Mark or Update Attendance")

        with st.form("attendance_form"):
            employee_id = st.selectbox(
                "Employee",
                employee_ids,
                format_func=employee_label,
            )
            attendance_date = st.date_input(
                "Attendance Date",
                value=pd.Timestamp.today().date(),
            )
            status = st.selectbox(
                "Attendance Status",
                ATTENDANCE_STATUSES,
            )
            remarks = st.text_input("Remarks (optional)")

            submitted = st.form_submit_button(
                "Save Attendance",
                type="primary",
            )

        if submitted:
            try:
                save_attendance(
                    employee_id,
                    attendance_date,
                    status,
                    remarks,
                )
                st.success(
                    "Attendance saved. If a record already existed "
                    "for that employee and date, it was updated."
                )
                st.rerun()
            except sqlite3.Error as exc:
                st.error(f"Could not save attendance: {exc}")

    with records_tab:
        st.subheader("Attendance Records")

        col1, col2 = st.columns(2)
        today = pd.Timestamp.today().date()

        with col1:
            start_date = st.date_input(
                "From Date",
                value=today.replace(day=1),
                key="attendance_start",
            )

        with col2:
            end_date = st.date_input(
                "To Date",
                value=today,
                key="attendance_end",
            )

        selected_employee = st.selectbox(
            "Filter by Employee",
            ["All Employees"] + employee_ids,
            format_func=lambda eid: (
                eid if eid == "All Employees" else employee_label(eid)
            ),
            key="attendance_employee_filter",
        )

        if start_date > end_date:
            st.error("The start date must be on or before the end date.")
        else:
            employee_filter = (
                None
                if selected_employee == "All Employees"
                else selected_employee
            )

            records = get_attendance(
                start_date,
                end_date,
                employee_filter,
            )

            if records.empty:
                st.info("No attendance records found for these filters.")
            else:
                st.dataframe(
                    records,
                    use_container_width=True,
                    hide_index=True,
                )

    with summary_tab:
        st.subheader("Attendance Summary")

        summary_start = st.date_input(
            "Summary From",
            value=today.replace(day=1),
            key="summary_start",
        )
        summary_end = st.date_input(
            "Summary To",
            value=today,
            key="summary_end",
        )

        if summary_start > summary_end:
            st.error("The start date must be on or before the end date.")
        else:
            records = get_attendance(summary_start, summary_end)

            if records.empty:
                st.info("No attendance records found for this period.")
            else:
                counts = records["status"].value_counts()

                cols = st.columns(4)
                for col, label in zip(
                    cols,
                    ["Present", "Absent", "Half Day", "Other"],
                ):
                    if label == "Other":
                        value = int(
                            counts.get("Weekly Off", 0)
                            + counts.get("Holiday", 0)
                        )
                    else:
                        value = int(counts.get(label, 0))

                    col.metric(label, value)

                st.bar_chart(counts)
