# Main FastAPI/Flask application
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from plaid.api.plaid_api import PlaidApi
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
import datetime

# Load environment variables
load_dotenv()

# Call API credentials
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")

# Initialize FastAPI app
app = FastAPI()

# Allow Streamlit to communicated with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize Plaid client
PLAID_ENV = "sandbox"
host_url = "https://sandbox.plaid.com" if PLAID_ENV == "sandbox" else "https://production.plaid.com"

config = Configuration(host=host_url)
client = PlaidApi(ApiClient(config))

# Store access token globally (in real app, store in database)

@app.post("/create_link_token")
def create_link_token():
    """
    Creates a Plaid Link Token for Streamlit frontend.
    """
    try:
        request = LinkTokenCreateRequest(
            client_id = PLAID_CLIENT_ID,
            secret= PLAID_SECRET,
            products=[Products("transactions")],
            client_name="My Financial Dashboard",
            country_codes=[CountryCode("US")],
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id="paris")
        )

        response = client.link_token_create(request)
        return {"link_token": response["link_token"]}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

access_token = None
item_id = None

@app.post("/exchange_public_token")
def exchange_public_token():
    global access_token
    public_token = request.form['public_token']
    request = ItemPublicTokenExchangeRequest(
        public_token=public_token
    )
    response = client.item_public_token_exchange(request)

    return {"public_token_exchange": response['public_token_exchange']}