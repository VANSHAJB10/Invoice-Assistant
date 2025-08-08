import streamlit as st
from main import generate_invoice  # Import the single entry point
from data.services import service_list

service_list = service_list  
def main():
    st.title("Invoice Assistant")

    # Input fields
    client_name = st.text_input("Client Name")
    bank_name = st.text_input("Bank Name")
    account_number = st.text_input("Account Number")
    ifsc_code = st.text_input("IFSC Code")

    # Service list input
    st.subheader("Services")
    use_default_services = st.checkbox("Use Default Service List", value=True)

    if use_default_services:
          
        selected_services = {}
        for service, price in service_list.items():
            selected = st.checkbox(service, value=False, key=f"default_{service}")  # Unique key
            if selected:
                selected_services[service] = price
    else:
        num_services = st.number_input("Number of Services", min_value=1, max_value=10, value=3, step=1)
        selected_services = {}
        for i in range(num_services):
            col1, col2 = st.columns(2)
            with col1:
                service_name = st.text_input(f"Service {i+1} Name", key=f"custom_name_{i}")  # Unique key
            with col2:
                service_price = st.number_input(f"Service {i+1} Price", min_value=0.0, value=100.0, key=f"custom_price_{i}")  # Unique key
            if service_name:  # Only add if a name is provided
                selected_services[service_name] = service_price

    if st.button("Generate Invoice"):
        # Call the single entry point in main.py
        results = generate_invoice(
            client_name=client_name,
            bank_name=bank_name,
            account_number=account_number,
            ifsc_code=ifsc_code,
            selected_services=selected_services
        )

        # Display results
        st.subheader("Invoice")
        st.markdown(results["invoice_text"])

        st.subheader("LLM Analysis")
        st.write(f"Client Classification: {results['classification']}")
        st.write(f"Profitability: {results['profitability']}")
        st.write(f"Summary: {results['summary']}")

if __name__ == "__main__":
    main()