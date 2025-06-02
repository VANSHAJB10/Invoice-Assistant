import os
from typing import List, TypedDict
from colorama import Fore
from dotenv import load_dotenv

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langgraph.graph import StateGraph, END

import secrets
from datetime import date
from datetime import timedelta

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
OPENAI_API_KEY = secrets.OPENAI_API_KEY

def create_invoice_markdown(file_path: str):
    today = date.today().isoformat()
    number_of_weeks = 2  # Example value, can be adjusted or passed as an argument
    weekly_due_date = (date.today() + timedelta(days=number_of_weeks * 7)).isoformat()

    invoice_text = f"""
    # Invoice

    **Client: BossLabs**
    **Date: {today}**
    **Due Date: {weekly_due_date}**
    **Address:** HSR Layout, Bangalore, India
    **Payment Terms:** Net30

    ## Services Provided
    - **Service 1:** Cost of service 1
    - **Service 2:** Cost of service 2
    - **Service 3:** Cost of service 3
    - **Service 4:** Cost of service 4

    **Note:**
    Please make the payment by the due date. 
    If you have any questions regarding this invoice, please contact us at hello@bosslabs.com

    **Bank Details**
    Bank Name: Example Bank
    Account Number: 123456789
    IFSC Code: EXAMPLE123

    **Contact Information**
    Phone: +91 12345 67890
    Email: hello@bosslabs.in

    **Thank you for your choosing BossLabs!**
    ** Copyright © {today[:4]} BossLabs. All rights reserved.**
    """

    with open(file_path, 'w') as file:
        file.write(invoice_text)
    print(Fore.GREEN + f"Invoice created successfully at {file_path}" + Fore.RESET)

# passing data as text to the state graph

# Read invoice markdown
def read_invoice_template(file_path: str) -> str:
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

#Initialize the OpenAI model
llm = ChatOpenAI(model="gpt-4", temperature=0)
# no creative liberty to the model.

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
        Text: {text}. Return the total amount as  only a number with currency symbols of INR (₹).
        """
    )

    message = HumanMessage(content=prompt.format(text=state["text"]))
    total_amount = llm.invoke([message]).content.strip().split(", ")
    state["total_amount_due"] = float(total_amount[0].replace(",", ""))
    return state

# Extract profitability status
def node_extract_profitability_status(state: State):
    total_amount_due = state["total_amount_due"]
    cost_of_services = state["cost_of_services"]
    profit = total_amount_due - cost_of_services
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
        Profitability Status: {profitability}
        
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

graph = workflow.compile()