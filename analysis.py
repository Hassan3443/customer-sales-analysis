import pandas as pd
import matplotlib.pyplot as plt
import mysql.connector
import warnings
from matplotlib.ticker import FuncFormatter

# Hide warnings
warnings.filterwarnings("ignore")

# ---------------------------------------
# Connect to MySQL
# ---------------------------------------

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="60102006",
    database="ecommerce"
)

# ---------------------------------------
# Helper function for formatting numbers
# ---------------------------------------

def format_millions(x, pos):
    return f'{x/1e6:.1f}M'

# ---------------------------------------
# Query 1: Top Categories
# ---------------------------------------

query1 = """
SELECT Category, SUM(TotalAmount) AS revenue
FROM amazon
GROUP BY Category
ORDER BY revenue DESC
LIMIT 10;
"""

top_categories = pd.read_sql(query1, conn)

# Sort for better visualization
top_categories = top_categories.sort_values(by='revenue', ascending=True)

# Plot
plt.figure(figsize=(10,6))
plt.barh(top_categories['Category'], top_categories['revenue'], color='#4CAF50')

plt.title("Top Categories by Revenue", fontsize=14, weight='bold')
plt.xlabel("Revenue")

plt.gca().xaxis.set_major_formatter(FuncFormatter(format_millions))

# Add labels on bars
for i, v in enumerate(top_categories['revenue']):
    plt.text(v, i, f"{v/1e6:.1f}M", va='center')

plt.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig("top_categories.png")
plt.show()

# ---------------------------------------
# Query 2: Monthly Revenue
# ---------------------------------------

query2 = """
SELECT DATE_FORMAT(OrderDate, '%Y-%m') AS month,
       SUM(TotalAmount) AS revenue
FROM amazon
GROUP BY month
ORDER BY month;
"""

monthly_sales = pd.read_sql(query2, conn)

# Convert to datetime & sort
monthly_sales['month'] = pd.to_datetime(monthly_sales['month'])
monthly_sales = monthly_sales.sort_values('month')

# Plot
plt.figure(figsize=(10,6))
plt.plot(monthly_sales['month'], monthly_sales['revenue'], marker='o', color='#2196F3')

plt.title("Monthly Revenue Trend", fontsize=14, weight='bold')
plt.xlabel("Month")
plt.ylabel("Revenue")

plt.gca().yaxis.set_major_formatter(FuncFormatter(format_millions))

plt.xticks(rotation=45)
plt.grid(alpha=0.3)

plt.tight_layout()
plt.savefig("monthly_sales.png")
plt.show()

# ---------------------------------------
# Query 3: Top States
# ---------------------------------------

query3 = """
SELECT State, SUM(TotalAmount) AS revenue
FROM amazon
GROUP BY State
ORDER BY revenue DESC
LIMIT 10;
"""

top_states = pd.read_sql(query3, conn)

# Sort for better visualization
top_states = top_states.sort_values(by='revenue', ascending=True)

# Plot
plt.figure(figsize=(10,6))
plt.barh(top_states['State'], top_states['revenue'], color='#FF9800')

plt.title("Top States by Revenue", fontsize=14, weight='bold')
plt.xlabel("Revenue")

plt.gca().xaxis.set_major_formatter(FuncFormatter(format_millions))

# Add labels
for i, v in enumerate(top_states['revenue']):
    plt.text(v, i, f"{v/1e6:.1f}M", va='center')

plt.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig("top_states.png")
plt.show()

# ---------------------------------------
# Close connection
# ---------------------------------------

conn.close()

print("Charts generated and saved successfully!")