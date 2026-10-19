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
    page_title="PeopleDesk | HR & Payroll",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()


# =========================================================
# DESIGN SYSTEM
# =========================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #7667F8;
    --primary-dark: #5B4DE0;
    --navy: #191C3B;
    --text: #242744;
    --muted: #8186A1;
    --border: #E9EAF5;
    --surface: #FFFFFF;
    --background: #F5F6FC;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: var(--background);
    color: var(--text);
}

.block-container {
    max-width: 1600px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

/* Header */
[data-testid="stHeader"] {
    background: rgba(245, 246, 252, 0.95);
}

/* Premium sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #171A38 0%,
        #22264D 55%,
        #302D63 100%
    );
    border-right: 1px solid #30345C;
}

[data-testid="stSidebar"] > div:first-child {
    background: transparent;
}

[data-testid="stSidebar"] * {
    color: #F4F4FF;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 11px 13px;
    border-radius: 12px;
    transition: all 0.2s ease;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255, 255, 255, 0.10);
}

[data-testid="stSidebar"] [data-testid="stRadio"] label p {
    font-size: 13px;
    font-weight: 500;
}

.brand {
    padding: 12px 4px 28px;
}

.brand-icon {
    font-size: 30px;
    margin-bottom: 5px;
}

.brand-title {
    font-size: 28px;
    line-height: 1.2;
    font-weight: 800;
    letter-spacing: -1px;
    color: #FFFFFF;
}

.brand-subtitle {
    font-size: 10px;
    color: #BFC4E8;
    letter-spacing: 1.5px;
    margin-top: 7px;
}

.sidebar-footer {
    margin-top: 35px;
    padding-top: 17px;
    border-top: 1px solid rgba(255,255,255,0.15);
    color: #BFC4E8;
    font-size: 11px;
    line-height: 1.9;
}

/* Dashboard hero */
.hero {
    position: relative;
    overflow: hidden;
    padding: 30px 32px;
    border-radius: 22px;
    margin-bottom: 26px;
    background: linear-gradient(
        115deg,
        #E7E3FF 0%,
        #F7F6FF 53%,
        #E5F7F3 100%
    );
    border: 1px solid #E3E3F6;
    box-shadow: 0 10px 32px rgba(44, 48, 100, 0.06);
}

.hero-kicker {
    color: #6555E8;
    font-size: 10px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.8px;
}

.hero h1 {
    color: #202342;
    font-size: clamp(26px, 2.4vw, 35px);
    font-weight: 800;
    letter-spacing: -1.1px;
    line-height: 1.25;
    margin: 11px 0 8px;
}

.hero p {
    color: #6D728F;
    font-size: 14px;
    margin: 0;
}

.hero-date {
    color: #5F55D7;
    font-size: 12px;
    font-weight: 600;
    margin-top: 16px;
}

/* Section headings */
.section-heading {
    color: #242744;
    font-size: 19px;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin: 27px 0 7px;
}

.section-caption {
    color: #858AA3;
    font-size: 12px;
    line-height: 1.6;
    margin: 0 0 17px;
}

/* KPI cards */

.metric-card {
    background: #FFFFFF;
    border: 1px solid #EAE7FA;
    border-radius: 18px;
    padding: 22px 24px;
    box-shadow: 0 4px 18px rgba(35, 32, 85, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 28px rgba(35, 32, 85, 0.10);
}


.metric-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.metric-label {
    color: #555B7A !important;
    font-size: 13px;
    font-weight: 600;
    opacity: 1;
}


.metric-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 13px;
    font-size: 19px;
    background: #EFEDFF;
}

.metric-value {
    color: #222541;
    font-size: clamp(23px, 2vw, 30px);
    line-height: 1.25;
    font-weight: 800;
    letter-spacing: -0.8px;
    margin-top: 13px;
    overflow-wrap: anywhere;
}

.metric-note {
    color: #858AA3;
    font-size: 11px;
    line-height: 1.5;
    margin-top: 7px;
}

/* Content panels */
.content-card {
    background: #FFFFFF;
    border: 1px solid #E9EAF5;
    border-radius: 17px;
    padding: 18px 20px;
    margin-bottom: 10px;
    box-shadow: 0 5px 18px rgba(38, 44, 85, 0.035);
}

.content-card h3 {
    color: #252946;
    font-size: 15px;
    font-weight: 750;
    margin: 0 0 6px;
}

.content-card p {
    color: #858AA3;
    font-size: 12px;
    line-height: 1.6;
    margin: 0;
}

/* Buttons */
div.stButton > button {
    border-radius: 11px;
    min-height: 42px;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid #E0E2F0;
    transition: all 0.2s ease;
}

div.stButton > button[kind="primary"] {
    background: #7667F8;
    color: #FFFFFF;
    border-color: #7667F8;
    box-shadow: 0 4px 12px rgba(118, 103, 248, 0.18);
}

div.stButton > button[kind="primary"]:hover {
    background: #5B4DE0;
    border-color: #5B4DE0;
    color: #FFFFFF;
    transform: translateY(-1px);
}

div.stButton > button:hover {
    border-color: #BDB7FF;
    color: #5B4DE0;
}

/* Form controls */
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] > div {
    border-radius: 10px;
}

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stTextArea"] textarea {
    border-radius: 10px;
}

