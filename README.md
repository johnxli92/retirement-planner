# Retirement Planner Web App

This is a web app for planning retirement using a safe withdrawal rate (SWR) approach.

It lets you:
- Enter your age, target retirement age, and plan until age
- Enter current 401k and brokerage balances, plus optional annual contributions and expected real returns
- Choose an SWR percentage (withdrawal recalculated each year based on current portfolio balance)
- See projected balances and retirement income (pre- and post-tax) through your chosen end age
- View graphs showing portfolio balances over time

## Running locally

1. Create and activate a virtual environment (optional but recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the app:
```bash
streamlit run retirement_planner/app.py
```

The app will open in your browser at `http://localhost:8501`

## Deploying to the Internet

### Streamlit Cloud (Recommended - Free)

1. Push your code to GitHub (create a new repository if needed)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app"
5. Select your repository and branch
6. Set main file path: `retirement_planner/app.py`
7. Click "Deploy"

Your app will be live at a URL like: `https://your-app-name.streamlit.app`

### Alternative Options

- **Railway**: Connect GitHub repo, auto-detects Streamlit
- **Render**: Free tier available, requires setting start command
- **Heroku**: Paid options only

## Features

- **Tax Modeling**: US-style federal tax brackets with state tax support
- **Dual Account Tracking**: Separate 401k (tax-deferred) and brokerage (taxable) account tracking
- **Flexible Withdrawal Strategy**: Choose to withdraw from brokerage first or 401k first
- **Dynamic Withdrawals**: Withdrawal amount recalculates each year as a percentage of current portfolio balance
- **Visualizations**: Charts showing portfolio balances and income over time


