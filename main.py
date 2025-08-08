from typing import List, TypedDict
from colorama import Fore
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from langgraph.graph import StateGraph, END
from datetime import date, timedelta
import google.generativeai as genai

#### ***\/\/\/\/\/*** UNCOMMENT FOR TESTING ***\/\/\/\/\/*** #
# from secret_store import GEMINI_API_KEY

load_dotenv()
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

class State(TypedDict):
     #payment terms , services
    cost_of_services: float #cost of services
    total_amount_due: float #total amount to be paid
    profitability: str #status of profitability of the invoice for the business
    summary: str

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
    message = prompt.format(text=state['text'])
    response = llm.invoke([HumanMessage(content=message)])
    return {"classification": response.content}

def node_summarize(state: State):
    prompt = PromptTemplate(
        input_variables=["text"],
        template="""
        Generate a concise summary of the following invoice:
        {text}
        Summary:
        """
    )
    message = prompt.format(text=state['text'])
    response = llm.invoke([HumanMessage(content=message)])
    return {"summary": response.content}

def node_profitability(state: State):
    prompt = PromptTemplate(
        input_variables=["cost", "amount"],
        template="""
        Determine if the invoice is profitable for the business.
        Invoice cost: {cost}
        Invoice amount: {amount}
        Profitability (Profitable/Loss):
        """
    )
    message = prompt.format(cost=state['cost_of_services'], amount=state['total_amount_due'])
    response = llm.invoke([HumanMessage(content=message)])
    return {"profitability": response.content}


def classify_client(total_amount):
    if total_amount <= 15000:
        classification = "Low Budget"
    elif 15001 <= total_amount <= 45000:
        classification = "Mid-Range"
    else:
        classification = "Premium"
    return classification

def get_payment_terms(classification: str) -> str:
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

def create_invoice_markdown(client_name: str, selected_services: dict, bank_details: dict, classification: str):
    today = date.today().isoformat()
    number_of_weeks = 2
    weekly_due_date = (date.today() + timedelta(days=number_of_weeks * 7)).isoformat()
    services_md = "\n".join([f"- **{name}:** ₹{price:.2f}" for name, price in selected_services.items()])
    payment_terms_md = get_payment_terms(classification)
    bank_details_md = "\n".join([f"- **{key}:** {value}" for key, value in bank_details.items()])

    invoice_text = f"""
    # Invoice

    **Client: {client_name}**
    **Date: {today}**
    **Due Date: {weekly_due_date}**

    ## Services Provided
    {services_md}

    ## Payment Terms
    {payment_terms_md}

    **Bank Details**
    {bank_details_md}

    **Contact Information**
    Phone: +91 12345 67890
    Email: hello@bosslabs.in

    **Thank you for your choosing BossLabs!**
    ** Copyright © {today[:4]} BossLabs. All rights reserved.**
    """
    return invoice_text

def process_invoice(invoice_text: str, cost_of_services: float) -> dict:
    total_amount_due = sum([float(line.split(':')[-1].replace('₹', '').strip()) for line in invoice_text.splitlines() if "Total Amount" in line])
    # Define the graph
    builder = StateGraph(State)

    builder.add_node("classify_client", node_classify_client)
    builder.add_node("summarize", node_summarize)
    builder.add_node("profitability", node_profitability)

    builder.set_entry_point("classify_client")

    builder.add_edge("classify_client", "summarize")
    builder.add_edge("summarize", "profitability")
    builder.add_edge("profitability", END)

    graph = builder.compile()

    # Run
    inputs = {"text": invoice_text, "cost_of_services": cost_of_services, "total_amount_due": total_amount_due}
    results = graph.invoke(inputs)

    # Extract
    classification = results['classify_client']['classification']
    summary = results['summarize']['summary']
    profitability = results['profitability']['profitability']

    return {"classification": classification, "summary": summary, "profitability": profitability}

def generate_invoice(client_name: str, bank_name: str, account_number: str, ifsc_code: str, selected_services: dict):
    """
    Generates the invoice and processes it using the LLM.
    """

    # Prepare bank details
    bank_details = {
        "Bank Name": bank_name,
        "Account Number": account_number,
        "IFSC Code": ifsc_code
    }

    # Calculate total amount
    total_amount = sum(selected_services.values())

    # Classify client based on total_amount
    classification = classify_client(total_amount)

    # Generate invoice markdown using your existing function
    invoice_text = create_invoice_markdown(
        client_name=client_name,
        selected_services=selected_services,
        bank_details=bank_details,
        classification=classification
    )

    # Call your existing processing logic
    result = process_invoice(invoice_text, total_amount)

    return {
        "invoice_text": invoice_text,
        "classification": result['classification'],
        "profitability": result['profitability'],
        "summary": result['summary']
    }

