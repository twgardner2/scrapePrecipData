import json
import boto3
import urllib3
from bs4 import BeautifulSoup
import re
import pandas as pd
import io
from haversine import haversine

# https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-create-no-dependencies


def scrape_website(url):
    '''
    This function will return the text in the <pre></pre> tag
    '''
    # Create a connection pool manager
    http = urllib3.PoolManager()

    # Send an HTTP GET request to the URL
    response = http.request('GET', url)

    # Check if the request was successful (status code 200)
    if response.status == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.data, 'html.parser')

        # Extract data from the parsed HTML
        data = soup.find('pre').text

        return data
    else:
        print(f"Failed to retrieve data. Status code: {response.status}")
        return None


def scrape_website_example():
    return (
        '''24hr Accumulated Precipitation ending around 7AM on 2024-01-14 12:00:00. Generated Sun Jan 14 12:42:50 2024
12N      , NJ , Andover AS , 41.01 , -74.74 ,     0.03
8W2      , VA , New Market , 38.66 , -78.71 ,     0.00
ABE      , PA , Allentown  , 40.65 , -75.43 ,     0.00
ABPV2    , VA , Lincolnia  , 38.8  , -77.13 ,     0.00
ACY      , NJ , Atlantic C , 39.46 , -74.58 ,     0.00
AFRV2    , VA , Alexandria , 38.84 , -77.09 ,     0.01
AKQ      , VA , Wakefield  , 36.98 , -77.01 ,     0.00
AOO      , PA , Altoona AP , 40.3  , -78.32 ,     0.02
APXV2    , VA , Appomattox , 37.33 , -78.83 ,     0.00
ATGP1    , PA , Atglen DEO , 39.92 , -75.99 ,     0.00
AVOP1    , PA , Avondale C , 39.86 , -75.79 ,     0.01
AVP      , PA , Wilkes-Bar , 41.34 , -75.73 ,     0.04
BBBD1    , DE , Bethany Be , 38.54 , -75.05 ,     0.00
BCNV2    , VA , Burke IFLO , 38.79 , -77.3  ,     0.00
BDBN4    , NJ , Bound Broo , 40.57 , -74.55 ,     0.01
BETP1    , PA , Bethlehem  , 40.61 , -75.38 ,     0.00
BFD      , PA , Bradford A , 41.8  , -78.64 ,     0.03
BKBD1    , DE , Blackbird  , 39.4  , -75.63 ,     0.00
BKRN4    , NJ , Basking Ri , 40.71 , -74.51 ,     0.04
BKW      , WV , Beckley AP , 37.79 , -81.12 ,     0.00
BKWN4    , NJ , Blackwells , 40.48 , -74.58 ,     0.00
BLAN4    , NJ , Blue Ancho , 39.68 , -74.86 ,     0.00
BMDN4    , NJ , Belle Mead , 40.47 , -74.65 ,     0.00
BNGD1    , DE , Bethany Be , 38.55 , -75.06 ,     0.00'''
    )


def wrangleToDataframe(textIn):
    rx_dataLine = re.compile(r'^.+,.+,.+,.+,.+,.+$')

    # Keep only lines that are data (removes the text line at the top)
    precipData = [line for line in textIn.split(
        '\n') if rx_dataLine.match(line)]

    # Add a header that matches the data format
    precipData = ['stationId,state,location,lat,lng,precip'] + precipData

    # Make into dataframe
    precipData = '\n'.join(precipData)
    precipData = pd.read_csv(io.StringIO(precipData))

    return (precipData)


def closestPrecipValue(myLoc, precipDf):

    # Create tuple of (lat,lng)
    precipDf['latLng'] = precipDf.apply(
        lambda row: (row['lat'], row['lng']), axis=1)
    # Calculate haversine distance between myLoc and all observation stations
    precipDf['distToMyLoc'] = precipDf.apply(
        lambda row: haversine(row['latLng'], myLoc), axis=1)

    # Get closest station
    closestRow = precipDf[precipDf['distToMyLoc']
                          == precipDf['distToMyLoc'].min()]

    # Return row of data as a dict
    return (closestRow.to_dict('records')[0])


def sendEmail(results):

    if results['success']:
        # Unpack elements of results['precipDict']
        location, stationId, distToMyLoc, precip = (lambda location, stationId, distToMyLoc, precip, **kwargs: (
            location.strip(), stationId.strip(), distToMyLoc, precip))(**results['precipDict'])

        # Construct subject and message
        subject = f'Precipitation data for {results["date"]}'
        message = f'The precipitation for {results["date"]} at {location} ({stationId}, {distToMyLoc:0.2f} km away) was {precip:0.2f} inches.'

    else:
        # Construct subject and message
        subject = f'Precipitation data lambda function FAILURE'
        message = f'Scraping precipitation data failed because: {results["error"]}.'

    # Send email via Simple Email Service
    client = boto3.client('ses', region_name='us-east-1')

    response = client.send_email(
        Destination={
            'ToAddresses': ['twgardner2@gmail.com']
        },
        Message={
            'Subject': {
                'Charset': 'UTF-8',
                'Data': subject,
            },
            'Body': {
                'Text': {
                    'Charset': 'UTF-8',
                    'Data': message,
                }
            },
        },
        Source='twgardner2@gmail.com'
    )

    return (response)


def lambda_handler(event, context):

    urlToScrape = 'https://www.weather.gov/marfc/DailyPrecipData'
    myLoc = (38.81855487829746, -77.28262316525014)  # (lat, lng)

    # Results object to populate and pass to sendEmail at the end
    results = {
        'success':    None,
        'precipDict': None,
        'date':       None,
        'error':      None,
    }

    # Scrape precipitation data from NWS
    scraped_data = scrape_website(urlToScrape)
    # scraped_data = scrape_website_example()

    if scraped_data:
        print(f'Scraping succeeded.')
    else:
        print('Scraping failed.')
        results['success'] = False
        results['error'] = 'scraping failed'

    if results['success'] is not False:
        # Get date of data
        try:
            rx_date = re.compile(r'\d{4}-\d{2}-\d{2}')
            # rx_date = re.compile(r'\d{5}-\d{2}-\d{2}')
            date = rx_date.search(scraped_data).group()
            results['date'] = date
        except AttributeError:
            print('Extracting date failed.')
            results['success'] = False
            results['error'] = 'extracting date failed'

    if results['success'] is not False:
        # Wrangle scraped text into Dataframe
        try:
            df = wrangleToDataframe(scraped_data)
        except:
            print('Converting scraped data to dataframe failed.')
            results['success'] = False
            results['error'] = 'converting scraped data to dataframe failed'

    if results['success'] is not False:
        # Get precip at closest observation station
        try:
            # precipLoc, precip = closestPrecipValue(myLoc, df)
            results['precipDict'] = closestPrecipValue(myLoc, df)
            results['success'] = True
            # print(precipDict)
        except:
            print('Finding the closest observation station failed.')
            results['success'] = False
            results['error'] = 'finding the closest observation station failed'

    # Send the email
    response = sendEmail(results)

    return (response)
