import pandas as pd
from datetime import datetime
import os

def process_file(input_filepath):
    # Extract the base filename without extension
    base_filename = os.path.splitext(os.path.basename(input_filepath))[0]
    
    # Specify column names
    column_names = ['Date_Time', 'Data_Type', 'Process', 'Fat', 'SNF', 'Density', 'Water', 'LTC', 'GSS', 'Factory']

    # Read the TXT file into a pandas DataFrame
    data = pd.read_csv(input_filepath, sep='\t', header=None, names=column_names, na_values=[''])

    # Convert 'Date_Time' column to strings
    data['Date_Time'] = data['Date_Time'].astype(str)

    # Function to convert the date-time string to a datetime object
    def convert_to_datetime(number):
        try:
            if len(number) < 12:
                number = '0' + number

            day = int(number[0:2])
            month = int(number[2:4])
            year = 2000 + int(number[4:6])
            hour = int(number[6:8])
            minute = int(number[8:10])
            second = int(number[10:12])

            # Check for valid date and time
            if month < 1 or month > 12 or day < 1 or day > 31 or hour > 23 or minute > 59 or second > 59:
                return None

            # Attempt to create a datetime object to catch invalid dates (e.g., February 30)
            return datetime(year, month, day, hour, minute, second)
        except (ValueError, TypeError):
            return None

    # Apply the function to the 'Date_Time' column
    data['Date_Time'] = data['Date_Time'].apply(convert_to_datetime)

    # Remove rows with invalid date-time values
    data = data.dropna(subset=['Date_Time'])

    # Custom function to determine shift
    def get_shift(datetime_value):
        hour = datetime_value.hour
        if 0 < hour < 12:
            return 'Morning'
        else:
            return 'Evening'

    # Apply the function to create 'Shift' column
    # Extract time component
    data['Time'] = data['Date_Time'].dt.time
    data['Shift'] = data['Date_Time'].apply(get_shift)

    data['Date'] = data['Date_Time'].dt.date
    data['Year'] = data['Date_Time'].dt.year
    data['Month'] = data['Date_Time'].dt.month
    data['Day'] = data['Date_Time'].dt.day
    data['Month_Name'] = data['Date_Time'].dt.month_name()

    # Calculate number of unique dates
    number_of_records = len(data['Date'].unique())
    One = pd.DataFrame({'Number_of_Records': [number_of_records]})
    
    # Processing Two: Pivot table of MS process by Date and Shift
    Two = data[data['Process'] == 'MS'].pivot_table(index='Date', columns='Shift', aggfunc={'Process': 'size'}).sort_index(ascending=False)

    # Processing Three: Sum of Process1 by Date and Shift divided by 25
    data['Process1'] = pd.to_numeric(data['Process'], errors='coerce')
    Three = round(data.pivot_table(index='Date', columns='Shift', aggfunc={'Process1': 'sum'}) / 25, 0).sort_index(ascending=False)

    # Define month order
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December']

    # Processing Four
    data['Month_Name'] = pd.Categorical(data['Month_Name'], categories=month_order, ordered=True)
    df1 = data.copy()
    df1['Fat'] = pd.to_numeric(df1['Fat'], errors='coerce')
    df1['SNF'] = pd.to_numeric(df1['SNF'], errors='coerce')
    Four = round(
        df1[(df1['Fat'] > 1.5) & (df1['SNF'] > 3) & (df1['Process'] == 'CLN')]
        .pivot_table(index='Month_Name', columns=['Shift', 'Year'], aggfunc={'Process': 'count'}),
        0
    )

    # Processing Five
    Five = round(
        df1[(df1['Fat'] < 0.2) & (df1['SNF'] > 4) & (df1['Process'] == 'CLN')]
        .pivot_table(index='Date', columns=['Shift', 'Year'], aggfunc={'Process': 'count'})
        .fillna(0),
        0
    )

    # Processing Six
    Six = data[(data['Data_Type'] == 'E') & (data['Fat'] != 0)].groupby(['Month_Name', 'Process', 'Fat']).agg(
        No_of_Record_in_Day=('Data_Type', 'size'))

    # Processing Seven
    Seven = data[(data['Data_Type'] == 'S') & data['Process'].isin(['INTERCEPT_FAT', 'SLOPE_SNF', 'INTERCEPT_SNF', 'SLOPE_FAT'])].groupby(
        ['Date', 'Process', 'LTC', 'SNF', 'Density']).agg(No_of_Record_in_Day=('Time', 'size'))

    # Processing Eight

    def calculate_gain(row):
        try:
            fat_value = float(row['Fat'])  # Convert the 'Fat' column to float for numerical comparison
            if 2 <= fat_value < 5:
                return 'Low Gain' + " " + str(int(row['GSS']))
            elif 5.1 < fat_value < 7.5:
                return 'Medium Gain' + " " + str(int(row['GSS']))
            elif 2 > fat_value:
                return  str(int(row['GSS']))
            else:
                return 'Higher Gain' + " " + str(int(row['GSS']))
        except ValueError:
            return 'Invalid Value'   # Or any other appropriate handling for non-numeric values
        
    data['Gain'] = data.apply(calculate_gain, axis=1)

    Eight = data[data['Process'] == 'MS'][['Date', 'Year', 'Month', 'Fat', 'SNF', 'Gain']]

    # Processing Nine
    Nine = df1[df1['Process'] == 'MACHINE'][['Process', 'Fat', 'SNF', 'LTC']]

    # Final_data_with_Gain remains unchanged
    Final_data_with_Gain = data

    # Generate output filename with the same base name as input file
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    output_filename = f'{base_filename}_{timestamp}.xlsx'
    output_filepath = os.path.join('output', output_filename)
    
    # Save the processed DataFrame and other data to an output Excel file
    with pd.ExcelWriter(output_filepath) as writer:
        #data.to_excel(writer, sheet_name='Original Data', index=False)
        One.to_excel(writer, sheet_name='Total Sample', index=False)
        Two.to_excel(writer, sheet_name='Shiftwise Sample')
        Three.to_excel(writer, sheet_name='Water Cleaning')
        Four.to_excel(writer, sheet_name='Monthly Cleaning')
        Five.to_excel(writer, sheet_name='Daily Cleaning')
        Six.to_excel(writer, sheet_name='Error')
        Seven.to_excel(writer, sheet_name= 'Calibration')
        Eight.to_excel(writer, sheet_name='Gain', index=False)
        Nine.to_excel(writer, sheet_name='Machine ID Change', index=False)
        Final_data_with_Gain.to_excel(writer, sheet_name='Final_data_with_Gain', index=False)

    return output_filename
