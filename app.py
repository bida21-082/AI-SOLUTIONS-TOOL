import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

#page config
st.set_page_config(page_title="AI Solutions Performance Dashboard", layout="wide")

#tab spacing CSS
st.markdown("""
<style>
.stTabs [data-baseweb="tab-list"] {
    gap: 2rem !important;
    justify-content: center !important;
}
.stTabs [data-baseweb="tab"] {
    font-size: 1.1rem !important;
    padding: 0.5rem 1.5rem !important;
}
</style>
""", unsafe_allow_html=True)

#logo
st.sidebar.image("logo.jpg", width=150)

@st.cache_data
def load_data():
    df = pd.read_csv('ai_solutions_web_log.csv', parse_dates=['date'])
    return df

def filter_data_by_date(df):
    min_date = df['date'].min()
    max_date = df['date'].max()
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
    else:
        filtered_df = df.copy()
    return filtered_df

def speedometer(value, title="Conversion Rate"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#1f77b4"},
            'steps': [
                {'range': [0, 33], 'color': "#d62728"},
                {'range': [33, 66], 'color': "#ff7f0e"},
                {'range': [66, 100], 'color': "#2ca02c"}
            ],
        }
    ))
    fig.update_layout(height=300, margin=dict(t=50, b=0, l=0, r=0))
    return fig

