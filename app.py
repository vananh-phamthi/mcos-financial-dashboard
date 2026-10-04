import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="MCOS & P&L Executive Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Custom Styling (Executive Dark/Modern Theme)
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #092c21 0%, #00543D 50%, #064e3b 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 84, 61, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .main-header h1 {
        margin: 0;
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #ffffff;
    }
    .main-header p {
        margin: 6px 0 0 0;
        font-size: 14px;
        color: #a7f3d0;
        font-weight: 500;
    }
    
    .kpi-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 18px 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
    }
    .kpi-title {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #64748b;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 800;
        color: #0f172a;
        font-family: 'JetBrains Mono', monospace;
    }
    .kpi-sub {
        font-size: 12px;
        margin-top: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .badge-pos {
        background-color: #dcfce7;
        color: #15803d;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 11px;
    }
    .badge-neg {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 11px;
    }
    .badge-neutral {
        background-color: #f1f5f9;
        color: #475569;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 11px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------
@st.cache_data
def load_data():
    csv_path = os.path.join(os.path.dirname(__file__), "data", "mcos_tabular_data.csv")
    if not os.path.exists(csv_path):
        # Fallback to current folder
        csv_path = "mcos_tabular_data.csv"
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return df
    else:
        st.error(f"Data file not found at {csv_path}. Please ensure `mcos_tabular_data.csv` is present.")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

# ---------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/combo-chart.png", width=64)
    st.title("Filters & Scenarios")
    
    # Region Filter
    regions = ["All Regions"] + sorted(df["Region"].dropna().unique().tolist())
    selected_region = st.selectbox("🌍 Select Region", regions)
    
    # Filter df by Region for Entity choices
    if selected_region != "All Regions":
        filtered_by_reg = df[df["Region"] == selected_region]
    else:
        filtered_by_reg = df
        
    # Entity Filter
    entities = sorted(filtered_by_reg["Entity"].dropna().unique().tolist())
    # Default priority to Total Vietnam or first available Total
    default_ix = 0
    if "Total Vietnam" in entities:
        default_ix = entities.index("Total Vietnam")
    elif len(entities) > 0:
        default_ix = 0
        
    selected_entity = st.selectbox("🏢 Select Business Unit / Entity", entities, index=default_ix)
    
    # Benchmark / Variance Mode
    st.markdown("---")
    st.subheader("Benchmark Comparison")
    comp_mode = st.radio(
        "Compare 2027 Budget Against:",
        options=[
            "2026 LTF (8+4)",
            "2026 Budget",
            "2025 Actual (Y-1)"
        ],
        index=0
    )
    
    # Category Filter
    categories = ["All Categories"] + sorted(df["Category"].dropna().unique().tolist())
    selected_cat = st.selectbox("📑 P&L Category Filter", categories)
    
    st.markdown("---")
    st.caption("Aboitiz Foods MCOS & P&L Intelligence | Currency: USD '000")

# Filter data for selected entity
entity_df = df[df["Entity"] == selected_entity]

if selected_cat != "All Categories":
    table_df = entity_df[entity_df["Category"] == selected_cat]
else:
    table_df = entity_df

# Helper function to get metric values
def get_account_metric(df_subset, account_match):
    match = df_subset[df_subset["Account_Name"].str.contains(account_match, case=False, na=False)]
    if not match.empty:
        row = match.iloc[0]
        return {
            "2024A": row.get("FY2024_Actual", 0),
            "2025A": row.get("FY2025_Actual_Yminus1", 0),
            "2026B": row.get("FY2026_Budget", 0),
            "2026LTF": row.get("FY2026_LTF", 0),
            "2027B": row.get("FY2027_Budget", 0),
            "var_26LTF": row.get("Var_27B_vs_26LTF", 0),
            "pct_26LTF": row.get("Pct_27B_vs_26LTF", 0),
            "var_26B": row.get("Var_27B_vs_26B", 0),
            "pct_26B": row.get("Pct_27B_vs_26B", 0),
            "var_25A": row.get("Var_27B_vs_25A", 0),
            "pct_25A": row.get("Pct_27B_vs_25A", 0)
        }
    return {k: 0 for k in ["2024A", "2025A", "2026B", "2026LTF", "2027B", "var_26LTF", "pct_26LTF", "var_26B", "pct_26B", "var_25A", "pct_25A"]}

# ---------------------------------------------------------
# Header Banner
# ---------------------------------------------------------
st.markdown(f"""
<div class="main-header">
    <h1>📈 {selected_entity.upper()} — P&L & MCOS EXECUTIVE DASHBOARD</h1>
    <p>Financial Performance & Budget Variance Analysis | Actual 2024, Actual 2025 (Y-1), Budget 2026, LTF 2026 (8+4) vs Budget 2027 (USD '000)</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Executive KPI Scorecards
# ---------------------------------------------------------
vol_data = get_account_metric(entity_df, "Total Volumes")
sales_data = get_account_metric(entity_df, "Total Net Sales")
mat_data = get_account_metric(entity_df, "Total Raw Materials")
mcos_data = get_account_metric(entity_df, "Total MCOS")
cogs_data = get_account_metric(entity_df, "Total COGS")
hc_data = get_account_metric(entity_df, "Total Head Count")

# Determine active variance benchmark
if comp_mode == "2026 LTF (8+4)":
    v_key, p_key, base_name = "var_26LTF", "pct_26LTF", "vs 26LTF"
elif comp_mode == "2026 Budget":
    v_key, p_key, base_name = "var_26B", "pct_26B", "vs 26B"
else:
    v_key, p_key, base_name = "var_25A", "pct_25A", "vs 25A (Y-1)"

def render_kpi(col, title, val_2027, diff, pct, unit="", is_cost=False):
    # For cost, positive variance is negative (over budget)
    if diff > 0:
        badge_class = "badge-neg" if is_cost else "badge-pos"
        badge_text = f"+{diff:,.1f}{unit} (+{pct:.1f}%) {base_name}"
    elif diff < 0:
        badge_class = "badge-pos" if is_cost else "badge-neg"
        badge_text = f"{diff:,.1f}{unit} ({pct:.1f}%) {base_name}"
    else:
        badge_class = "badge-neutral"
        badge_text = f"0.0{unit} (0.0%) {base_name}"
        
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{val_2027:,.1f}{unit}</div>
            <div class="kpi-sub">
                <span class="{badge_class}">{badge_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)
render_kpi(k1, "Volume (MT)", vol_data["2027B"], vol_data[v_key], vol_data[p_key])
render_kpi(k2, "Net Sales", sales_data["2027B"], sales_data[v_key], sales_data[p_key], unit="k")
render_kpi(k3, "Raw Material COS", mat_data["2027B"], mat_data[v_key], mat_data[p_key], unit="k", is_cost=True)
render_kpi(k4, "Total MCOS", mcos_data["2027B"], mcos_data[v_key], mcos_data[p_key], unit="k", is_cost=True)
render_kpi(k5, "Total COGS", cogs_data["2027B"], cogs_data[v_key], cogs_data[p_key], unit="k", is_cost=True)
render_kpi(k6, "Headcount (Closing)", hc_data["2027B"], hc_data[v_key], hc_data[p_key], is_cost=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Executive Visualizations Tabs
# ---------------------------------------------------------
tab_charts, tab_table, tab_waterfall, tab_cross_regional = st.tabs([
    "📊 Financial Trajectory & Cost Structure",
    "📋 Detailed Accounts Table",
    "📉 Variance Analysis (Cost Drivers)",
    "🌐 Cross-Regional Comparison"
])

# ---------------------------------------------------------
# Tab 1: Financial Trajectory
# ---------------------------------------------------------
with tab_charts:
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.subheader("Multi-Year Trajectory: Revenue, Volume & COGS")
        scenarios = ["2024 Actual", "2025 Actual (Y-1)", "2026 Budget", "2026 LTF (8+4)", "2027 Budget"]
        
        fig_traj = go.Figure()
        fig_traj.add_trace(go.Bar(
            x=scenarios,
            y=[sales_data["2024A"], sales_data["2025A"], sales_data["2026B"], sales_data["2026LTF"], sales_data["2027B"]],
            name="Net Sales ($k)",
            marker_color="#00543D"
        ))
        fig_traj.add_trace(go.Bar(
            x=scenarios,
            y=[cogs_data["2024A"], cogs_data["2025A"], cogs_data["2026B"], cogs_data["2026LTF"], cogs_data["2027B"]],
            name="Total COGS ($k)",
            marker_color="#dc2626"
        ))
        fig_traj.add_trace(go.Scatter(
            x=scenarios,
            y=[vol_data["2024A"], vol_data["2025A"], vol_data["2026B"], vol_data["2026LTF"], vol_data["2027B"]],
            name="Volume (MT)",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="#0284c7", width=3),
            marker=dict(size=8)
        ))
        
        fig_traj.update_layout(
            barmode="group",
            height=420,
            margin=dict(l=40, r=40, t=30, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(title="USD ('000)", showgrid=True, gridcolor="#f1f5f9"),
            yaxis2=dict(title="Volume (MT)", overlaying="y", side="right", showgrid=False),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        st.plotly_chart(fig_traj, use_container_width=True)

    with col_c2:
        st.subheader("MCOS Component Evolution (VC vs FC vs Depr)")
        
        vc_data = get_account_metric(entity_df, "MCOS-Standard Absorption Cost - Variable")
        if vc_data["2027B"] == 0:
            vc_data = get_account_metric(entity_df, "VARIABLE COST")
            
        fc_data = get_account_metric(entity_df, "MCOS-Standard Absorption Cost - Fixed")
        if fc_data["2027B"] == 0:
            fc_data = get_account_metric(entity_df, "FIXED COST")
            
        depr_data = get_account_metric(entity_df, "Total MCOS - Depreciation")
        
        fig_mcos = go.Figure()
        fig_mcos.add_trace(go.Bar(
            x=scenarios,
            y=[vc_data["2024A"], vc_data["2025A"], vc_data["2026B"], vc_data["2026LTF"], vc_data["2027B"]],
            name="Variable Cost (VC)",
            marker_color="#0ea5e9"
        ))
        fig_mcos.add_trace(go.Bar(
            x=scenarios,
            y=[fc_data["2024A"], fc_data["2025A"], fc_data["2026B"], fc_data["2026LTF"], fc_data["2027B"]],
            name="Fixed Cost (FC)",
            marker_color="#f59e0b"
        ))
        fig_mcos.add_trace(go.Bar(
            x=scenarios,
            y=[depr_data["2024A"], depr_data["2025A"], depr_data["2026B"], depr_data["2026LTF"], depr_data["2027B"]],
            name="Depreciation (PPE/ROU)",
            marker_color="#7c3aed"
        ))
        
        fig_mcos.update_layout(
            barmode="stack",
            height=420,
            margin=dict(l=40, r=40, t=30, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(title="USD ('000)", showgrid=True, gridcolor="#f1f5f9"),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        st.plotly_chart(fig_mcos, use_container_width=True)

# ---------------------------------------------------------
# Tab 2: Detailed Accounts Table
# ---------------------------------------------------------
with tab_table:
    st.subheader(f"P&L Line Items ({selected_entity})")
    
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        search_query = st.text_input("🔍 Search by Account Name or Code", "")
    with col_s2:
        export_csv = st.download_button(
            label="📥 Download Data (CSV)",
            data=table_df.to_csv(index=False).encode('utf-8'),
            file_name=f"{selected_entity}_PL_MCOS_2027B.csv",
            mime='text/csv'
        )
    
    display_df = table_df.copy()
    if search_query:
        display_df = display_df[
            display_df["Account_Name"].str.contains(search_query, case=False, na=False) |
            display_df["Account_Code"].astype(str).str.contains(search_query, case=False, na=False)
        ]
        
    # Re-order and rename columns for display
    cols_to_show = [
        "Category", "Account_Code", "Account_Name",
        "FY2024_Actual", "FY2025_Actual_Yminus1", "FY2026_Budget", "FY2026_LTF", "FY2027_Budget"
    ]
    
    if comp_mode == "2026 LTF (8+4)":
        cols_to_show += ["Var_27B_vs_26LTF", "Pct_27B_vs_26LTF"]
    elif comp_mode == "2026 Budget":
        cols_to_show += ["Var_27B_vs_26B", "Pct_27B_vs_26B"]
    else:
        cols_to_show += ["Var_27B_vs_25A", "Pct_27B_vs_25A"]
        
    final_view = display_df[cols_to_show].rename(columns={
        "Category": "Category",
        "Account_Code": "Code",
        "Account_Name": "Account Name",
        "FY2024_Actual": "2024 Actual",
        "FY2025_Actual_Yminus1": "2025 Actual (Y-1)",
        "FY2026_Budget": "2026 Budget",
        "FY2026_LTF": "2026 LTF (8+4)",
        "FY2027_Budget": "2027 Budget",
        "Var_27B_vs_26LTF": "Variance ($)",
        "Pct_27B_vs_26LTF": "Variance (%)",
        "Var_27B_vs_26B": "Variance ($)",
        "Pct_27B_vs_26B": "Variance (%)",
        "Var_27B_vs_25A": "Variance ($)",
        "Pct_27B_vs_25A": "Variance (%)"
    })
    
    st.dataframe(
        final_view.style.format({
            "2024 Actual": "{:,.2f}",
            "2025 Actual (Y-1)": "{:,.2f}",
            "2026 Budget": "{:,.2f}",
            "2026 LTF (8+4)": "{:,.2f}",
            "2027 Budget": "{:,.2f}",
            "Variance ($)": "{:,.2f}",
            "Variance (%)": "{:.2f}%"
        }),
        height=550,
        use_container_width=True
    )

# ---------------------------------------------------------
# Tab 3: Variance Waterfall / Drivers
# ---------------------------------------------------------
with tab_waterfall:
    st.subheader(f"Top Cost Variance Drivers (2027 Budget vs {comp_mode})")
    
    # Filter to MCOS cost items (excluding subtotals)
    cost_items = entity_df[
        entity_df["Category"].isin(["MCOS - Variable Cost", "MCOS - Fixed Cost", "MCOS - Depreciation", "Raw Materials & COGS"]) &
        ~entity_df["Account_Name"].str.contains("Total|Check", case=False, na=False)
    ].copy()
    
    var_col = "Var_27B_vs_26LTF" if comp_mode == "2026 LTF (8+4)" else ("Var_27B_vs_26B" if comp_mode == "2026 Budget" else "Var_27B_vs_25A")
    cost_items["Abs_Var"] = cost_items[var_col].abs()
    top_drivers = cost_items.sort_values(by="Abs_Var", ascending=False).head(12)
    
    fig_drivers = px.bar(
        top_drivers,
        x=var_col,
        y="Account_Name",
        orientation="h",
        color=var_col,
        color_continuous_scale=["#15803d", "#f1f5f9", "#b91c1c"],
        labels={var_col: f"Variance ($k) vs {comp_mode}", "Account_Name": "Account Line Item"},
        title=f"Top 12 Cost Variances ($k) — Positive = Cost Increase, Negative = Cost Reduction"
    )
    fig_drivers.update_layout(
        height=500,
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    st.plotly_chart(fig_drivers, use_container_width=True)

# ---------------------------------------------------------
# Tab 4: Cross-Regional Comparison
# ---------------------------------------------------------
with tab_cross_regional:
    st.subheader("Cross-Regional Summary (All Business Units)")
    
    summary_entities = ["Total Vietnam", "Total China", "Total Indonesia", "Total Msia", "Sri Lanka", "DASH"]
    reg_df = df[df["Entity"].isin(summary_entities)]
    
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        vol_reg = reg_df[reg_df["Account_Name"].str.contains("Total Volumes", case=False, na=False)]
        fig_reg_vol = px.bar(
            vol_reg,
            x="Entity",
            y="FY2027_Budget",
            color="Region",
            text_auto=".1s",
            title="2027 Budgeted Volumes (MT) by Region",
            color_discrete_sequence=["#00543D", "#0284c7", "#f59e0b", "#7c3aed", "#ec4899", "#10b981"]
        )
        fig_reg_vol.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=400)
        st.plotly_chart(fig_reg_vol, use_container_width=True)
        
    with col_r2:
        mcos_reg = reg_df[reg_df["Account_Name"].str.contains("Total MCOS", case=False, na=False) & ~reg_df["Account_Name"].str.contains("Depreciation", case=False, na=False)]
        fig_reg_mcos = px.bar(
            mcos_reg,
            x="Entity",
            y="FY2027_Budget",
            color="Region",
            text_auto=".1s",
            title="2027 Budgeted Total MCOS (USD '000) by Region",
            color_discrete_sequence=["#00543D", "#0284c7", "#f59e0b", "#7c3aed", "#ec4899", "#10b981"]
        )
        fig_reg_mcos.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=400)
        st.plotly_chart(fig_reg_mcos, use_container_width=True)