/* Tables */
div[data-testid="stDataFrame"] {
    border: 1px solid #E9EAF5;
    border-radius: 13px;
    overflow: hidden;
    background: #FFFFFF;
}

/* Charts */
[data-testid="stPlotlyChart"] {
    background: #FFFFFF;
    border: 1px solid #E9EAF5;
    border-radius: 17px;
    padding: 8px 10px 3px;
    box-shadow: 0 5px 18px rgba(38, 44, 85, 0.035);
}

/* Alerts */
[data-testid="stAlert"] {
    border-radius: 12px;
}

/* Dividers */
hr {
    border-color: #E7E9F3;
}

/* Hide Streamlit footer and menu */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

/* Responsive styling */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem;
    }

    .hero {
        padding: 22px;
        border-radius: 17px;
    }

    .metric-card {
        padding: 14px;
        min-height: 120px;
    }

    .section-heading {
        font-size: 17px;
    }

    .content-card {
        padding: 15px;
    }
}

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# DATABASE-DRIVEN DASHBOARD DATA
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
            SELECT
                COUNT(DISTINCT employee_id) AS present_today
            FROM attendance
            WHERE attendance_date = ?
              AND status IN ('Present', 'Half Day')
            """,
            conn,
            params=(today.isoformat(),),
        )

        on_leave = pd.read_sql_query(
            """
            SELECT COUNT(DISTINCT employee_id) AS employees_on_leave
            FROM leave_requests
            WHERE status = 'Approved'
              AND start_date <= ?
              AND end_date >= ?
            """,
            conn,
            params=(today.isoformat(), today.isoformat()),
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
                COALESCE(NULLIF(TRIM(department), ''), 'Unassigned')
                    AS Department,
                COUNT(*) AS Employees
            FROM employees
            WHERE employment_status = 'Active'
            GROUP BY COALESCE(NULLIF(TRIM(department), ''), 'Unassigned')
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
            ORDER BY pay_month DESC
            LIMIT 6
            """,
            conn,
        )

    payroll_trend = payroll_trend.sort_values("Month") if not payroll_trend.empty else payroll_trend

    return {
        "today": today.strftime("%A, %d %B %Y"),
        "month_key": month_key,
        "total_employees": int(employee_counts.iloc[0]["total_employees"] or 0),
        "active_employees": int(employee_counts.iloc[0]["active_employees"] or 0),
        "present_today": int(attendance.iloc[0]["present_today"] or 0),
        "employees_on_leave": int(on_leave.iloc[0]["employees_on_leave"] or 0),
        "pending_leaves": int(leaves.iloc[0]["pending_leaves"] or 0),
        "payroll_records": int(payroll_summary.iloc[0]["payroll_records"] or 0),
        "total_net_salary": float(payroll_summary.iloc[0]["total_net_salary"] or 0),
        "total_gross_salary": float(payroll_summary.iloc[0]["total_gross_salary"] or 0),
        "total_deductions": float(payroll_summary.iloc[0]["total_deductions"] or 0),
        "recent_employees": recent_employees,
        "recent_payroll": recent_payroll,
        "departments": departments,
        "payroll_trend": payroll_trend,
    }


