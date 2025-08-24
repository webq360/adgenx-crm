from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
import requests
from dotenv import load_dotenv
import os

# Load variables from .env
load_dotenv()


def change_spend_cap(amount, ad_account_id):

    # --- 1. DEFINE YOUR CREDENTIALS AND IDs ---
    MY_APP_ID = os.getenv('MY_APP_ID')
    MY_APP_SECRET = os.getenv('MY_APP_SECRET')
    MY_ACCESS_TOKEN = os.getenv('MY_ACCESS_TOKEN')
    AD_ACCOUNT_ID = 'act_{}'.format(ad_account_id)

    # --- 2. INITIALIZE THE API ---
    FacebookAdsApi.init(
        MY_APP_ID,
        MY_APP_SECRET,
        MY_ACCESS_TOKEN
    )

    # --- 3. GET THE AD ACCOUNT OBJECT ---
    ad_account = AdAccount(AD_ACCOUNT_ID)

    # --- 4. UPDATE THE SPEND CAP ---
    try:
        response = ad_account.api_update(
            params={
                AdAccount.Field.spend_cap: amount
            }
        )

        print('Spend cap updated successfully:', response)
        return True

    except Exception as e:
        print('Error updating spend cap:', e)
        return False

def get_ad_account_info(ad_account_id):
    MY_ACCESS_TOKEN = os.getenv('MY_ACCESS_TOKEN')
    AD_ACCOUNT_ID = 'act_{}'.format(ad_account_id) 

    url = f"https://graph.facebook.com/v23.0/{AD_ACCOUNT_ID}"
    params = {
        "fields": "amount_spent,balance",
        "access_token": MY_ACCESS_TOKEN
    }

    response = requests.get(url, params=params)
    print(response.json())

get_ad_account_info('1490547679044213')