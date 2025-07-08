import pandas as pd
import numpy as np
import numpy_financial as npf
import streamlit as st
import plotly.express as px
import json
import os

st.set_page_config(page_title="Simple Finance App", page_icon="💰", layout="wide")

category_file = "categories.json"

if "categories" not in st.session_state:
    st.session_state.categories = {
        "Uncategorized": [],
    }

if os.path.exists(category_file):
    with open(category_file,"r") as f:
        st.session_state.categories = json.load(f)

def save_categories():
    with open(category_file,"w") as f:
        json.dump(st.session_state.categories, f)

def categorize_transcations(df):
    df["Category"] = "Uncategorized"

    for category, keywords in st.session_state.categories.items():
        if category == "Uncategorized" or not keywords:
            continue

        lowwered_keywords = [keyword.lower().strip() for keyword in keywords]
        for idx, row in df.iterrows():
            details = row["Details"].lower().strip()
            if details in lowwered_keywords:
                df.at[idx, "Category"] = category
    
    return df

def load_transactions(file):
    try:
        df = pd.read_csv(file, skipinitialspace=True)

        df.columns = [col.strip() for col in df.columns]
        # df.columns = df.columns.str.strip()
        df["Amount"] = df["Amount"].str.replace(",","").astype(float)
        # df['Amount'] = df['Amount'].replace(',', '', regex=True)
        # df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y", dayfirst=True, errors='coerce')

        return categorize_transcations(df)
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None
        
def add_keyword_to_category(category, keyword):
    keyword = keyword.strip()
    if keyword and keyword not in st.session_state.categories[category]:
        st.session_state.categories[category].append(keyword)
        save_categories()
        return True
    
    return False

