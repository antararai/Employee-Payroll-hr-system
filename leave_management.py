
import sqlite3
import pandas as pd
import streamlit as st
from datetime import date
from database import get_connection


def get_active_employees():
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT employee_id, full_name
            FROM employees
            WHERE employment_status = 'Active'
            ORDER BY full_name
            """,
            conn
        )


def get_leave_requests():
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT
                l.leave_id AS 'Request ID',
                e.full_name AS 'Employee',
                l.leave_type AS 'Leave Type',
                l.start_date AS 'Start Date',
                l.end_date AS 'End Date',
                l.days_requested AS 'Days',
                l.reason AS 'Reason',
                l.status AS 'Status'
            FROM leave_requests l
            JOIN employees e
                ON l.employee_id = e.employee_id
            ORDER BY l.created_at DESC
            """,
            conn
        )


def render_leave_management():
    st.title("Leave Management")
    st.caption("Apply for leave, review requests, and manage approvals.")

    employees = get_active_employees()

    if employees.empty:
        st.warning("Please add an active employee in Employee Management first.")
        return

    tab1, tab2, tab3 = st.tabs([
        "Apply for Leave",
        "Leave Requests",
        "Approve / Reject"
    ])

    with tab1:
        st.subheader("New Leave Application")

        with st.form("leave_application_form"):
            employee_options = {
                f"{row['full_name']} (ID: {row['employee_id']})":
                int(row["employee_id"])
                for _, row in employees.iterrows()
            }

            selected_employee = st.selectbox(
                "Select Employee",
                list(employee_options.keys())
            )

            leave_type = st.selectbox(
                "Leave Type",
                ["Casual Leave", "Sick Leave", "Earned Leave", "Other"]
            )

            start_date = st.date_input(
                "Start Date",
                value=date.today()
            )

            end_date = st.date_input(
                "End Date",
                value=date.today()
            )

            reason = st.text_area("Reason for Leave")

            submitted = st.form_submit_button("Submit Application")

            if submitted:
                if end_date < start_date:
                    st.error("End date cannot be before the start date.")
                else:
                    days_requested = (end_date - start_date).days + 1

                    try:
                        with get_connection() as conn:
                            conn.execute(
                                """
                                INSERT INTO leave_requests (
                                    employee_id,
                                    leave_type,
                                    start_date,
                                    end_date,
                                    days_requested,
                                    reason
                                )
                                VALUES (?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    employee_options[selected_employee],
                                    leave_type,
                                    start_date.isoformat(),
                                    end_date.isoformat(),
                                    days_requested,
                                    reason.strip()
                                )
                            )

                        st.success("Leave application submitted successfully!")
                        st.rerun()

                    except sqlite3.Error as error:
                        st.error(f"Could not submit application: {error}")

    with tab2:
        st.subheader("All Leave Requests")

        requests = get_leave_requests()

        if requests.empty:
            st.info("No leave applications have been submitted yet.")
        else:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Pending", "Approved", "Rejected"]
            )

            if status_filter != "All":
                requests = requests[
                    requests["Status"] == status_filter
                ]

            st.dataframe(
                requests,
                use_container_width=True,
                hide_index=True
            )

            st.metric("Requests Shown", len(requests))

    with tab3:
        st.subheader("Review Leave Applications")

        with get_connection() as conn:
            pending = pd.read_sql_query(
                """
                SELECT
                    l.leave_id,
                    e.full_name,
                    l.leave_type,
                    l.start_date,
                    l.end_date,
                    l.days_requested,
                    l.reason
                FROM leave_requests l
                JOIN employees e
                    ON l.employee_id = e.employee_id
                WHERE l.status = 'Pending'
                ORDER BY l.created_at
                """,
                conn
            )

        if pending.empty:
            st.info("There are no pending leave requests.")
        else:
            for _, request in pending.iterrows():
                with st.container(border=True):
                    st.write(
                        f"**{request['full_name']}** — "
                        f"{request['leave_type']}"
                    )

                    st.write(
                        f"**Dates:** {request['start_date']} to "
                        f"{request['end_date']}"
                    )

                    st.write(f"**Days:** {request['days_requested']}")
                    st.write(f"**Reason:** {request['reason'] or 'Not provided'}")

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(
                            "Approve",
                            key=f"approve_{request['leave_id']}"
                        ):
                            with get_connection() as conn:
                                conn.execute(
                                    """
                                    UPDATE leave_requests
                                    SET status = 'Approved',
                                        reviewed_at = CURRENT_TIMESTAMP
                                    WHERE leave_id = ?
                                      AND status = 'Pending'
                                    """,
                                    (int(request["leave_id"]),)
                                )

                            st.success("Leave approved!")
                            st.rerun()

                    with col2:
                        if st.button(
                            "Reject",
                            key=f"reject_{request['leave_id']}"
                        ):
                            with get_connection() as conn:
                                conn.execute(
                                    """
                                    UPDATE leave_requests
                                    SET status = 'Rejected',
                                        reviewed_at = CURRENT_TIMESTAMP
                                    WHERE leave_id = ?
                                      AND status = 'Pending'
                                    """,
                                    (int(request["leave_id"]),)
                                )

                            st.warning("Leave rejected.")
                            st.rerun()
