import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
import numpy as np
from scipy.stats import pearsonr
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
import sqlite3
import csv
import sys


# turning the json file from the api into a readable file
def json_to_dataframe(response):
    return pd.DataFrame(response.json()[1:], columns=response.json()[0])


def df_to_csv(df, filename):
    return df.to_csv(filename, encoding='utf-8', index=False)


def get_data_from_web(url):
    df = pd.read_csv(url)
    df.to_csv("commute_times.csv", encoding='utf-8', index=False)
    print("commute_times.csv was created!")
    return df


def get_csv_web(url, filename):
    req = requests.get(url)
    url_content = req.content
    csv_file = open(filename, 'wb')
    csv_file.write(url_content)
    csv_file.close()
    return csv_file


def get_api_info(website, filename):
    url = website
    response = requests.request("GET", url)
    census = json_to_dataframe(response)
    census.to_csv(filename)
    print("new_zip.csv was created!\n")
    return census


def get_med_income():
    url = 'https://www.laalmanac.com/employment/em12c.php'
    content = requests.get(url)
    soup = BeautifulSoup(content.content, 'html.parser')
    # getting zipcode
    zip_tag = soup.find('tbody')
    output = []
    for button_tag in zip_tag.find_all('tr'):
        texts = button_tag.find_all('td')
        for text in texts:
            if text.text.isdigit():
                output.append(int(text.text))

    # removing two zipcodes that have no income related to it
    unwantedNum = {91046, 93563}
    newOutput = [ele for ele in output if ele not in unwantedNum]
    incomeLst = []
    # getting income and putting it into a list
    soup.find_all('td')
    income = [tag.text for tag in soup.find_all('td', text=re.compile(r'\$\d*'))]
    for item in income:
        incomeLst.append(item)

    # creating dataframe/csv file incomeLst and output
    df = pd.DataFrame(list(zip(newOutput, incomeLst)), columns=['zip_code', 'median_household_income'])
    df.to_csv('zip_code_and_income.csv', index=False)
    print("zip_code_and_income.csv was created!\n")
    return df


def read_csv(filename):
    df = pd.read_csv(filename)
    return df


def clean_df():
    # making column names same so they can merge easy
    df = pd.read_csv("new_zip.csv")
    df = df.rename(columns={"NAME": "new_zip_code"})
    df1 = pd.read_csv("commute_times.csv")
    df1 = df1.rename(columns={"census_display_label": "new_zip_code"})
    # merge df and df1
    new_df = pd.merge(df, df1)

    # rename the new_zip columns to the ones from metadata file
    renamed_csv = new_df.rename(columns={'S0802_C01_090E': 'travel_time',
                                         'S0802_C02_008E': 'drove_alone_age',
                                         'S0802_C02_009E': 'drove_alone_male',
                                         'S0802_C02_010E': 'drove_alone_female',
                                         'S0802_C03_008E': 'carpooled_age',
                                         'S0802_C03_009E': 'carpooled_male',
                                         'S0802_C03_010E': 'carpooled_female',
                                         'S0802_C04_008E': 'public_transport_age',
                                         'S0802_C04_009E': 'public_transport_male',
                                         'S0802_C04_010E': 'public_transport_female'
                                         })

    # new df with the important columns only
    renamed_csv = renamed_csv[
        ['new_zip_code', 'GEO_ID', 'zip_code', 'travel_time', 'drove_alone_age', 'drove_alone_male',
         'drove_alone_female', 'carpooled_age', 'carpooled_male', 'carpooled_female', 'public_transport_age',
         'public_transport_male', 'public_transport_female', 'commute_time_mins_est']]

    # merging one more df, changing the column name
    df2 = pd.read_csv("zip_code_and_income.csv")
    all_df = pd.merge(renamed_csv, df2)

    # cleaning median household income (getting rid of $ and ,
    all_df['median_household_income'] = all_df['median_household_income'].str.replace(',', '', regex=True).str.replace(
        '$', '', regex=True). \
        astype(int)

    # getting rid of NAN
    all_df["commute_time_mins_est"] = np.nan_to_num(all_df["commute_time_mins_est"])

    # wrte to csv
    df_to_csv(all_df, "all_df.csv")
    print("Combined csv was created!\n")
    return all_df


