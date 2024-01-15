
## Background:  

I want to collect historical data on how much rain I get at my house. It seems
that, while there is a lot of interest in what the weather will be in the 
future, there isn't much interest in past weather. I can't find many useful 
sources of recent historical precipitation. The most useful one I've discovered 
is from the National Weather Service (https://www.weather.gov/marfc/DailyPrecipData).
This site shows precipitation observations at about 175 stations in the 
mid-Atlantic. The problem is, when the site updates to the next day's data, it's 
gone. I can't find any place where this data is recorded, so I'm recording it 
myself. 

Because I know there will be days that I don't get a chance to check the website 
before that day's data is gone, I wanted some automated way of recording the 
data. The NWS has an API for many of its products, but this doesn't seem to be 
one for this data. So, I made this AWS Lambda function to scrape the website and 
email me every day. 

## Notes to future me so he knows how this works
### Services used:
* **AWS Lambda:** used to run my Python code on a remote server, without me having 
to manage that remote server.  
* **AWS Simple Email Service:** used to send the final result in an email to 
myself.  
* **AWS Event Bridge:** used to schedule execution of my Lambda function, via a 
cron statement  

### Setting up the Lambda function environment
To give your Lambda function access to the modules it needs, you add what AWS 
refers to as "Layers." I'm using two layers:  

1) A custom layer that I deployed according to [these](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-create-no-dependencies) 
instructions to use `beautifulsoup4` and `haversine`. Basically:

    * Create a `python/` directory where you have `pip` install your 
    dependencies.  
        ```
        python -m pip install --target ./python haversine beautifulsoup4
        ```
    * `zip` that directory
        ```
        zip -r ./scrape-precip-data-modules.zip ./python
        ```
    * In AWS Lambda, create a layer, supplying your `.zip`
        * If your `.zip` is over 10MB, they recommend you put it in an S3 bucket 
        and pass it to the Lambda layer from the bucket
        
        ```
        aws s3 cp scrape-precip-data-modules.zip s3://scrape-burke-precip-data-modules
        ```



2) An AWS-provided layer (`AWSSDKPandas-Python311`) for `pandas`.