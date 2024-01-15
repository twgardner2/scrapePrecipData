
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
one for this data. So, I made this lambda function to scrape the website and 
email me every day. 