def create_database(filename):
    print("Creating database...")
    file = open(filename)
    conn = sqlite3.connect('commute_income.db')
    c = conn.cursor()
    c.execute("""DROP TABLE IF EXISTS combined""")
    query = """CREATE TABLE commute_income_dataset (new_zip_code str, 
                                                        GEO_ID str, 
                                                        zip_code int,
                                                        travel_time real, 
                                                        drove_alone_age real,
                                                        drove_alone_male real,
                                                        drove_alone_female real,
                                                        carpooled_age real,
                                                        carpooled_male real,
                                                        carpooled_female real,
                                                        public_transport_age real,
                                                        public_transport_male real,
                                                        public_transport_female real,
                                                        commute_time_mins_est real,
                                                        median_household_income int
                                                        )"""
    c.execute(query)
    with open(filename, "r") as fin:
        dr = csv.DictReader(fin)
        to_db = [(i["new_zip_code"], i["GEO_ID"], i["zip_code"], i["travel_time"], i["drove_alone_age"],
                  i["drove_alone_male"], i["drove_alone_female"], i["carpooled_age"], i["carpooled_male"],
                  i["carpooled_female"], i["public_transport_age"], i["public_transport_male"],
                  i["public_transport_female"], i["commute_time_mins_est"], i["median_household_income"]) for i in dr]
    c.executemany(
        "INSERT INTO commute_income_dataset (new_zip_code, GEO_ID, zip_code, travel_time, drove_alone_age, drove_alone_male, drove_alone_female, carpooled_age, carpooled_male, carpooled_female, public_transport_age, public_transport_male, public_transport_female, commute_time_mins_est, median_household_income) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);",
        to_db)
    conn.commit()
    conn.close()
    print("Database created!\n")


def get_coer_val_df(df, column1, column2):
    data1 = df[column1]
    data2 = df[column2]

    # perason's correlation
    corr, _ = pearsonr(data1, data2)
    print('Pearsons correlation: %.3f' % corr)

    # sperman's correlation
    corr, _ = spearmanr(data1, data2)
    print('Spearmans correlation: %.3f' % corr)


