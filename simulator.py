import pandas as pd
import random
import logging
import matplotlib.pyplot as plt
import seaborn as sns
import os  # For handling file paths
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# File paths
file_path = 'data/sample_dataset.csv'  # Replace with your dataset path

# Load dataset
try:
    logging.info("==== PAYROLL FRAUD SIMULATION STARTED ====")
    data = pd.read_csv(file_path, encoding='ISO-8859-1')  # Adjust encoding if necessary
    logging.info(f"Successfully loaded the dataset from {file_path}.")
except FileNotFoundError:
    logging.error(f"File not found: {file_path}")
    raise
except UnicodeDecodeError as e:
    logging.error(f"Encoding error while loading file: {e}")
    raise
except Exception as e:
    logging.error(f"Unexpected error loading file: {e}")
    raise

# Add 'FraudDescription' and 'IsFraudulent' columns if missing
data['FraudDescription'] = 'Valid'
data['IsFraudulent'] = False

# Initialize fraud count dictionary
fraud_counts = {
    "Ghost Employees": 0,
    "Duplicate Records": 0,
    "Excessive Salary Payments": 0,
    "Invalid Account Numbers": 0,
    "Double Salary Payments": 0
}

# Fraud simulation functions
def ghost_employees(data, index):
    global fraud_counts
    fraud_counts["Ghost Employees"] += 1
    random_employee_id = random.randint(1000000, 9999999)
    first_name = random.choice(data['FullName'].str.split().str[0])
    other_name = random.choice(data['FullName'].str.split().str[1:])
    other_name = ' '.join(other_name) if isinstance(other_name, list) else other_name
    new_name = f"{first_name} {other_name}"

    data.at[index, 'FullName'] = new_name
    data.at[index, 'EmployeeID'] = str(random_employee_id)
    data.at[index, 'IsFraudulent'] = True
    data.at[index, 'FraudDescription'] = 'Ghost Employee - Fake employee record created.'

def duplicate_records(data, index, new_rows):
    global fraud_counts
    fraud_counts["Duplicate Records"] += 1
    duplicate = data.iloc[index].copy()
    duplicate['FraudDescription'] = 'Duplicate Employee - Record duplicated under a new ID.'
    duplicate['EmployeeID'] = f"{data.at[index, 'EmployeeID']}-DUP"
    new_rows.append(duplicate)

def excessive_salary_payments(data, index):
    global fraud_counts
    fraud_counts["Excessive Salary Payments"] += 1
    data.at[index, 'GrossSalary'] *= 2
    data.at[index, 'IsFraudulent'] = True
    data.at[index, 'FraudDescription'] = 'Excessive Salary - Salary inflated significantly.'

def invalid_account_numbers(data, index):
    global fraud_counts
    fraud_counts["Invalid Account Numbers"] += 1
    current_account_number = data.at[index, 'MaskedAccountNumber']
    altered_account = (
        current_account_number.replace('*', '') + ''.join([str(random.randint(0, 9)) for _ in range(random.randint(1, 3))])
        if random.choice([True, False])
        else current_account_number.replace('*', '')[:-random.randint(1, 3)]
    )
    data.at[index, 'MaskedAccountNumber'] = altered_account
    data.at[index, 'IsFraudulent'] = True
    data.at[index, 'FraudDescription'] = 'Invalid Account - Account number altered to an invalid length.'

def double_salary_payments(data, index, new_rows):
    global fraud_counts
    fraud_counts["Double Salary Payments"] += 1
    duplicate = data.iloc[index].copy()
    duplicate['MonthYear'] = f"{duplicate['MonthYear']}-DUP"
    duplicate['FraudDescription'] = 'Double Payment - Salary paid twice for the same month.'
    duplicate['IsFraudulent'] = True
    new_rows.append(duplicate)

# Fraud application
fraud_scenarios = [
    ghost_employees,
    duplicate_records,
    excessive_salary_payments,
    invalid_account_numbers,
    double_salary_payments
]

