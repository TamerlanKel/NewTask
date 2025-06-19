import argparse
import csv
from tabulate import tabulate

def filter_data(data, header, condition):
    if not condition:
        return data

    column_name = None
    op_value = None
    operator = None

    if '>=' in condition:
        column_name, op_value = condition.split('>=', 1)
        operator = '>='
    elif '<=' in condition:
        column_name, op_value = condition.split('<=', 1)
        operator = '<='
    elif '=' in condition:
        column_name, op_value = condition.split('=', 1)
        operator = '='
    elif '>' in condition:
        column_name, op_value = condition.split('>', 1)
        operator = '>'
    elif '<' in condition:
        column_name, op_value = condition.split('<', 1)
        operator = '<'
    else:
        print(f"Error: Invalid filter condition '{condition}'. No supported operator found (=, >, <, >=, <=).")
        return []

    try:
        column_name = column_name.strip()
        op_value = op_value.strip()
        column_index = header.index(column_name)
    except ValueError:
        print(f"Error: Invalid column name '{column_name}' in filter condition '{condition}'.")
        return []
    except AttributeError:
        print(f"Error: Malformed filter condition '{condition}'.")
        return []

    filtered_rows = []
    for row in data:
        cell_value = row[column_index]
        try:
            cell_value_num = float(cell_value)
            op_value_num = float(op_value)

            if (operator == '=' and cell_value_num == op_value_num) or \
               (operator == '>=' and cell_value_num >= op_value_num) or \
               (operator == '<=' and cell_value_num <= op_value_num) or \
               (operator == '>' and cell_value_num > op_value_num) or \
               (operator == '<' and cell_value_num < op_value_num):
                filtered_rows.append(row)
        except ValueError:
            if operator == '=' and cell_value.strip().lower() == op_value.strip().lower():
                filtered_rows.append(row)
            elif operator in ('>', '<', '>=', '<='):
                continue
    return filtered_rows

def aggregate_data(data, header, aggregation_expression):
    if not aggregation_expression:
        return None

    try:
        column_name, agg_type = aggregation_expression.split('=', 1)
        column_name = column_name.strip()
        agg_type = agg_type.strip().lower()
        column_index = header.index(column_name)
    except ValueError:
        print(f"Error: Invalid aggregation expression '{aggregation_expression}'. Check column name or format.")
        return None

    if agg_type not in ['avg', 'min', 'max']:
        print(f"Error: Invalid aggregation type '{agg_type}'. Supported types: avg, min, max.")
        return None

    values = []
    for row in data:
        try:
            values.append(float(row[column_index]))
        except ValueError:
            print(f"Warning: Non-numeric value '{row[column_index]}' in column '{column_name}'. Skipping for aggregation.")
            continue

    if not values:
        return {agg_type: 'N/A'}

    if agg_type == 'avg':
        return {agg_type: sum(values) / len(values)}
    elif agg_type == 'min':
        return {agg_type: min(values)}
    elif agg_type == 'max':
        return {agg_type: max(values)}

def main():
    parser = argparse.ArgumentParser(description="Process CSV files with filtering and aggregation.")
    parser.add_argument("file_path", help="Path to the CSV file.")
    parser.add_argument("--where", help="Filter condition (e.g., 'rating>4.7', 'brand=apple').")
    parser.add_argument("--aggregate", help="Aggregation expression (e.g., 'rating=avg', 'price=min').")

    args = parser.parse_args()

    try:
        with open(args.file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            data = list(reader)
    except FileNotFoundError:
        print(f"Error: File not found at '{args.file_path}'.")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    filtered_data = filter_data(data, header, args.where)

    if args.aggregate:
        aggregation_result = aggregate_data(filtered_data, header, args.aggregate)
        if aggregation_result:
            # Prepare for tabulate output
            agg_header = [list(aggregation_result.keys())[0]]
            agg_row = [list(aggregation_result.values())[0]]
            print(tabulate([agg_row], headers=agg_header, tablefmt="pipe"))
    else:
        if filtered_data:
            print(tabulate(filtered_data, headers=header, tablefmt="pipe"))
        else:
            print("No data found after filtering.")

if __name__ == "__main__":
    main()