def get_figs(csv):
    df = pd.read_csv(csv)

    # changing the large negative values (NA) to 0
    num = df._get_numeric_data()
    num[num < 0] = 0

    # income vs commmute
    x = df["median_household_income"]
    y = df["commute_time_mins_est"]
    # plot
    plt.scatter(x, y)
    plt.title("Income vs Commute time")
    plt.xlabel("Income")
    plt.ylabel("Commute Time (mins)")
    # creating a regression line
    m, b = np.polyfit(x, y, 1)
    plt.plot(x, m * x + b, color='red')
    # printing correlations
    print("\nCorrelation between Income and Commute:")
    get_coer_val_df(df, "median_household_income", "commute_time_mins_est")
    plt.savefig("income_commute.png")
    plt.show()

    # drove_alone vs commute time
    # find the 0 values to drop them
    # print((df.loc[df['drove_alone_age'] == 0]))
    # dropping the 0 value at its index
    new_df = df.drop([214])
    x = new_df["drove_alone_age"]
    y = new_df["commute_time_mins_est"]
    # plot
    plt.scatter(x, y)
    plt.title("Drove Alone Age vs Commute time")
    plt.xlabel("Drove Alone Age")
    plt.ylabel("Commute Time (mins)")
    # creating a regression line
    m, b = np.polyfit(x, y, 1)
    plt.plot(x, m * x + b, color='red')
    # printing correaltion
    print("\nCorrelation between Drive Alone Age and Commute:")
    get_coer_val_df(new_df, "drove_alone_age", "commute_time_mins_est")
    plt.show()

    # drove_alone vs commute time
    # finding 0 value at index
    # print((df.loc[df['drove_alone_male'] == 0]))
    # dropping 0
    new_df = df.drop([214])
    x = new_df["drove_alone_male"]
    y = new_df["commute_time_mins_est"]
    # plot
    plt.scatter(x, y)
    plt.title("Drove Alone Male vs Commute time")
    plt.xlabel("Drove Alone Male")
    plt.ylabel("Commute Time (mins)")
    # creating a regression line
    m, b = np.polyfit(x, y, 1)
    plt.plot(x, m * x + b, color='red')
    # printing correaltion
    print("\nCorrelation between Drive Alone Male and Commute:")
    get_coer_val_df(new_df, "drove_alone_male", "commute_time_mins_est")
    plt.savefig("drove_alone_male_commute.png")
    plt.show()

    # drove_alone vs commute time
    # dropping the 0
    # print((df.loc[df['drove_alone_female'] == 0]))
    new_df = df.drop([214])
    x = new_df["drove_alone_female"]
    y = new_df["commute_time_mins_est"]
    # plot
    plt.scatter(x, y)
    plt.title("Drove Alone Female vs Commute time")
    plt.xlabel("Drove Alone Female")
    plt.ylabel("Commute Time (mins)")
    # creating a regression line
    m, b = np.polyfit(x, y, 1)
    plt.plot(x, m * x + b, color='red')
    # printing correaltion
    print("\nCorrelation between Drive Alone Female and Commute:")
    get_coer_val_df(new_df, "drove_alone_female", "commute_time_mins_est")
    plt.savefig("drove_alone_female_commute.png")
    plt.show()

    # carpooled vs commute time
    # dropping 0 index
    # print((df.loc[df['carpooled_age'] == 0]))
    new_df = df.drop([25, 187, 214])
    x = new_df["carpooled_age"]
    y = new_df["commute_time_mins_est"]
    # plot
    plt.scatter(x, y)
    plt.title("Carpooled Age vs Commute time")
    plt.xlabel("Carpooled")
    plt.ylabel("Commute Time (mins)")
    # creating a regression line
    m, b = np.polyfit(x, y, 1)
    plt.plot(x, m * x + b, color='red')
    # printing correaltion
    print("\nCorrelation between Carpool Age and Commute:")
    get_coer_val_df(new_df, "carpooled_age", "commute_time_mins_est")
    plt.savefig("carpooled_age_commute.png")
    plt.show()

    # carpooled vs commute time
    # dropping 0 index
    # print((df.loc[df['carpooled_male'] == 0]))
    new_df = df.drop([25, 187, 214])
    x = new_df["carpooled_male"]
    y = new_df["commute_time_mins_est"]
    # plot
    plt.scatter(x, y)
    plt.title("Carpooled Male vs Commute time")
    plt.xlabel("Carpooled")
    plt.ylabel("Commute Time (mins)")
    # creating a regression line
    m, b = np.polyfit(x, y, 1)
    plt.plot(x, m * x + b, color='red')
    # printing correaltion
    print("\nCorrelation between Carpool Male and Commute:")
    get_coer_val_df(new_df, "carpooled_male", "commute_time_mins_est")
    plt.savefig("carpooled_male_commute.png")
    plt.show()

    # carpooled vs commute time
    # dropping 0 at index
    # print((df.loc[df['carpooled_female'] == 0]))
    new_df = df.drop([187, 214])
    x = new_df["carpooled_female"]
    y = new_df["commute_time_mins_est"]
    # plot
    plt.scatter(x, y)
    plt.title("Carpooled Female vs Commute time")
    plt.xlabel("Carpooled")
    plt.ylabel("Commute Time (mins)")
    # creating a regression line
    m, b = np.polyfit(x, y, 1)
    plt.plot(x, m * x + b, color='red')
    # printing correaltion
    print("\nCorrelation between Carpool Female and Commute:")
    get_coer_val_df(new_df, "carpooled_female", "commute_time_mins_est")
    plt.savefig("carpooled_female_commute.png")
    plt.show()

    # public transport vs commute time
    # dropping 0 at index
    # print((df.loc[df['public_transport_age'] == 0]))
    new_df = df.drop([25, 90, 93, 95, 96, 139, 177, 187, 206, 214, 233, 271, 277])
    x = new_df["public_transport_age"]
    y = new_df["commute_time_mins_est"]
    # plot
    plt.scatter(x, y)
    plt.title("Public Transport Age vs Commute time")
    plt.xlabel("Public Transport Age")
    plt.ylabel("Commute Time (mins)")
    # creating a regression line
    m, b = np.polyfit(x, y, 1)
    plt.plot(x, m * x + b, color='red')
    # printing correaltion
    print("\nCorrelation between Public Transport Age and Commute:")
    get_coer_val_df(new_df, "public_transport_age", "commute_time_mins_est")
    plt.savefig("public_transport_age_commute.png")
    plt.show()

    # public transport vs commute time
    # dropping 0 at index
    # print((df.loc[df['public_transport_male'] == 0]))
    new_df = df.drop([25, 93, 95, 96, 139, 177, 187, 206, 214, 233, 271, 277])
    x = new_df["public_transport_male"]
    y = new_df["commute_time_mins_est"]
    # plot
    plt.scatter(x, y)
    plt.title("Public Transport Male vs Commute time")
    plt.xlabel("Public Transport Male")
    plt.ylabel("Commute Time (mins)")
    m, b = np.polyfit(x, y, 1)
    # add linear regression line to scatterplot
    plt.plot(x, m * x + b, color='red')
    # printing correaltion
    print("\nCorrelation between Public Transport Male and Commute:")
    get_coer_val_df(new_df, "public_transport_male", "commute_time_mins_est")
    plt.savefig("public_transport_male_commute.png")
    plt.show()

    # public transport vs commute time
    # dropping 0 at index
    # print((df.loc[df['public_transport_female'] == 0]))
    new_df = df.drop([25, 29, 90, 93, 95, 139, 177, 214, 233, 271, 277])
    x = new_df["public_transport_female"]
    y = new_df["commute_time_mins_est"]
    # plot
    plt.scatter(x, y)
    plt.title("Public Transport Female vs Commute time")
    plt.xlabel("Public Transport Female")
    plt.ylabel("Commute Time (mins)")
    # creating regression line
    m, b = np.polyfit(x, y, 1)
    plt.plot(x, m * x + b, color='red')
    # printing correaltion
    print("\nCorrelation between Public Transport Female and Commute:")
    get_coer_val_df(new_df, "public_transport_female", "commute_time_mins_est")
    plt.savefig("public_transport_female_commute.png")
    plt.show()

    print("\nFigures are made!\n")