# =========================================================
# REUSABLE UI COMPONENTS
# =========================================================
def metric_card(label, value, note, icon):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-top">
                <div class="metric-label">{escape(str(label))}</div>
                <div class="metric-icon">{icon}</div>
            </div>
            <div class="metric-value">{escape(str(value))}</div>
            <div class="metric-note">{escape(str(note))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_heading(title, caption=None):
    st.markdown(
        f'<div class="section-heading">{escape(title)}</div>',
        unsafe_allow_html=True,
    )
    if caption:
        st.markdown(
            f'<div class="section-caption">{escape(caption)}</div>',
            unsafe_allow_html=True,
        )


def content_heading(title, subtitle):
    st.markdown(
        f"""
        <div class="content-card">
            <h3>{escape(title)}</h3>
            <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def navigate_to(destination):
    st.session_state["pending_navigation"] = destination


# =========================================================
# DASHBOARD
# =========================================================
def render_dashboard():
    data = get_dashboard_data()

    # Welcome banner
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-kicker">People Operations</div>
            <h1>PeopleDesk Dashboard</h1>
            <p>Your workforce overview, all in one place.</p>
            <div class="hero-date">
                📅 {escape(data["today"])} &nbsp; · &nbsp; HR Admin Dashboard
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Workforce KPIs
    section_heading(
        "Organization Overview",
        "A live snapshot of your employee records and daily workforce.",
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
            "Currently active employees",
            "🟢",
        )

    with c3:
        metric_card(
            "Present Today",
            data["present_today"],
            "Present or half-day attendance",
            "📅",
        )

    with c4:
        metric_card(
            "Pending Leaves",
            data["pending_leaves"],
            "Awaiting HR review",
            "🕒",
        )

    # Analytics
    section_heading(
        "Workforce Analytics",
        "Explore department distribution and historical payroll totals.",
    )

    left, right = st.columns(2, gap="large")

    with left:
        content_heading(
            "👥 Department Distribution",
            "Active employees grouped by department",
        )

        departments = data["departments"]

        if departments.empty:
            st.info("Add active employees to see department analytics.")
        else:
            fig = px.pie(
                departments,
                names="Department",
                values="Employees",
                hole=0.64,
                color_discrete_sequence=[
                    "#7667F8",
                    "#25B8A5",
                    "#FF7C9C",
                    "#F4B544",
                    "#4D91F7",
                    "#9D7BE8",
                ],
            )

            fig.update_traces(
                textposition="inside",
                textinfo="percent",
                marker=dict(line=dict(color="#FFFFFF", width=3)),
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Employees: %{value}<br>"
                    "Share: %{percent}"
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
                    y=-0.15,
                    xanchor="center",
                    x=0.5,
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#626987", family="Inter"),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                key="department_distribution_chart",
            )

    with right:
        content_heading(
            "💰 Monthly Payroll Trend",
            "Net salary totals from generated payroll records",
        )

        payroll_trend = data["payroll_trend"]

        if payroll_trend.empty:
            st.info("Generate payroll records to see the payroll trend.")
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
                color_discrete_sequence=["#7667F8"],
            )

            fig.update_traces(
                texttemplate="₹%{text:,.0f}",
                textposition="outside",
                cliponaxis=False,
                marker_line_width=0,
                hovertemplate=(
                    "Month: %{x}<br>"
                    "Net Salary: ₹%{y:,.2f}"
                    "<extra></extra>"
                ),
            )

            fig.update_layout(
                height=330,
                margin=dict(t=30, b=45, l=15, r=15),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    type="category",
                    title="Payroll Month",
                    showgrid=False,
                ),
                yaxis=dict(
                    title="Net Salary (₹)",
                    gridcolor="#ECEEF7",
                    zeroline=False,
                    rangemode="tozero",
                ),
                showlegend=False,
                font=dict(color="#626987", family="Inter"),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                key="monthly_payroll_chart",
            )

    # Payroll summary
    section_heading(
        "Payroll Summary",
        f"Recorded payroll totals for {data['month_key']}.",
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
            f"₹{data['total_net_salary']:,.2f}",
            "Take-home payroll total",
            "💸",
        )

    with p3:
        metric_card(
            "Gross Payroll",
            f"₹{data['total_gross_salary']:,.2f}",
            "Before deductions",
            "📈",
        )

    with p4:
        metric_card(
            "Total Deductions",
            f"₹{data['total_deductions']:,.2f}",
            "Recorded deductions",
            "➖",
        )

    # Recent records
    section_heading(
        "Recent Records",
        "Quick access to the latest employee and payroll entries.",
    )

    employee_col, payroll_col = st.columns(2, gap="large")

    with employee_col:
        content_heading(
            "👤 Recent Employees",
            "The five most recently added employee records",
        )

        employees = data["recent_employees"]

        if employees.empty:
            st.info("No employee records yet. Add your first employee.")
        else:
            st.dataframe(
                employees,
                use_container_width=True,
                hide_index=True,
            )

        st.button(
            "Manage Employees →",
            key="dashboard_manage_employees",
            use_container_width=True,
            on_click=navigate_to,
            args=("Employee Management",),
        )

    with payroll_col:
        content_heading(
            "💳 Recent Payroll Records",
            "The five latest payroll entries",
        )

        payroll = data["recent_payroll"]

        if payroll.empty:
            st.info("No payroll records yet. Generate payroll to see them.")
        else:
            display_payroll = payroll.copy()
            display_payroll["Net Salary (₹)"] = display_payroll[
                "Net Salary (₹)"
            ].apply(
                lambda amount: f"₹{float(amount):,.2f}"
            )

            st.dataframe(
                display_payroll,
                use_container_width=True,
                hide_index=True,
            )

        st.button(
            "Manage Payroll →",
            key="dashboard_manage_payroll",
            use_container_width=True,
            on_click=navigate_to,
            args=("Payroll Management",),
        )

    # Quick navigation
    section_heading(
        "Quick Navigation",
        "Jump directly to a frequently used HR module.",
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
            st.button(
                label,
                key=f"quick_{destination}",
                use_container_width=True,
                on_click=navigate_to,
                args=(destination,),
            )

    # Small footer
    st.markdown(
        """
        <div style="
            text-align:center;
            color:#969AB0;
            font-size:11px;
            margin-top:32px;
            padding-top:16px;
            border-top:1px solid #E6E8F2;
        ">
            PeopleDesk · HR & Payroll Management System
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================
with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-icon">👥</div>
            <div class="brand-title">PeopleDesk</div>
            <div class="brand-subtitle">HR &amp; PAYROLL SYSTEM</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Workspace")

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
        "Navigation",
        pages,
        key="navigation_radio",
        label_visibility="collapsed",
    )

    st.markdown(
        """
        <div class="sidebar-footer">
            <b>PeopleDesk HRMS</b><br>
            Local Application · HR Admin<br>
            <span style="color:#969CC8;">
                Workforce management made simpler.
            </span>
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