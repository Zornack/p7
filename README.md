# UOCIS322 - Project 7 #
Author: Jaryd Davis, jcsdavis@gmail.com

An ACP brevet time calculator.

Supports user registration and authentication. Logging in genreates a token that is valid for 10 minutes. Upon token expiriation the user must log in again. 

All API functions required a loged in user. 

Username and hashed password stored in mongodb along with unique ID. 

Dockerfile included for ease of use with docker build and docker run.

Distances input as miles are converted to kilometers then floored. Distances input as kilometers are rounded to the nearest digit.

Kilometer distances are converted to opening and closing times following the minimum and maximum speeds listed here: https://rusa.org/pages/acp-brevet-control-times-calculator

Opening and closing times are added to the user entered starting time.

Negative distances return null values and an error message. Distances 20% longer than the brevet distance include an error message.

acp_times calculates the opening and closing times and returns an arrow object

flask_brevets pulls km, brevet distance and starting time from the client, then returns the opening and closing times.

javascript updates the page asynchonrasly via AJAX and jQuery.

Test calculations included for debugging. Run with nosetests. Edit tests/test_brev.py for further testing.

Insert adds km, open and close times to a database. Requires a valid final control. Inserting clears the last inserted values from the database.

Display renders a new page with the data from the database.

## Algorithm:

Min and max speeds and their respective distances are stored in tuples in lists. 

Open time pulls the start time from flask_brevets then finds the largest applicable speed range, calculates the elapsed hours from that bracket, then works down through the other brackets until complete. It returns the arrow object with the time shifted according to the calculated time.

Close time is similar except it overrides the distance with the brevet distance if it is greater than the brevet distance and has hardcoded close times for the final control.

## API:

api.py retrives the open and clse times from mongodb and serves them in either JSON or CSV. The API supports listing all the open and close times, just the open or just the close. "?top=x" returns the first x entries of the database. 0 returns all. 

api_display.py allows easy use of this service. Upon clicking display the webpage is reloaded and the requested format, top entires and query type and returned. . 0 returns all the entires and negative numbers return an error. An empty database also returns an error. 


## Credits

Michal Young, Ram Durairajan, Steven Walton, Joe Istas, Ali Hassani