def find_commute(csv, commute_time, zip_code):
    df = pd.read_csv(csv)
    commute_time = df[commute_time].tolist()
    zip_code = df[zip_code].tolist()
    zip_income = {zip_code[i]: commute_time[i] for i in range(len(zip_code))}
    while True:
        zipcode = input(
            "Welcome! Please enter a 5 digit zip code in Los Angeles County to find out your average commute time: ")
        try:
            if int(zipcode) not in zip_code:
                print("Not in zip code list, please input again")
            else:
                break
        except ValueError:
            print("Please input digits")
    zipcode = int(zipcode)
    print("Your average commute time is: ", zip_income.get(zipcode))


def main(argv):
    if len(argv) == 0:  # Run all datasets
        # API dataset
        commute_transport = get_api_info(
            "https://api.census.gov/data/2017/acs/acs5/subject?get=NAME,group(S0802)&for=zip%20code%20tabulation%20area:*&in=state:06&key=e5cb7b8fef1a0231c759d2bc2e6dbcb33651366f",
            'new_zip.csv')

        # beautifulsoup dataset
        income = get_med_income()

        # read in csv file
        commute_time = get_data_from_web(
            'https://project.wnyc.org/commute-times-us/data/commute_times_us_zipcode_2011.csv')

        # make combined csv
        clean = clean_df()

        # run plots
        # get_figs('all_df.csv')

        # create database
        create_database("all_df.csv")

        # print out all datasets:
        print(commute_transport)
        print(commute_time)
        print(income)
        print(clean)

        # create figures
        get_figs('all_df.csv')

        # printing out input
        find_commute("all_df.csv", "commute_time_mins_est", "zip_code")

    else:
        if argv[0] == '--scrape':  # Only return the first 5 rows
            # API datasets
            commute_transport = get_api_info(
                "https://api.census.gov/data/2017/acs/acs5/subject?get=NAME,group(S0802)&for=zip%20code%20tabulation%20area:*&in=state:06&key=e5cb7b8fef1a0231c759d2bc2e6dbcb33651366f",
                'new_zip.csv')

            # beautifulsoup dataset

            # read in csv
            commute_time = get_data_from_web(
                'https://project.wnyc.org/commute-times-us/data/commute_times_us_zipcode_2011.csv')

            # make combine csv

            # print first 5 rows
            print(commute_transport[:5])
            print(get_med_income()[:5])
            print(commute_time[:5])
            print(clean_df()[:5])


        elif argv[0] == '--static':
            commute_transport = get_api_info(
                "https://api.census.gov/data/2017/acs/acs5/subject?get=NAME,group(S0802)&for=zip%20code%20tabulation%20area:*&in=state:06&key=e5cb7b8fef1a0231c759d2bc2e6dbcb33651366f",
                'new_zip.csv')

            # beautifulsoup dataset
            get_med_income()

            # read in csv
            get_data_from_web('https://project.wnyc.org/commute-times-us/data/commute_times_us_zipcode_2011.csv')

            # make combine csv
            print("Combined dataframe: \n")
            print(clean_df()[:5])


if __name__ == "__main__":
    main(sys.argv[1:])