def main():
    st.title("Simple Finance App")
    
    # Load data
    data_file = st.file_uploader("Upload your Statements .CSV file", type=["csv"])

    if data_file is not None:
        df = load_transactions(data_file)

        if df is not None:
            st.session_state.main_df = df.copy()
            debits_df = st.session_state.main_df[df["Debit/Credit"] == "Debit"].copy()
            credits_df = st.session_state.main_df[df["Debit/Credit"] == "Credit"].copy()

            tab1, tab2, tab3 = st.tabs(["Expenses (Debits)", "Payments (Credits)", "Loan calculator"])

            with tab1:
                new_category = st.text_input("New category Name")
                add_button = st.button("Add Category")

                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        # st.success(f"Added a new category: {new_category}")
                        st.rerun()

                st.subheader("Your Expences")
                save_button = st.button("Apply changes", type="primary")

                edited_df = st.data_editor(
                    debits_df[["Date", "Details", "Amount", "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                        "Amount": st.column_config.NumberColumn("Amount", format="%.2f ZAR"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="category_editor"
                )

                # save_button = st.button("Apply changes", type="primary")
                if save_button:
                    for idx, row in edited_df.iterrows():
                        new_category = row["Category"]
                        if new_category == debits_df.at[idx, "Category"]:
                            continue
                        
                        details = row["Details"]
                        debits_df.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, details)
                        st.rerun()

                st.subheader("Expence Summary")
                category_totals = debits_df.groupby("Category")["Amount"].sum().reset_index()
                category_totals = category_totals.sort_values("Amount", ascending=False)

                st.dataframe(
                    category_totals,
                    column_config={
                        "Amount": st.column_config.NumberColumn("Amount", format="%.2f ZAR")
                    },
                    hide_index=True,
                    use_container_width=True
                )

                fig = px.pie(
                    category_totals,
                    values = "Amount",
                    names = "Category",
                    title = "Expenses by Category"
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                new_category = st.text_input("New category")
                add_button = st.button("Add to Category")

                if add_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        # st.success(f"Added a new category: {new_category}")
                        st.rerun()

                st.subheader("Your Income")
                save_button = st.button("Apply", type="primary")

                re_Credits_df = st.data_editor(
                    credits_df[["Date", "Details", "Amount", "Category"]],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                        "Amount": st.column_config.NumberColumn("Amount", format="%.2f ZAR"),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=list(st.session_state.categories.keys())
                        )
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="Credits_df"
                )

                if save_button:
                    for idx, row in re_Credits_df.iterrows():
                        new_category = row["Category"]
                        if new_category == credits_df.at[idx, "Category"]:
                            continue
                        
                        details = row["Details"]
                        credits_df.at[idx, "Category"] = new_category
                        add_keyword_to_category(new_category, details)
                        st.rerun()
                
                st.subheader("Income Summary")
                category_totals = credits_df.groupby("Category")["Amount"].sum().reset_index()
                category_totals = category_totals.sort_values("Amount", ascending=False)

                st.dataframe(
                    category_totals,
                    column_config={
                        "Amount": st.column_config.NumberColumn("Amount", format="%.2f ZAR")
                    },
                    hide_index=True,
                    use_container_width=True
                )

                fig = px.pie(
                    category_totals,
                    values = "Amount",
                    names = "Category",
                    title = "Income by Category"
                )
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("Budget Calculator")
                st.text("The first step toward buying an asset is finding out how much you can spend. To do that, enter your monthly income after taxes in the worksheet below and subtract your monthly expenses. Add additional expenses, if necessary. The remaining balance is an estimate of what you can possibly put toward your monthly finance payment.")
                
                total_payments = credits_df["Amount"].sum()
                st.metric("Total Income", f"{total_payments:,.2f} ZAR")

                total_expence = debits_df["Amount"].sum()
                st.metric("Monthly Expenses:", f"{total_expence:,.2f} ZAR")

                Surplus = total_payments-total_expence
                st.metric("Remaining surplus balance:", f"{Surplus:,.2f} ZAR")

                Max_Payment = Surplus * 0.7
                st.metric("Max payment:", f"{Max_Payment:,.2f} ZAR")

                Possible_asset_Price = Max_Payment*60
                st.metric("Possible cash price of an asset:", f"{Possible_asset_Price:,.2f} ZAR")

            with tab3:
                Obj_Cash_Value = st.text_input("Cash Value of Object")
                Loan_Term = st.text_input("Loan Term (Anual)")
                Interest_Rate = st.text_input("Interest Rate (Anual as Decimal)")
                Start_Date = st.date_input("Start date (Optional)")
                Deposit = st.text_input("Deposit (Optional [Value])")
                Baloon = st.text_input("Baloon (Optional [Value])")

                Calculate_btn = st.button("Calculate")

                if Calculate_btn and Obj_Cash_Value and Loan_Term and Interest_Rate:
                    temp = float(Obj_Cash_Value)    
                    if Deposit:
                        temp = temp - float(Deposit)
                    if Baloon:
                        temp = temp - float(Baloon)

                    # Calculate the monthly payment
                    monthly_payment = npf.pmt(float(Interest_Rate)/12, float(Loan_Term)*12, -temp) # loan_amount is negative as it's a cash outflow initially
                    st.metric("Monthly Re-payments:", f"{monthly_payment:,.2f} ZAR")

                    payments_DF = pd.DataFrame({
                        'Payment Nr.': [0],
                        'Date of Payments': [None],
                        'PMT': [None],
                        'Interest Payed': [None],
                        'Principal Reduction': [None],
                        'Ending balance': [temp]
                    })

                    Ending_Balance = temp
                    for i in range((int(Loan_Term)*12)):
                        interest_Payed = Ending_Balance*(float(Interest_Rate)/12)
                        Princaple_Reduction = monthly_payment - interest_Payed
                        Ending_Balance = Ending_Balance - Princaple_Reduction
                        if Start_Date.month + 1 <= 12:
                            Start_Date = Start_Date.replace(month=Start_Date.month + 1)
                        elif Start_Date.month + 1 > 12:
                            Start_Date = Start_Date.replace(year=Start_Date.year + 1, month=(Start_Date.month + 1) % 12)


                        appending_Row = pd.DataFrame({
                        'Payment Nr.': [i+1],
                        'Date of Payments': [Start_Date.strftime("%Y/%m")],
                        'PMT': [f"R {monthly_payment:.2f}"],
                        'Interest Payed': [f"R {interest_Payed:.2f}"],
                        'Principal Reduction': [f"R {Princaple_Reduction:.2f}"],
                        'Ending balance': [f"R {Ending_Balance:.2f}"]
                        })
                        
                        payments_DF = pd.concat([payments_DF, appending_Row], ignore_index=True)


                    st.dataframe(payments_DF, hide_index=True)
                

main()
            