def executive_view(df):
    st.header("Executive Summary")

    #Traffic and demo request conversion over years
    df['year'] = df['date'].dt.year
    if 'session_id' in df.columns:
        traffic_year = df.groupby('year')['session_id'].nunique().reset_index(name='Total Traffic')
    elif 'ip_address' in df.columns:
        traffic_year = df.groupby('year')['ip_address'].nunique().reset_index(name='Total Traffic')
    else:
        traffic_year = df.groupby('year').size().reset_index(name='Total Traffic')

    if 'demo_request' in df.columns:
        demo_year = df[df['demo_request'] == 1].groupby('year').size().reset_index(name='Demo Requests')
    else:
        demo_year = pd.DataFrame({'year': [], 'Demo Requests': []})

    combined = pd.merge(traffic_year, demo_year, on='year', how='left').fillna(0)
    combined['Conversion Rate (%)'] = (combined['Demo Requests'] / combined['Total Traffic']) * 100

    col5, col6 = st.columns([2,1])

    with col5:
        fig = px.bar(combined, x='year', y=['Total Traffic', 'Demo Requests'],
                     title="Web Traffic & Demo Requests Over Years",
                     labels={'value': 'Count', 'year': 'Year', 'variable': 'Metric'},
                     color_discrete_map={'Total Traffic': '#1f77b4', 'Demo Requests': '#ff7f0e'})
        fig.update_layout(barmode='group', xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col6:
        fig_gauge = speedometer(combined['Conversion Rate (%)'].iloc[-1] if not combined.empty else 0, title="Latest Demo Conversion Rate")
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("**Insight:** Conversion rate shows how effectively web traffic is turning into demo requests, a key step in the sales funnel.")

    st.markdown("---")
    st.header("Advanced Sales KPIs")

    df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()

    #Customer Acquisition Cost (CAC)
    st.subheader("Customer Acquisition Cost (CAC)")
    if {'marketing_expense', 'new_customers'}.issubset(df.columns):
        total_expense = df['marketing_expense'].sum()
        new_customers = df['new_customers'].sum()
        cac = total_expense / new_customers if new_customers > 0 else 0
        st.metric("CAC", f"${cac:,.2f}", help="Cost to acquire one new customer")

        monthly = df.groupby('month').agg({'marketing_expense':'sum', 'new_customers':'sum'}).reset_index()
        monthly['CAC'] = monthly.apply(lambda row: row['marketing_expense']/row['new_customers'] if row['new_customers']>0 else 0, axis=1)
        fig_cac = px.line(monthly, x='month', y='CAC', title="Monthly CAC Trend", labels={'month':'Month', 'CAC':'CAC ($)'})
        st.plotly_chart(fig_cac, use_container_width=True)
    else:
        st.info("Marketing expense or new customers data not available.")

    st.markdown("---")

    #Customer Retention Rate
    st.subheader("Customer Retention Rate")
    if {'total_customers', 'churned_customers'}.issubset(df.columns):
        total_customers = df['total_customers'].max()
        churned = df['churned_customers'].sum()
        retention_rate = ((total_customers - churned) / total_customers) * 100 if total_customers > 0 else 0
        st.metric("Retention Rate", f"{retention_rate:.2f}%", help="Percentage of customers retained")

        monthly = df.groupby('month').agg({'total_customers':'max', 'churned_customers':'sum'}).reset_index()
        monthly['Retention Rate'] = ((monthly['total_customers'] - monthly['churned_customers']) / monthly['total_customers']) * 100
        fig_retention = px.line(monthly, x='month', y='Retention Rate', title="Monthly Customer Retention Rate", labels={'month':'Month', 'Retention Rate':'Retention (%)'})
        st.plotly_chart(fig_retention, use_container_width=True)
    else:
        st.info("Total customers or churn data not available.")

    st.markdown("---")

    #Market Penetration Rate
    st.subheader("Market Penetration Rate")
    if {'total_customers', 'market_size'}.issubset(df.columns):
        total_customers = df['total_customers'].max()
        market_size = df['market_size'].max()
        penetration = (total_customers / market_size) * 100 if market_size > 0 else 0
        st.metric("Market Penetration", f"{penetration:.2f}%", help="Percentage of total market reached")

        monthly = df.groupby('month').agg({'total_customers':'max', 'market_size':'max'}).reset_index()
        monthly['Penetration'] = (monthly['total_customers'] / monthly['market_size']) * 100
        fig_penetration = px.line(monthly, x='month', y='Penetration', title="Monthly Market Penetration Rate", labels={'month':'Month', 'Penetration':'Penetration (%)'})
        st.plotly_chart(fig_penetration, use_container_width=True)
    else:
        st.info("Total customers or market size data not available.")

def sales_insights(df):
    st.header("Sales Insights")

    total_sessions = df['session_id'].nunique() if 'session_id' in df.columns else len(df)
    total_visitors = df['ip_address'].nunique() if 'ip_address' in df.columns else None
    total_jobs_placed = df['jobs_placed'].sum() if 'jobs_placed' in df.columns else 0
    total_job_requests = df['job_type_requested'].count() if 'job_type_requested' in df.columns else 0
    total_sales = df['sales'].sum() if 'sales' in df.columns else 0
    total_conversions = df['conversion_status'].sum() if 'conversion_status' in df.columns else 0

    conversion_rate = (total_conversions / total_sessions) * 100 if total_sessions else 0
    job_success_rate = (total_jobs_placed / total_job_requests) * 100 if total_job_requests else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", f"${total_sales:,.0f}", help="Total sales revenue")
    col2.metric("Job Success Rate", f"{job_success_rate:.2f}%", help="Jobs placed vs requested")
    col3.metric("Unique Visitors", total_visitors if total_visitors else "N/A", help="Distinct visitors during selected period")

    st.markdown("---")

    df['quarter'] = df['date'].dt.to_period('Q').astype(str)
    quarterly_sales = df.groupby(['quarter', 'product_type'])['sales'].sum().reset_index()
    yearly_sales = df.groupby(['date', 'product_type'])['sales'].sum().reset_index()

    col1, col2 = st.columns(2)

    with col1:
        fig_q = px.line(quarterly_sales, x='quarter', y='sales', color='product_type',
                        title="Quarterly Sales Trends by Product")
        fig_q.update_layout(xaxis_title="Quarter", yaxis_title="Sales")
        st.plotly_chart(fig_q, use_container_width=True)

    with col2:
        fig_y = px.bar(yearly_sales, x='date', y='sales', color='product_type',
                       title="Daily Sales by Product", barmode='stack')
        fig_y.update_layout(xaxis_title="Date", yaxis_title="Sales")
        st.plotly_chart(fig_y, use_container_width=True)

    st.subheader("Conversion Rates: Demo vs AI Assistant Requests")
    if {'demo_request', 'ai_assistant_request', 'conversion_status'}.issubset(df.columns):
        demo_conv = df[df['demo_request'] == 1]['conversion_status'].mean() * 100
        ai_conv = df[df['ai_assistant_request'] == 1]['conversion_status'].mean() * 100

        col3, col4 = st.columns(2)
        with col3:
            st.plotly_chart(speedometer(demo_conv, "Demo Request Conversion %"), use_container_width=True)
        with col4:
            st.plotly_chart(speedometer(ai_conv, "AI Assistant Conversion %"), use_container_width=True)
    else:
        st.info("Conversion data for demo and AI assistant requests is not available.")

    #Sales Growth Rate
    st.markdown("---")
    st.subheader("Sales Growth Rate")
    df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
    monthly_sales = df.groupby('month')['sales'].sum().reset_index()
    monthly_sales['Growth Rate (%)'] = monthly_sales['sales'].pct_change() * 100
    fig_growth = px.bar(monthly_sales, x='month', y='Growth Rate (%)', title="Monthly Sales Growth Rate", labels={'month':'Month', 'Growth Rate (%)':'Growth Rate (%)'})
    st.plotly_chart(fig_growth, use_container_width=True)

    #Marketing Campaign Performance
    st.markdown("---")
    st.subheader("Marketing Campaign Performance")
    if {'campaign_id', 'campaign_name', 'campaign_spend', 'campaign_revenue'}.issubset(df.columns):
        campaign_summary = df.groupby(['campaign_id', 'campaign_name']).agg({'campaign_spend':'sum', 'campaign_revenue':'sum'}).reset_index()
        campaign_summary['ROI'] = (campaign_summary['campaign_revenue'] - campaign_summary['campaign_spend']) / campaign_summary['campaign_spend'] * 100
        fig_campaign = px.bar(campaign_summary, x='campaign_name', y='ROI', color='ROI',
                     title="Campaign ROI (%)",
                     labels={'campaign_name':'Campaign', 'ROI':'Return on Investment (%)'},
                     color_continuous_scale=px.colors.sequential.Teal)
        fig_campaign.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_campaign, use_container_width=True)
    else:
        st.info("Campaign data not available.")

