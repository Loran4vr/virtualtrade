# VirtualTrade - Paper Trading Platform for Indian Markets

VirtualTrade is a virtual paper trading application for Indian equity stocks, futures, and options. It allows users to practice trading without risking real money, using virtual funds.

## Features

- **Google Sign-in Authentication**: Simple login with Google account (no phone verification required)
- **Market Data**: Access to Indian equity stocks, futures, and options data
- **Paper Trading**: Buy and sell stocks with virtual money
- **Portfolio Management**: Track your holdings and performance
- **Transaction History**: View your trading history
- **Responsive Design**: Works on both desktop and mobile devices

## Tech Stack

- **Frontend**: React, Tailwind CSS
- **Backend**: Flask (Python)
- **Authentication**: Google OAuth 2.0
- **Market Data**: Alpha Vantage API

## Deployment

The application is deployed at: https://rkkh7ikc5nlp.manus.space

## Local Development

### Prerequisites

- Node.js and npm/pnpm
- Python 3.11+
- Google OAuth credentials

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with the following variables:
   ```
   SECRET_KEY=your-secret-key
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key
   ```

5. Run the backend server:
   ```
   python main.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   pnpm install
   ```

3. Run the development server:
   ```
   pnpm run dev
   ```

4. Build for production:
   ```
   pnpm run build
   ```

## Usage

1. Sign in with your Google account
2. Explore the market data and search for stocks
3. Buy and sell stocks with your virtual funds
4. Track your portfolio performance
5. View your transaction history

## Notes

- This is a paper trading platform, no real money is involved
- Market data may be delayed depending on the API tier
- For educational purposes only, not financial advice

