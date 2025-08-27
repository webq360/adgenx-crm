import os
from dotenv import load_dotenv
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adaccount import AdAccount as AdAccountObject


# Get the path to the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the .env file in the parent directory
env_path = os.path.join(script_dir, '..', '.env')

# Load the .env file from the specified path
load_dotenv(dotenv_path=env_path)


def change_spend_cap(amount, ad_account_id, admin_bm_id):
    """
    Changes the spend cap for a given ad account.
    """
    try:
        # Get credentials using the admin_bm_id to format the variable names
        MY_APP_ID = os.getenv(f'MY_APP_ID{admin_bm_id}')
        MY_APP_SECRET = os.getenv(f'MY_APP_SECRET{admin_bm_id}')
        MY_ACCESS_TOKEN = os.getenv(f'MY_ACCESS_TOKEN{admin_bm_id}')
        
        # Initialize the API for this specific request
        FacebookAdsApi.init(MY_APP_ID, MY_APP_SECRET, MY_ACCESS_TOKEN)

        ad_account = AdAccount('act_{}'.format(ad_account_id))
        response = ad_account.api_update(
            params={
                AdAccount.Field.spend_cap: amount
            }
        )
        return True
    except Exception as e:
        print('❌ Error updating spend cap:', e)
        return False


def get_ad_account_info(ad_account_id, admin_bm_id):
    """
    Fetches ad account information using the SDK.
    """
    try:
        # Get credentials using the admin_bm_id
        MY_APP_ID = os.getenv(f'MY_APP_ID{admin_bm_id}')
        MY_APP_SECRET = os.getenv(f'MY_APP_SECRET{admin_bm_id}')
        MY_ACCESS_TOKEN = os.getenv(f'MY_ACCESS_TOKEN{admin_bm_id}')
        
        # Initialize the API for this specific request
        FacebookAdsApi.init(MY_APP_ID, MY_APP_SECRET, MY_ACCESS_TOKEN)
        
        ad_account = AdAccountObject('act_{}'.format(ad_account_id))
        fields_to_get = [
            'amount_spent',
            'spend_cap'
        ]
        info = ad_account.api_get(fields=fields_to_get)
        
        # Convert currency fields from cents to dollars
        for field in ['spend_cap', 'amount_spent']:
            if field in info:
                try:
                    info[field] = float(info[field]) / 100
                except (ValueError, TypeError):
                    info[field] = 0
        info.balance = info.get('spend_cap') - info.get('amount_spent')

        return info
    except Exception as e:
        print('❌ Error getting ad account info:', e)
        return None