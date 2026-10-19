
import streamlit as st
import pandas as pd
from datetime import date
from html import escape

from database import init_db, get_connection
from employee_management import render_employee_management
from attendance_management import render_attendance_management
from leave_management import render_leave_management
from payroll_management import render_payroll_management
from payslips import render_payslips


st.set_page_config(
    page_title="PeopleDesk | HR Management",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()


# -------------------- CUSTOM STYLING --------------------

st.markdown("""
<style>
    .stApp {
        background-color: #F5F7FB;
    }

    [data-testid="stSidebar"] {
        background-color: #17233F;
    }

    [data-testid="stSidebar"] * {
        color: #F3F6FC;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        background-color: transparent;
        border-radius: 8px;
        padding: 7px 9px;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    .hero {
        background: linear-gradient(115deg, #243B67, #5268A9);
        color: white;
        padding: 28px 30px;
        border-radius: 18px;
        margin-bottom: 24px;
    }

    .hero h1 {
        color: white;
        font-size: 30px;
        margin: 0 0 8px 0;
    }

    .hero p {
        color: #E1E8FA;
        margin: 0;
        font-size: 15px;
    }

    .section-heading {
        color: #202D49;
        font-size: 21px;
        font-weight: 700;
        margin: 20px 0 14px 0;
    }

    .metric-card {
        background: white;
        border: 1px solid #E4E9F2;
        border-radius: 14px;
        padding: 19px 18px;
        min-height: 126px;
        box-shadow: 0 3px 12px rgba(30, 48, 80, 0.04);
    }

    .metric-label {
        color: #68758C;
        font-size: 13px;
        margin-bottom: 12px;
    }

    .metric-value {
        color: #202D49;
        font-size: 29px;
        font-weight: 750;
        line-height: 1.2;
    }

    .metric-note {
        color: #8B96A9;
        font-size: 12px;
        margin-top: 8px;
    }

    .panel {
        background: white;
        border: 1px solid #E4E9F2;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 3px 12px rgba(30, 48, 80, 0.04);
    }

    div[data-testid="stButton"] button {
        border-radius: 9px;
        min-height: 43px;
        font-weight: 600;
        border-color: #D9E1EF;
    }

    div[data-testid="stButton"] button:hover {
        border-color: #5268A9;
        color: #354D86;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #E4E9F2;
        border-radius: 10px;
        overflow: hidden;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)


# -------------------- DASHBOARD DATA --------------------

def get_dashboard_data():
    today = date.today()
    today_string = today.isoformat()
    current_month = today.strftime("%Y-%m")

    with get_connection() as conn:
        total_employees = conn.execute(
            "SELECT COUNT(*) FROM employees"
        ).fetchone()[0]

        active_employees = conn.execute(
            """
            SELECT COUNT(*) FROM employees
            WHERE employment_status = 'Active'
            """
        ).fetchone()[0]

        present_today = conn.execute(
            """
            SELECT COUNT(*) FROM attendance
            WHERE attendance_date = ?
              AND status IN ('Present', 'Half Day')
            """,
            (today_string,)
        ).fetchone()[0]

        pending_leaves = conn.execute(
            """
            SELECT COUNT(*) FROM leave_requests
            WHERE status = 'Pending'
            """
        ).fetchone()[0]

        payroll = conn.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(net_salary), 0)
            FROM payroll
            WHERE pay_month = ?
            """,
            (current_month,)
        ).fetchone()

        recent_employees = pd.read_sql_query(
            """
            SELECT
                employee_id AS 'ID',
                full_name AS 'Employee',
                department AS 'Department',
                designation AS 'Designation',
                employment_status AS 'Status'
            FROM employees
            ORDER BY employee_id DESC
            LIMIT 5
            """,
            conn
        )

        recent_payroll = pd.read_sql_query(
            """
            SELECT
                e.full_name AS 'Employee',
                p.pay_month AS 'Month',
                p.net_salary AS 'Net Salary (₹)',
                p.payment_status AS 'Payment Status'
            FROM payroll p
            JOIN employees e
                ON p.employee_id = e.employee_id
            ORDER BY p.pay_month DESC, p.payroll_id DESC
            LIMIT 5
            """,
            conn
        )

    return {
        "total": total_employees,
        "active": active_employees,
        "present": present_today,
        "pending": pending_leaves,
        "payroll_count": payroll[0],
        "payroll_total": payroll[1],
        "employees": recent_employees,
        "payroll_records": recent_payroll,
        "month": today.strftime("%B %Y"),
        "today": today.strftime("%d %B %Y")
    }


def metric_card(label, value, note, icon):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{icon} &nbsp; {escape(label)}</div>
            <div class="metric-value">{escape(str(value))}</div>
            <div class="metric-note">{escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# -------------------- DASHBOARD --------------------

def render_dashboard():
    data = get_dashboard_data()

    st.markdown(
        f"""
        <div class="hero">
            <h1>Good to see you 👋</h1>
            <p>
                Welcome to PeopleDesk — your employee, attendance,
                leave and payroll overview.
            </p>
            <p style="margin-top:14px;font-size:13px;">
                {escape(data["today"])} &nbsp; • &nbsp; HR Overview
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-heading">Workforce Overview</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        metric_card(
            "Total Employees", data["total"],
            "All employee records", "👥"
        )

    with c2:
        metric_card(
            "Active Employees", data["active"],
            "Currently active", "🟢"
        )

    with c3:
        metric_card(
            "Present Today", data["present"],
            "Present or half-day records", "📅"
        )

    with c4:
        metric_card(
            "Pending Leaves", data["pending"],
            "Awaiting review", "🕒"
        )

    st.markdown(
        '<div class="section-heading">Payroll Overview</div>',
        unsafe_allow_html=True
    )

    p1, p2, p3 = st.columns(3, gap="medium")

    with p1:
        metric_card(
            "Payroll Period", data["month"],
            "Current calendar month", "🗓️"
        )

    with p2:
        metric_card(
            "Payroll Records", data["payroll_count"],
            "Records generated this month", "📄"
        )

    with p3:
        metric_card(
            "Total Net Payroll",
            f"₹{data['payroll_total']:,.2f}",
            "All statuses for this month", "💰"
        )

    st.markdown(
        '<div class="section-heading">Recent Activity</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("#### 👥 Recent Employees")

        if data["employees"].empty:
            st.info("No employee records yet.")
        else:
            st.dataframe(
                data["employees"],
                use_container_width=True,
                hide_index=True
            )

    with right:
        st.markdown("#### 💳 Recent Payroll")

        if data["payroll_records"].empty:
            st.info("No payroll records yet.")
        else:
            st.dataframe(
                data["payroll_records"],
                use_container_width=True,
                hide_index=True
            )

    st.markdown(
        '<div class="section-heading">Quick Actions</div>',
        unsafe_allow_html=True
    )

    st.caption("Choose a task to jump directly to its module.")

    q1, q2, q3 = st.columns(3, gap="medium")

    with q1:
        st.button(
            "👥  Manage Employees",
            key="quick_employees",
            use_container_width=True,
            on_click=navigate_to,
            args=("Employee Management",)
        )

    with q2:
        st.button(
            "📅  Manage Attendance",
            key="quick_attendance",
            use_container_width=True,
            on_click=navigate_to,
            args=("Attendance Management",)
        )

    with q3:
        st.button(
            "💰  Manage Payroll",
            key="quick_payroll",
            use_container_width=True,
            on_click=navigate_to,
            args=("Payroll Management",)
        )


# -------------------- NAVIGATION --------------------

def navigate_to(destination):
    # Callback runs before Streamlit reruns the page.
    # A separate radio key prevents widget-state errors.
    st.session_state["navigation_radio"] = destination


st.sidebar.markdown("## 🏢 PeopleDesk")
st.sidebar.caption("EMPLOYEE & HR MANAGEMENT")
st.sidebar.divider()

pages = [
    "Dashboard",
    "Employee Management",
    "Attendance Management",
    "Leave Management",
    "Payroll Management",
    "Payslips"
]

if "navigation_radio" not in st.session_state:
    st.session_state["navigation_radio"] = "Dashboard"

page = st.sidebar.radio(
    "WORKSPACE",
    pages,
    key="navigation_radio"
)

if page == "Dashboard":
    render_dashboard()

elif page == "Employee Management":
    render_employee_management()

elif page == "Attendance Management":
    render_attendance_management()

elif page == "Leave Management":
    render_leave_management()

elif page == "Payroll Management":
    render_payroll_management()

elif page == "Payslips":
    render_payslips()

st.sidebar.divider()
st.sidebar.caption("PeopleDesk HRMS • Local application")
