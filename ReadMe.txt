DSCI 510 Homework 5- Taylor D'Ambrosio:

Description: I have created a final dataset, using a csv file named "all_df.csv". This
dataset was created from 3 different data sources from the Data Source Section. 
"new_zip.csv", "commute_times.csv", and "zip_code_and_income.csv" are all datasets that 
were created from the Data Source Section, and used as intermediaries in order to combine 
the three into the "all_df.csv". All datasets can be found on the web, and with this code, 
can be downloaded and saved in this file to be used and combined together for further 
analysis. I created from the final dataset, a database, figures, calculated correlations,
and created an input for a user to input their zipcode in Los Angeles County and see what 
their commute time is.

Requirements:
These packages need to be installed in order to make the code run
1. requests
2. pandas
3. Beautiful Soup
4. re
5. numpy
6. scripy.stats (pearsonr and spearmanr)
7. matplotlib
8. sqlite3
9. csv
10. sys

To install these packages, a requirements.txt file is included. To use, write 
"pip install -r requirements.txt" and the package on the terminal

Data Sources:
1. Demographics of Commuters in Los Angeles (https://data.census.gov/cedsci/table?q=S0802&g=0400000US06%248600000_0500000US06037&tid=ACSST5Y2020.S0802):
Using the Census API, the dataset was accessed with a key that is included in the code and 
I specifically looked for the ZCTA 5 digit zip codes and only the zip codes found in Los 
Angeles County. The API gave me a csv with with over 2,000 columns of demographics, but only used:
wanted the columns containing: 'NAME', 'S0802_C01_090E', 'S0802_C02_008E', 'S0802_C02_009E',
'S0802_C02_010E', 'S0802_C03_008E', 'S0802_C03_009E', 'S0802_C03_010E', 'S0802_CO4_008E',
'S0802_C04_009E', 'S0802_C04_010E'
I used the metadata file that is included in this folder, derived from this website:
https://api.census.gov/data/2019/acs/acs1/subject/groups/S0802.html to change the names of 
the columns mentioned to column names that were easier to interpret the csv. The S0802 
refers to the dataset that was pulled from the census website and the other numbers are
what questions they are. E stands for "estimate" because there was "estimate" and "margin 
of error", so I used the "estimate" numbers. The API returns back a json file and I 
converted it into a csv so it would be easier to process with the other datasets.

2. Zip Codes and Median Household Income (https://www.laalmanac.com/employment/em12c.php)
From this website that lists the zip codes, cities, and median household income for all 
zip codes in Los Angeles county, I accessed the link and used beautiful soup to scrape the
website to just retrieve all the zipcodes ans the median household income and saved then
in lists and then into a csv file. 

3. Commute time and Zip Code (https://project.wnyc.org/commute-times-us/data/commute_times_us_zipcode_2011.csv)
From this website, I used the url and used pandas to get the website and download it as a
dataframe, then saved it as a csv "commute_times.csv". This includes all commute times and
their associated zip codes from all over the United States. 

Running the Code:
The code can be run in 3 modes: default, scape, and static:

Default mode: to run the code in default mode, type command - python3 scraper.py
In this mode, all four datasets and csv files ("new_zip.csv", "zip_code_and_income.csv", 
"commute_times.csv", and "all_df.csv") will be created. The figures that I have created using
the 'all_df.csv' is also made and downloaded as .png files in the folder, as well as their
correlation values will be printed. To continue running the code, each figure needs to be
closed. Make sure they are all closed so that the code will run. I have also created
a database using sqlite3, and a database is created as a .db file in the folder as well.
---NOTE IT TAKES ~1 MINUTE TO RUN THIS CODE---

Scape mode: To run the code in scape mode, type command - python3 scraper.py --scrape
In this mode, the four datasets will be generated and it will print out the first 5 rows of
each dataset as well as a description of the actual size of each dataset. 

Static mode: to run the code in static mode, type command - python3 scraper.py --static
In this mode, only the final dataset will be shown and its first 5 rows, which is the 
dataset that is used for all the analysis. 