def product_insights(df):
    st.header("Product Insights")

    st.subheader("Top Product Globally")
    if 'product_type' in df.columns:
        product_counts = df['product_type'].value_counts().reset_index()
        product_counts.columns = ['Product Type', 'Count']
        top_product = product_counts.iloc[0]['Product Type']

        fig = px.bar(product_counts, x='Product Type', y='Count',
                     title="Product Popularity",
                     text='Count',
                     color='Product Type',
                     color_discrete_map={top_product: '#d62728'})
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"**Top Product Globally:** {top_product}")
    else:
        st.info("Product type data is not available.")

    st.subheader("Conversion Rates by Product Type")
    if {'product_type', 'conversion_status'}.issubset(df.columns):
        conv_rates = df.groupby('product_type')['conversion_status'].mean().reset_index()
        conv_rates['Conversion Rate (%)'] = conv_rates['conversion_status'] * 100
        fig_conv = px.bar(conv_rates, x='product_type', y='Conversion Rate (%)',
                          title="Conversion Rate by Product",
                          text=conv_rates['Conversion Rate (%)'].map(lambda x: f"{x:.1f}%"),
                          labels={'product_type': 'Product Type'})
        fig_conv.update_traces(textposition='outside')
        st.plotly_chart(fig_conv, use_container_width=True)
    else:
        st.info("Conversion data is not available.")

    #Product Deliverance Metrics
    st.markdown("---")
    st.subheader("Product Deliverance Metrics")
    if {'product_id', 'delivery_time_days', 'delivery_status'}.issubset(df.columns):
        avg_delivery_time = df['delivery_time_days'].mean()
        on_time_delivery_rate = (df[df['delivery_status'] == 'On Time'].shape[0] / df.shape[0]) * 100 if df.shape[0] > 0 else 0
        st.metric("Avg Delivery Time (days)", f"{avg_delivery_time:.2f}")
        st.metric("On-Time Delivery Rate", f"{on_time_delivery_rate:.2f}%", help="Percentage of deliveries on time")

        fig = px.histogram(df, x='delivery_time_days', nbins=30, title="Delivery Time Distribution (Days)", labels={'delivery_time_days':'Days'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Product delivery data not available.")

def main():
    st.title("AI Solutions Performance Dashboard")

    df = load_data()
    filtered_df = filter_data_by_date(df)
    tab_titles = ["Sales Insights", "Product Insights", "Executive Summary"]
    tabs = st.tabs(tab_titles)

    with tabs[0]:
        sales_insights(filtered_df)

    with tabs[1]:
        product_insights(filtered_df)

    with tabs[2]:
        executive_view(filtered_df)

if __name__ == "__main__":
    main()
