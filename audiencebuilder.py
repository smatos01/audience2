import pandas as pd  # pip install pandas openpyxl
import plotly.express as px  # pip install plotly-express
import streamlit as st  # pip install streamlit
from os import chdir, getcwd
from datetime import date, datetime, timedelta

import pickle
from pathlib import Path
import streamlit_authenticator as stauth  

# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="Audience Builder",
                   page_icon=":ring:",
                   layout="wide")

# --- USER AUTHENTICATION ---
names = ["Sandro Matos", "Chantelle Whelan"]
usernames = ["sandro.matos", "chantelle.whelan"]

# load hashed passwords
file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

#Create a dictionary for the credentials
credentials = {
"usernames":{
usernames[0]:{"name":names[0],"password":hashed_passwords[0]},
usernames[1]:{"name":names[1],"password":hashed_passwords[1]}            
            }
              }

authenticator = stauth.Authenticate(credentials,"my_app_cookie", "abcdef_key", cookie_expiry_days=30)
#number of days you don’t need to login again. If 0 you always need to login.

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect") #red box

if authentication_status == None:
    st.warning("Please enter your username and password") #yellow box

if authentication_status: #if true, then run our app

    # ---- READ EXCEL ----
    @st.cache_data #cache so doesn't load data every time we refresh dashboard
    def get_data_from_excel():
        df = pd.read_excel(
            io="customer_dummy_data.xlsx",
            engine="openpyxl",
            sheet_name="Sheet1",
            skiprows=0,
            usecols="A:H",
            nrows=1000,
        )
        return df

    chdir('C:\\Users\\smatos\\OneDrive - dentsu\\streamlit')

    df = get_data_from_excel()



    # ---- SIDEBAR ----
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title(f"So great to have you here, {name}!! 😹")

    st.sidebar.header("Basic Filters:")

    country = st.sidebar.multiselect(
        "Select the Country:",
        options=df["country"].unique(),
        default=df["country"].unique()
    )

    membership = st.sidebar.multiselect(
        "Select Membership Status:",
        options=df["membership"].unique(),
        default=df["membership"].unique()
    )

    gender = st.sidebar.multiselect(
        "Select the Gender:",
        options=df["gender"].unique(),
        default=df["gender"].unique()
    )

    st.sidebar.header("Advanced Filters:")

    nbr_advanced = st.sidebar.selectbox(
        "Select The number of advanced selections:",
        options=range(0, 2),
    )

    purchase_period1 = ''
    if nbr_advanced == 1:
        purchase_flag1 = st.sidebar.selectbox(
            "Purchase Behaviour:",
            options=['Did Purchase','Did Not Purchase'],
        )

        purchase_product1 = st.sidebar.multiselect(
            "Product:",
            options=df["product"].unique(),
            default=df["product"].unique()
        )

        purchase_period1 = st.sidebar.text_input('Time Period (last number of days):', '')


    df_selection1 = df.query(
        "country == @country & membership == @membership & gender == @gender"
    )

    if purchase_period1=='':
        df_selection = df_selection1
    else:
        date_target = date.today() - timedelta(days=int(purchase_period1))
        if purchase_flag1 == 'Did Purchase':
            df_to_keep = df_selection1.query(
                "date >= @date_target & product == @purchase_product1"
            )
            df_customers_to_keep = df_to_keep["customer_id"].unique().tolist()
            df_selection = df_selection1.query(
                "customer_id == @df_customers_to_keep"
            )
        else:
            df_to_remove = df_selection1.query(
                "date >= @date_target & product == @purchase_product1"
            )
            df_customers_to_remove = df_to_remove["customer_id"].unique().tolist()
            df_selection = df_selection1.query(
                "customer_id != @df_customers_to_remove"
            )

    # ---- MAINPAGE ----
    st.title(":ring: Audience Builder")
    st.markdown("##") #inserts a paragraph



    # TOP METRICS
    total_customers = int(df_selection["customer_id"].nunique())
    total_customers_perc = round(total_customers/int(df["customer_id"].nunique())*100,1)
    total_orders = int(df_selection["order_id"].nunique())
    avg_orders = round(total_orders/total_customers,1)
    total_quantity = int(df_selection["quantity"].sum())
    upt = round(total_quantity/total_orders,1)


    left_column, middle_column, right_column = st.columns(3)
    with left_column:
        st.subheader("Number of Customers:")
        st.subheader(f"{total_customers:,} ({total_customers_perc:,}%)")
    with middle_column:
        st.subheader("Avg Number of Orders:")
        st.subheader(f"{avg_orders:,}")
    with right_column:
        st.subheader("UPT:")
        st.subheader(f"{upt:,}")

    st.markdown("""---""")

    # Customers by Gender [PIE CHART]
    customers_by_gender = (
        df_selection.groupby(by=["gender"]).nunique()[["customer_id"]]
    )

    fig_customers_by_gender = px.pie(
        customers_by_gender,
        values="customer_id",
        names=customers_by_gender.index,
        title="<b># Customers by Gender</b>"
    )

    # Customers by Membership [PIE CHART]
    customers_by_membership = (
        df_selection.groupby(by=["membership"]).nunique()[["customer_id"]]
    )

    fig_customers_by_membership = px.pie(
        customers_by_membership,
        values="customer_id",
        names=customers_by_membership.index,
        title="<b># Customers by Membership</b>"
    )

    left_column, right_column = st.columns(2)
    left_column.plotly_chart(fig_customers_by_gender, use_container_width=True)
    right_column.plotly_chart(fig_customers_by_membership, use_container_width=True)

    # QUANTITY BY PRODUCT [BAR CHART] 
##    qty_by_product = df_selection.groupby(by=["product"]).sum()[["quantity"]]

    qty_by_product = df_selection.groupby(by=["product"]).nunique()[["customer_id"]]
    
    fig_qty_by_product = px.bar(
        qty_by_product,
        x=qty_by_product.index,
        y="customer_id",
        title="<b>Quantity by product</b>",
        color_discrete_sequence=["#0083B8"] * len(qty_by_product),
        template="plotly_white",
    )

    st.plotly_chart(fig_qty_by_product)


    st.markdown("""---""")


    # ---- HIDE STREAMLIT STYLE ----
    hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
    st.markdown(hide_st_style, unsafe_allow_html=True)


    # Show dataframes - original and filtered

    st.dataframe(df)
    st.dataframe(df_selection)


    ################ TO ADD:

    # Benchmark Metrics with total customers
    # Benchmark with specific population

