import os
from typing import List, TypedDict
from colorama import Fore
from dotenv import load_dotenv

from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from langgraph.graph import StateGraph, END
# from langchain_openai import ChatOpenAI

# ***\/\/\/\/\/*** UNCOMMENT FOR TESTING  ***\/\/\/\/\/*** #
#from secrets import GEMINI_API_KEY

from datetime import date
from datetime import timedelta
import google.generativeai as genai

load_dotenv()

######################## OPEN AI KEY Code Block ###############################
#os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# OPENAI_API_KEY = OPENAI_API_KEY
######################## OPEN AI KEY Code Block End ###########################

#### ***\/\/\/\/\/*** UNCOMMENT FOR PUSHING to PROD ***\/\/\/\/\/*** #
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

print("🚩DEBUG: Response from Gemini API:")

class GeminiLLM:
    def __init__(self, model="gemini-2.0-flash", temperature=0):
        self.model = model
        self.temperature = temperature

    def invoke(self, messages):
        prompt = messages[0].content if messages else ""
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(
            prompt,
            generation_config={"temperature": self.temperature}
        )
        return type("Obj", (object,), {"content": response.text})

llm = GeminiLLM(model="gemini-2.0-flash", temperature=0)

def get_user_selected_services(services: dict) -> dict:
    print("Available services:")
    for idx, (service, price) in enumerate(services.items(), 1):
        print(f"{idx}. {service} - ₹{price:.2f}")
    selected_indices = input("Enter the 'numbers' of the services to include (comma-separated, e.g., 1,3): ")
    selected_indices = [int(i.strip()) for i in selected_indices.split(",") if i.strip().isdigit()]
    selected_services = {list(services.keys())[i-1]: list(services.values())[i-1] for i in selected_indices if 0 < i <= len(services)}
    return selected_services

# Payment terms based on client classification
def get_payment_terms(classification: str) -> str:

    ################################### Payment Terms based on classification ###################################
    terms = {
        "Low Budget": [
            "1. Advance payment of 60% of total amount.",
            "2. UPI, Bank transfer accepted.",
            "3. Balance amount to be paid after the final demo and before the final delivery."
        ],
        "Mid-Range": [
            "1. Advance payment of 45% of total amount.",
            "2. UPI, Bank transfer accepted.",
            "3. Balance amount to be paid after the final demo and before the final delivery."
        ],
        "Premium": [
            "1. Advance payment of 30% of total amount.",
            "2. UPI, Bank transfer accepted.",
            "3. Balance amount to be paid after the final demo and before the final delivery."
        ]
    }
    return "\n".join(terms.get(classification, []))

def create_invoice_markdown(file_path: str):
    today = date.today().isoformat()
    number_of_weeks = 2  # Example value, can be adjusted or passed as an argument
    weekly_due_date = (date.today() + timedelta(days=number_of_weeks * 7)).isoformat()

    ################### Available services and their prices ###################
    services = {
        "Ad Creatives": 100.00,
        "SEO Optimization Consultation": 1500.00,
        "Graphics": 800.00,
        "Development": 12000.00

        # Add more services as needed in format - "Service Name": price
    }

    selected_services = get_user_selected_services(services)
    total_amount = sum(selected_services.values())

    ########################### Classify client based on total amount ###########################
    if total_amount <= 15000:
        classification = "Low Budget"
    elif 15001 <= total_amount <= 45000:
        classification = "Mid-Range"
    else:
        classification = "Premium"
    payment_terms_md = get_payment_terms(classification)

    ############################ Inputs for Invocie Markdown ###########################
    client_name = input("Enter the client's name: ").strip() or "Client Name"
    services_md = "\n".join([f"- **{name}:** {price:.2f}" for name, price in selected_services.items()])

    ##################################### Bank details #####################################
    print("Please enter your bank details for payment OR Press ENTER to use default values.")
    bank_name = input("Enter Bank Name OR Press ENTER for default: ").strip() or "Example Bank"
    account_number = input("Enter Account Number OR Press ENTER for default: ").strip() or "123456789"
    ifsc_code = input("Enter IFSC Code OR Press ENTER for default: ").strip() or "EXAMPLE123"
    
    bank_details = {
        "Bank Name": bank_name,
        "Account Number": account_number,
        "IFSC Code": ifsc_code
    }
    bank_details_md = "\n".join([f"- **{key}:** {value}" for key, value in bank_details.items()])

    ###################### Create the invoice markdown text ######################
    invoice_text = f"""
    # Invoice

    **Client: {client_name}**
    **Date: {today}**
    **Due Date: {weekly_due_date}**
    **Address:** HSR Layout, Bangalore, India

    ## Services Provided
    {services_md}

    ## Payment Terms
    {payment_terms_md}

    **Note:**
    Please make the payment by the due date. 
    If you have any questions regarding this invoice, please contact us at hello@bosslabs.com

    **Bank Details**
    {bank_details_md}

    **Contact Information**
    Phone: +91 12345 67890
    Email: hello@bosslabs.in

    **Thank you for your choosing BossLabs!**
    ** Copyright © {today[:4]} BossLabs. All rights reserved.**
    """

    with open(file_path, 'w') as file:
        file.write(invoice_text)
    print(Fore.GREEN + f"Invoice created successfully at {file_path}" + Fore.RESET)

################################## passing data as text to the state graph ##################################

