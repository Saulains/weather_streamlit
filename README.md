# Weather Streamlit

This project demonstrates how to present a data analysis and monitoring solution as a web application using the Streamlit framework.  
The data used in this repository contains historical temperature observations for multiple cities and current weather data retrieved via the OpenWeatherMap API.

The application performs time series analysis, anomaly detection, and current temperature monitoring.

## Files

- `app.py`: Streamlit application file  
- `temperature_data.csv`: historical temperature dataset  
- `requirements.txt`: package requirements file  

## Run Demo Locally

### Shell

For directly running Streamlit locally in the repository root folder:

```bash
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ streamlit run app.py
```

Open http://localhost:8501 to view the app.

## Streamlit Cloud Deployment

Put your app on GitHub (like this repository). Make sure it is public and that you have a requirements.txt file.

Sign into Streamlit Cloud:
Sign into https://share.streamlit.io with your GitHub account.

Deploy and share:
Click "New app", then fill in your repository, branch, and file path (app.py), choose a Python version and click "Deploy".
After deployment, the application will be available via a public link.
