# backend/subscription/__init__.py

import stripe
import os

SUBSCRIPTION_PLANS = {
    'basic': {
        'name': 'Basic',
        'price': 100,
        'credit': 100000,  # 1 lakh
        'duration_days': 30
    },
    'standard': {
        'name': 'Standard',
        'price': 250,
        'credit': 250000,  # 2.5 lakhs
        'duration_days': 30
    },
    'premium': {
        'name': 'Premium',
        'price': 475,
        'credit': 500000,  # 5 lakhs
        'duration_days': 30
    },
    'ultimate': {
        'name': 'Ultimate',
        'price': 925,
        'credit': 1000000,  # 10 lakhs
        'duration_days': 30
    }
}

def init_stripe(app):
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    # Additional Stripe configuration can go here 