alteration_level = 'low'  # Can be 'low', 'medium', or 'high'
total_records = len(data)
if alteration_level == 'low':
    alteration_count = max(1, total_records // 10)
elif alteration_level == 'medium':
    alteration_count = max(1, total_records // 2)
else:
    alteration_count = total_records

indices_to_alter = random.sample(range(total_records), alteration_count)
new_rows = []

for i, index in enumerate(indices_to_alter):
    fraud_scenario = random.choice(fraud_scenarios)
    activity_name = fraud_scenario.__name__.replace('_', ' ').capitalize()
    if fraud_scenario in [duplicate_records, double_salary_payments]:
        fraud_scenario(data, index, new_rows)
    else:
        fraud_scenario(data, index)
    
    progress = ((i + 1) / alteration_count) * 100
    logging.info(f"Progress: {progress:.2f}% - Current activity: {activity_name}")

if new_rows:
    data = pd.concat([data, pd.DataFrame(new_rows)], ignore_index=True)

# Extract unique MonthYear values
unique_months = data['MonthYear'].unique()

# Use the first MonthYear value for naming, assuming all records are from the same period
if len(unique_months) > 1:
    logging.warning("Multiple MonthYear values found. Using the first one for file naming.")
month_year = unique_months[0].replace(" ", "_")  # Replace spaces with underscores for file compatibility

# Define file paths dynamically
output_path = f"data/{month_year}_altered_dataset.csv"
summary_report_path_txt = f"data/{month_year}_SummaryReport.txt"
summary_report_path_html = f"data/{month_year}_SummaryReport.html"
visual_path_bar = f"data/{month_year}_FraudSummary_Bar.png"
visual_path_pie = f"data/{month_year}_FraudSummary_Pie.png"
visual_path_hist = f"data/{month_year}_FraudSummary_Hist.png"

# Save altered dataset
try:
    data.to_csv(output_path, index=False)
    logging.info(f"Altered dataset saved to {output_path}.")
except Exception as e:
    logging.error(f"Error saving altered dataset: {e}")
    raise

# Generate summary
total_fraudulent = data['IsFraudulent'].sum()
total_valid = len(data) - total_fraudulent
summary = (
    f"==== PAYROLL FRAUD SUMMARY REPORT ====\n"
    f"Total Records: {len(data)}\n"
    f"Total Fraudulent Records: {total_fraudulent}\n"
    f"Total Valid Records: {total_valid}\n"
    f"--- Fraud Counts by Scenario ---\n"
    f"Ghost Employees: {fraud_counts['Ghost Employees']}\n"
    f"Duplicate Records: {fraud_counts['Duplicate Records']}\n"
    f"Excessive Salary Payments: {fraud_counts['Excessive Salary Payments']}\n"
    f"Invalid Account Numbers: {fraud_counts['Invalid Account Numbers']}\n"
    f"Double Salary Payments: {fraud_counts['Double Salary Payments']}\n"
)

try:
    with open(summary_report_path_txt, 'w') as f:
        f.write(summary)
    logging.info(f"Summary report saved to {summary_report_path_txt}.")
except Exception as e:
    logging.error(f"Error saving summary report: {e}")
    raise

# Generate and save bar chart
fraud_data = pd.DataFrame({
    'Fraud Scenario': list(fraud_counts.keys()),
    'Count': list(fraud_counts.values())
})

plt.figure(figsize=(10, 6))
sns.barplot(
    data=fraud_data,
    x="Fraud Scenario",
    y="Count",
    hue="Fraud Scenario",  # Assigning x variable to hue
    palette="Blues_d",
    dodge=False  # To prevent the bars from splitting
)

# Adjust aesthetics
plt.title("Fraud Count by Scenario")
plt.ylabel("Count")
plt.xlabel("Fraud Scenario")
plt.xticks(rotation=45)
plt.legend([], [], frameon=False)  # Hide the legend
plt.tight_layout()

try:
    plt.savefig(visual_path_bar)
    plt.close()
    logging.info(f"Fraud summary bar chart saved to {visual_path_bar}.")
except Exception as e:
    logging.error(f"Error saving fraud summary bar chart: {e}")
    raise

# Generate and save pie chart
plt.figure(figsize=(8, 8))
plt.pie(fraud_counts.values(), labels=fraud_counts.keys(), autopct="%1.1f%%", startangle=90, colors=sns.color_palette("pastel"))
plt.title("Fraud Distribution by Scenario")

try:
    plt.savefig(visual_path_pie)
    plt.close()
    logging.info(f"Fraud summary pie chart saved to {visual_path_pie}.")
except Exception as e:
    logging.error(f"Error saving fraud summary pie chart: {e}")
    raise

# Generate and save histogram
plt.figure(figsize=(10, 6))
sns.histplot(data['GrossSalary'], bins=20, kde=True, color="blue")
plt.title("Distribution of Gross Salaries")
plt.xlabel("Gross Salary")
plt.ylabel("Frequency")

try:
    plt.savefig(visual_path_hist)
    plt.close()
    logging.info(f"Gross salary histogram saved to {visual_path_hist}.")
except Exception as e:
    logging.error(f"Error saving gross salary histogram: {e}")
    raise

logging.info("Summary report and visuals saved successfully.")
logging.info("==== PAYROLL FRAUD SIMULATION FINISHED ====")
