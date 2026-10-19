import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from html import escape

from database import init_db, get_connection
from employee_management import render_employee_management
from attendance_management import render_attendance_management
from leave_management import render_leave_management
from payroll_management import render_payroll_management
from payslips import render_payslips


# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="PeopleDesk | HR Management",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()


# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #F6F7FB;
        color: #252946;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #171B3A 0%, #292D5B 100%);
        border-right: 1px solid #343960;
    }

    [data-testid="stSidebar"] * {
        color: #F5F6FF;
    }

    .brand-title {
        font-size: 27px;
        font-weight: 800;
        color: white;
        letter-spacing: -0.7px;
    }

    .brand-subtitle {
        font-size: 10px;
        color: #C0C5EA;
        letter-spacing: 1.2px;
        margin-bottom: 25px;
    }

    .hero {
        background: linear-gradient(120deg, #E9E8FF, #F0F2FF, #E4F6F5);
        border: 1px solid #E4E6F7;
        border-radius: 22px;
        padding: 28px 30px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(48, 55, 105, 0.05);
    }

    .hero-kicker {
        color: #6C63FF;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    .hero h1 {
        color: #202442;
        font-size: 31px;
        font-weight: 800;
        margin: 9px 0;
    }

    .hero p {
        color: #626987;
        font-size: 14px;
        margin: 0;
    }

    .section-heading {
        color: #252946;
        font-size: 21px;
        font-weight: 800;
        margin: 22px 0 14px 0;
    }

    .section-caption {
        color: #7A809B;
        font-size: 12px;
        margin-top: -8px;
        margin-bottom: 15px;
    }

    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E9EBF5;
        border-radius: 17px;
        padding: 17px 18px;
        min-height: 125px;
        box-shadow: 0 5px 18px rgba(38, 44, 85, 0.04);
    }

    .metric-label {
        color: #7B819C;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 9px;
    }

    .metric-value {
        color: #252946;
        font-size: 28px;
        font-weight: 800;
        overflow-wrap: anywhere;
    }

    .metric-note {
        color: #8B90A7;
        font-size: 11px;
        margin-top: 8px;
    }

    .content-card {
        background: #FFFFFF;
        border: 1px solid #E9EBF5;
        border-radius: 17px;
        padding: 17px 19px;
        margin-bottom: 12px;
        box-shadow: 0 5px 18px rgba(38, 44, 85, 0.035);
    }

    .content-card h3 {
        color: #252946;
        font-size: 16px;
        font-weight: 750;
        margin: 0 0 4px 0;
    }

    .content-card p {
        color: #858AA3;
        font-size: 12px;
        margin: 0;
    }

    div.stButton > button {
        border-radius: 10px;
        border: 1px solid #E1E4F1;
        font-weight: 600;
        min-height: 40px;
    }

    div.stButton > button[kind="primary"] {
        background: #6C63FF;
        border-color: #6C63FF;
        color: white;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #E9EBF5;
        border-radius: 12px;
        overflow: hidden;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# DASHBOARD DATA
# =========================================================
def get_dashboard_data():
    today = date.today()
    month_key = today.strftime("%Y-%m")

    with get_connection() as conn:

        employee_counts = pd.read_sql_query(
            """
            SELECT
                COUNT(*) AS total_employees,
                COALESCE(
                    SUM(
                        CASE
                            WHEN employment_status = 'Active' THEN 1
                            ELSE 0
                        END
                    ), 0
                ) AS active_employees
            FROM employees
            """,
            conn,
        )

        attendance = pd.read_sql_query(
            """
            SELECT COUNT(DISTINCT employee_id) AS present_today
            FROM attendance
            WHERE attendance_date = ?
              AND status IN ('Present', 'Half Day')
            """,
            conn,
            params=(today.isoformat(),),
        )

        leaves = pd.read_sql_query(
            """
            SELECT COUNT(*) AS pending_leaves
            FROM leave_requests
            WHERE status = 'Pending'
            """,
            conn,
        )

        payroll_summary = pd.read_sql_query(
            """
            SELECT
                COUNT(*) AS payroll_records,
                COALESCE(SUM(net_salary), 0) AS total_net_salary,
                COALESCE(SUM(gross_salary), 0) AS total_gross_salary,
                COALESCE(SUM(total_deductions), 0) AS total_deductions
            FROM payroll
            WHERE pay_month = ?
            """,
            conn,
            params=(month_key,),
        )

        recent_employees = pd.read_sql_query(
            """
            SELECT
                employee_id AS 'Employee ID',
                full_name AS 'Name',
                department AS 'Department',
                designation AS 'Designation',
                employment_status AS 'Status',
                joining_date AS 'Joining Date'
            FROM employees
            ORDER BY employee_id DESC
            LIMIT 5
            """,
            conn,
        )

        recent_payroll = pd.read_sql_query(
            """
            SELECT
                e.full_name AS 'Employee',
                p.pay_month AS 'Month',
                p.net_salary AS 'Net Salary (₹)',
                p.payment_status AS 'Status'
            FROM payroll p
            JOIN employees e
                ON e.employee_id = p.employee_id
            ORDER BY p.pay_month DESC, p.payroll_id DESC
            LIMIT 5
            """,
            conn,
        )

        departments = pd.read_sql_query(
            """
            SELECT
                department AS Department,
                COUNT(*) AS Employees
            FROM employees
            WHERE employment_status = 'Active'
            GROUP BY department
            ORDER BY Employees DESC
            """,
            conn,
        )

        payroll_trend = pd.read_sql_query(
            """
            SELECT
                pay_month AS Month,
                ROUND(SUM(net_salary), 2) AS NetSalary
            FROM payroll
            GROUP BY pay_month
            ORDER BY pay_month
            """,
            conn,
        )

    return {
        "today": today.strftime("%A, %d %B %Y"),
        "month_key": month_key,
        "total_employees": int(
            employee_counts.iloc[0]["total_employees"] or 0
        ),
        "active_employees": int(
            employee_counts.iloc[0]["active_employees"] or 0
        ),
        "present_today": int(
            attendance.iloc[0]["present_today"] or 0
        ),
        "pending_leaves": int(
            leaves.iloc[0]["pending_leaves"] or 0
        ),
        "payroll_records": int(
            payroll_summary.iloc[0]["payroll_records"] or 0
        ),
        "total_net_salary": float(
            payroll_summary.iloc[0]["total_net_salary"] or 0
        ),
        "total_gross_salary": float(
            payroll_summary.iloc[0]["total_gross_salary"] or 0
        ),
        "total_deductions": float(
            payroll_summary.iloc[0]["total_deductions"] or 0
        ),
        "recent_employees": recent_employees,
        "recent_payroll": recent_payroll,
        "departments": departments,
        "payroll_trend": payroll_trend,
    }


# =========================================================
# REUSABLE KPI CARD
# =========================================================
def metric_card(label, value, note, icon):
    st.markdown(
        f"""
        <div class="metric-card">
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
            ">
                <div class="metric-label">{escape(str(label))}</div>
                <div style="font-size:21px;">{icon}</div>
            </div>
            <div class="metric-value">{escape(str(value))}</div>
            <div class="metric-note">{escape(str(note))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# DASHBOARD NAVIGATION HELPER
# =========================================================
def navigate_to(destination):
    st.session_state["navigation_radio"] = destination


# =========================================================
# DASHBOARD PAGE
# =========================================================
def render_dashboard():
    data = get_dashboard_data()

    # Welcome banner
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-kicker">People Operations</div>
            <h1>Welcome back, Antara 👋</h1>
            <p>Your workforce overview, all in one place.</p>
            <p style="margin-top:12px;font-size:12px;">
                {escape(data["today"])} &nbsp; • &nbsp; HR Admin Dashboard
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Organization KPIs
    st.markdown(
        '<div class="section-heading">Organization Overview</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        metric_card(
            "Total Employees",
            data["total_employees"],
            "All employee records",
            "👥",
        )

    with c2:
        metric_card(
            "Active Employees",
            data["active_employees"],
            "Currently active",
            "🟢",
        )

    with c3:
        metric_card(
            "Present Today",
            data["present_today"],
            "Present or half-day marked",
            "📅",
        )

    with c4:
        metric_card(
            "Pending Leaves",
            data["pending_leaves"],
            "Requests awaiting review",
            "🕒",
        )

    # Analytics
    st.markdown(
        '<div class="section-heading">Workforce Analytics</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-caption">'
        'A quick look at your workforce and recorded payroll.'
        '</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns(2, gap="large")

    # Department pie chart
    with left:
        st.markdown(
            """
            <div class="content-card">
                <h3>👥 Department Distribution</h3>
                <p>Active employees across departments</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        departments = data["departments"]

        if departments.empty:
            st.info("Add active employees to view department analytics.")
        else:
            fig = px.pie(
                departments,
                names="Department",
                values="Employees",
                hole=0.62,
                color_discrete_sequence=[
                    "#6C63FF",
                    "#22B8A5",
                    "#FF719A",
                    "#F5B544",
                    "#4B8BFF",
                    "#9B72CF",
                ],
            )

            fig.update_traces(
                textposition="inside",
                textinfo="percent",
                hovertemplate=(
                    "%{label}<br>"
                    "Employees: %{value}"
                    "<extra></extra>"
                ),
            )

            fig.update_layout(
                height=330,
                margin=dict(t=10, b=20, l=10, r=10),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.12,
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#626987"),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                key="department_distribution_chart",
            )

    # Payroll trend chart
    with right:
        st.markdown(
            """
            <div class="content-card">
                <h3>💰 Monthly Payroll Trend</h3>
                <p>Net salary across generated payroll records</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        payroll_trend = data["payroll_trend"]

        if payroll_trend.empty:
            st.info("Generate payroll records to view the monthly trend.")
        else:
            fig = px.bar(
                payroll_trend,
                x="Month",
                y="NetSalary",
                text="NetSalary",
                labels={
                    "Month": "Payroll Month",
                    "NetSalary": "Net Salary (₹)",
                },
                color_discrete_sequence=["#7567F8"],
            )

            fig.update_traces(
                texttemplate="₹%{text:,.0f}",
                textposition="outside",
                cliponaxis=False,
                hovertemplate=(
                    "Month: %{x}<br>"
                    "Net Salary: ₹%{y:,.2f}"
                    "<extra></extra>"
                ),
            )

            fig.update_layout(
                height=330,
                margin=dict(t=35, b=45, l=15, r=15),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    type="category",
                    title="Payroll Month",
                    showgrid=False,
                    tickangle=0,
                ),
                yaxis=dict(
                    title="Net Salary (₹)",
                    gridcolor="#E8ECF4",
                    zeroline=False,
                    rangemode="tozero",
                ),
                showlegend=False,
                font=dict(color="#626987"),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                key="monthly_payroll_chart",
            )

    # Payroll summary
    st.markdown(
        '<div class="section-heading">Payroll Summary</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="section-caption">'
        f'Summary for {escape(data["month_key"])}.'
        f'</div>',
        unsafe_allow_html=True,
    )

    p1, p2, p3, p4 = st.columns(4, gap="medium")

    with p1:
        metric_card(
            "Payroll Records",
            data["payroll_records"],
            "Records for this month",
            "🧾",
        )

    with p2:
        metric_card(
            "Net Payroll",
            f'₹{data["total_net_salary"]:,.2f}',
            "Take-home payroll total",
            "💸",
        )

    with p3:
        metric_card(
            "Gross Payroll",
            f'₹{data["total_gross_salary"]:,.2f}',
            "Before deductions",
            "📈",
        )

    with p4:
        metric_card(
            "Deductions",
            f'₹{data["total_deductions"]:,.2f}',
            "Total recorded deductions",
            "➖",
        )

    # Recent records
    st.markdown(
        '<div class="section-heading">Recent Records</div>',
        unsafe_allow_html=True,
    )

    employees_col, payroll_col = st.columns(2, gap="large")

    with employees_col:
        st.markdown(
            """
            <div class="content-card">
                <h3>👤 Recent Employees</h3>
                <p>Latest five employee records</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if data["recent_employees"].empty:
            st.info("No employee records yet. Add your first employee.")
        else:
            st.dataframe(
                data["recent_employees"],
                use_container_width=True,
                hide_index=True,
            )

        if st.button(
            "Manage Employees →",
            key="dashboard_manage_employees",
            use_container_width=True,
        ):
            navigate_to("Employee Management")
            st.rerun()

    with payroll_col:
        st.markdown(
            """
            <div class="content-card">
                <h3>💳 Recent Payroll Records</h3>
                <p>Latest five payroll records</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if data["recent_payroll"].empty:
            st.info("No payroll records yet. Generate payroll to see records here.")
        else:
            display_payroll = data["recent_payroll"].copy()

            display_payroll["Net Salary (₹)"] = display_payroll[
                "Net Salary (₹)"
            ].map(
                lambda amount: f"₹{float(amount):,.2f}"
            )

            st.dataframe(
                display_payroll,
                use_container_width=True,
                hide_index=True,
            )

        if st.button(
            "Manage Payroll →",
            key="dashboard_manage_payroll",
            use_container_width=True,
        ):
            navigate_to("Payroll Management")
            st.rerun()

    # Quick navigation
    st.markdown(
        '<div class="section-heading">Quick Navigation</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-caption">'
        'Jump directly to a frequently used module.'
        '</div>',
        unsafe_allow_html=True,
    )

    q1, q2, q3, q4, q5 = st.columns(5, gap="small")

    quick_actions = [
        (q1, "👥 Employees", "Employee Management"),
        (q2, "📅 Attendance", "Attendance Management"),
        (q3, "📝 Leaves", "Leave Management"),
        (q4, "💰 Payroll", "Payroll Management"),
        (q5, "📄 Payslips", "Payslips"),
    ]

    for column, label, destination in quick_actions:
        with column:
            if st.button(
                label,
                key=f"quick_{destination}",
                use_container_width=True,
            ):
                navigate_to(destination)
                st.rerun()


# =========================================================
# SIDEBAR
# =========================================================
def navigate_to(destination):
    st.session_state["pending_navigation"] = destination

with st.sidebar:

    st.markdown(
        """
        <div style="padding:8px 2px 0 2px;">
            <div style="font-size:29px;margin-bottom:5px;">▦</div>
            <div class="brand-title">PeopleDesk</div>
            <div class="brand-subtitle">
                EMPLOYEE &amp; HR MANAGEMENT
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Navigation")

    pages = [
        "Dashboard",
        "Employee Management",
        "Attendance Management",
        "Leave Management",
        "Payroll Management",
        "Payslips",
    ]

    if "pending_navigation" in st.session_state:
        st.session_state["navigation_radio"] = st.session_state.pop(
            "pending_navigation"
        )

    selected_page = st.radio(
        "Go to",
        pages,
        key="navigation_radio",
        label_visibility="collapsed",
    )

    st.markdown(
        """
        <div style="
            color:#B9C0E9;
            font-size:11px;
            margin-top:22px;
            padding-top:14px;
            border-top:1px solid rgba(255,255,255,0.14);
        ">
            <b>PeopleDesk HRMS</b><br>
            Local Application · HR Admin
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# PAGE ROUTING
# =========================================================
if selected_page == "Dashboard":
    render_dashboard()

elif selected_page == "Employee Management":
    render_employee_management()

elif selected_page == "Attendance Management":
    render_attendance_management()

elif selected_page == "Leave Management":
    render_leave_management()

elif selected_page == "Payroll Management":
    render_payroll_management()

elif selected_page == "Payslips":
    render_payslips()