# Read invoice markdown
def read_invoice_markdown(file_path: str) -> str:
    with open(file_path, 'r') as file:
        return file.read()
    
# Define the state graph schema
## the way the State object is defined, defines the way you keep track of the state as agent executes further steps

class State(TypedDict):
    text: str #test of invoice
    classification: str #classification of client
    entities: List[str] #payment terms , services
    cost_of_services: float #cost of services
    total_amount_due: float #total amount to be paid
    profitability: str #status of profitability of the invoice for the business
    summary: str 

# Classify the client based on the invoice total amount
## helps business if they want to prioritise clients based on the total amount of invoice
def node_classify_client(state: State):
    prompt = PromptTemplate(
        input_variables=["text"],
        template="""
        Classify the client tier based on invoice amount into one of the following categories: Low Budget, Mid-Range, Premium.
        - Low Budget: Invoice amount between 0 to 15,000
        - Mid-Range: Invoice amount between 15,001 to 45,000
        - Premium: Invoice amount above 45,000
        
        Invoice Info: {text}
        
        Category:
        """
    )

    message = HumanMessage(content=prompt.format(text=state["text"]))
    classification = llm.invoke([message]).content.strip()
    state["classification"] = classification
    return state

# Extract total due amount
def node_extract_invoice_amount(state: State):
    prompt = PromptTemplate(
        input_variables=["text"],
        template="""
        Extract the total due amount from the invoice text.\n
        Text: {text}. Return the total amount as only a number with nothing else other than numbers.
        """
    )

    message = HumanMessage(content=prompt.format(text=state["text"]))
    total_amount = llm.invoke([message]).content.strip().split(", ")

    # Convert to float, then add INR symbol in front of the float value and add to state
    amount_float = float(total_amount[0].replace(",", ""))
    state["total_amount_due"] = f"₹{amount_float:.2f}"
    return state

# Extract profitability status
def node_extract_profitability_status(state: State):
    total_amount_due = state["total_amount_due"]
    cost_of_services = state["cost_of_services"]

    # Convert total_amount_due to float (remove currency symbol if present)
    if isinstance(total_amount_due, str):
        total_amount_due_float = float(total_amount_due.replace("₹", "").replace(",", "").strip())
    else:
        total_amount_due_float = float(total_amount_due)

    cost_of_services_float = float(cost_of_services)
    profit = total_amount_due_float - cost_of_services_float
    profitability_status = "Profitable" if profit > 0 else "Loss!"
    state["profitability"] = profitability_status

# Summarize the invoice
def node_summarize_invoice(state: State):
    prompt = PromptTemplate(
        input_variables=["text", "classification", "entities", "cost_of_services", "total_amount_due", "profitability"],
        template="""
        Summarize the invoice details.\n
        Text: {text}\n
        Classification: {classification}\n
        Entities: {entities}\n
        Cost of Services: {cost_of_services}\n
        Total Amount Due: {total_amount_due}\n
        Profitability Status: {profitability}\n
        
        Provide a concise summary of the invoice.
        """
    )

    message = HumanMessage(content=prompt.format(
        text=state["text"],
        classification=state["classification"],
        entities=", ".join(state["entities"]),
        cost_of_services=state["cost_of_services"],
        total_amount_due=state["total_amount_due"],
        profitability=state["profitability"]
    ))
    
    state["summary"] = llm.invoke([message]).content.strip()
    return state

# Create a graph 
workflow = StateGraph(State)

workflow.add_node("classify_client", node_classify_client)
workflow.add_node("extract_invoice_amount", node_extract_invoice_amount)
workflow.add_node("extract_profitability_status", node_extract_profitability_status)
workflow.add_node("summarize", node_summarize_invoice)

# Add edges to graph
workflow.set_entry_point("classify_client")
workflow.add_edge("classify_client", "extract_invoice_amount")
workflow.add_edge("extract_invoice_amount", "extract_profitability_status")
workflow.add_edge("extract_profitability_status", "summarize")
workflow.add_edge("summarize", END)

# Compile the graph
graph = workflow.compile()

# Draw Graph
try: 
    graph.get_graph(xray=True).draw_mermaid_png(output_file_path="graph.png")
except Exception:
    pass

# Process the invoice
def process_invoice(invoice_text: str, cost_of_services: float):
    state = State(
        text=invoice_text, classification="", 
        entities=[], 
        summary="", 
        cost_of_services = cost_of_services,
        total_amount_due=0.0,
        profitability=""
        )
    result = graph.invoke(state)
    return result

if __name__ == "__main__":
    invoice_file_path = "./data/invoice.md"
    create_invoice_markdown(invoice_file_path)
    invoice_text = read_invoice_markdown(invoice_file_path)
    cost_of_services = 800 #temporary value
    result = process_invoice(invoice_text, cost_of_services)

    print(Fore.WHITE, "Invoice Text:", invoice_text, "\n")
    print(Fore.YELLOW, "Client Classification:", result["classification"], "\n")
    print(Fore.GREEN, "Total Amount Due:", result["total_amount_due"], "\n")
    print(Fore.LIGHTCYAN_EX , "Cost of Services:", cost_of_services, "\n")
    print(Fore.BLUE, "Profitability:", result["profitability"], "\n")
    print(Fore.MAGENTA, "Summary:", result["summary"], "\n")