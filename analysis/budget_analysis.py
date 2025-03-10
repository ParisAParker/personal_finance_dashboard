# Analyze monthly spending vs budget

def get_actual_payday(year, month):
    """
    Determines the actual payday for a given month.
    - If the 26th is a weekend/holiday, shifts payday to the previous business day.
    
    Returns: Adjusted payday as a datetime object.
    """
    payday = pd.Timestamp(year, month, 26)
    
    # If payday falls on a weekend, shift to the previous business day
    if payday.weekday() >= 5:  # 5=Saturday, 6=Sunday
        payday -= BDay(1)  # Move to the previous business day

    return payday

def assign_pay_period(df, date_column="Date"):
    """
    Assigns transactions to the correct pay period based on the adjusted payday.
    """
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])  # Ensure datetime format

    # Determine pay periods
    df["PayPeriod"] = df[date_column].apply(
    lambda x: get_actual_payday(x.year - 1, 12).strftime('%Y-%m')
    if x.month == 1 else get_actual_payday(x.year, x.month - 1).strftime('%Y-%m')
    )

    return df

def transaction_pay_period(df):
    # Get the min and max date of the transactions dataframe
    min_date = df['Date'].min() - pd.offsets.MonthEnd(1)
    max_date = df['Date'].max() + pd.offsets.MonthEnd(1)

    # Get the monthly date range between min and max date
    date_range = pd.date_range(
        start = min_date,
        end = max_date,
        freq = 'ME'
    )

    # Initialize column to store pay period month
    df['Pay_Period'] = None

    # Get the pay period ranges for each month
    for x in date_range:
      
        current_paydate = get_actual_payday(x.year, x.month)
        if x.month == 12:
            next_paydate = get_actual_payday(x.year + 1, 1)
        else:
            next_paydate = get_actual_payday(x.year, x.month + 1)

        pay_period_range = pd.date_range(
            start = current_paydate,
            end = next_paydate,
            freq = 'D',
            inclusive = 'left'
        )

        # If the transaction falls within the pay period's date range, mark it as the correct month's pay period
        df['Pay_Period'] = df.apply(
            lambda x: (current_paydate + pd.DateOffset(months=1)).strftime('%B %Y') if x['Date'] in pay_period_range
            else x['Pay_Period'],
            axis=1
        )
        
    return df

def classify_income_expense(df, amount_column = 'Amount'):
    df['Transaction_Type'] = df[amount_column].apply(
        lambda x: 'Income' if x >= 0
        else 'Expense'
    )
    return df

def get_current_pay_period(df):   
    # Identify the current pay period
    current_pay_period = df[df['Pay_Period'] == 'March 2025']
    current_pay_period = current_pay_period[~((current_pay_period['Transaction_Type'] == 'Income') & (current_pay_period['Bank'] == 'AMEX'))]

    # Build helper columns for identifying refund transactions
    current_pay_period['abs_amount'] = current_pay_period['Amount'].abs()
    current_pay_period['is_refund_pair'] = False

    # Group transactions by absolute amount and check for charge-refund pairs
    matched_indices = set()
    for amount, group in current_pay_period.groupby('abs_amount'):
        charges = group[group['Amount'] < 0]
        refunds = group[group['Amount'] > 0]
        
        # Create empty list for storing paired indexes
        refund_exclude_list = []

        # Pair each charge with a refund within a close date range
        for charge_idx, charge_row in charges.iterrows():
            for refund_idx, refund_row in refunds.iterrows():
                if (abs((charge_row['Date'] - refund_row['Date']).days) <= 3) and refund_idx not in refund_exclude_list:  # Allow a 3-day window
                    current_pay_period.at[charge_idx, 'is_refund_pair'] = True
                    current_pay_period.at[refund_idx, 'is_refund_pair'] = True
                    refund_exclude_list.append(refund_idx)
                    break  # Move to next charge

    # Mark refund pairs as Ignored Transaction Type
    current_pay_period['Transaction_Type'] = current_pay_period.apply(
        lambda row: 'Ignored' if row['is_refund_pair'] == True
        else row['Transaction_Type'],
        axis=1
    )

    # Get the current pay period income
    current_pay_period_income = current_pay_period.groupby('Transaction_Type')['Amount'].sum()['Income']
    current_pay_period_expenses = current_pay_period.groupby('Transaction_Type')['Amount'].sum()['Expense']

    return current_pay_period, current_pay_period_income, current_pay_period_expenses

