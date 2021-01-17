# Airbnb-Covid-Analysis
This repo contains an Airbnb Analysis [Dashboard](https://movie-recommendation-phil.herokuapp.com/) for presenting the impact of covid 19 on Airbnb hosts within Australia. Several factors including price, reviews, and locations were carefully studied.

# Technical Details
* Data: Most data were scraped from Inside Airbnb and formed a folder with over 1000 files. These files contain information such as reviews, monthly snapshots of listings, and availabilities etc. To handle this fairly large dataset, [Dask](https://dask.org/) was used for parallel processing,
* App: The dashboard was built with [Dash](https://dash.plotly.com/) and Plotly, then deployed on heroku with gunicorn as the WSGI server.

# Environment
First, create a virtualenv or conda environment that includes the dependencies listed in the requirements.txt file.

# Mapbox setup
To run the dashboard, create a file name Credentials.py under the directory credentials. This file should contain a valid Mapbox token, which can be obtained for free by setting up an account at https://www.mapbox.com/.

# Launching Dashboard in Development Mode
Launch the dashboard in development mode from the command line with:

$ python app.py

Then open the dashboard at the URL displayed by the command.
# Preview
The play and pause buttons have been changed to the stepper and reset buttons in live dashboard due to resource constraints
![airbnb dashboard](https://github.com/Phil-avi/Airbnb-Covid-Analysis/blob/main/assets/airbnb.gif)
