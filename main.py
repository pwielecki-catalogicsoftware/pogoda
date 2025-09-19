import webbrowser
from config import output_file_current, output_file_forecast
from generate_current_html import generate_current_html
from generate_forecast_html import generate_forecast_html

webbrowser.register(
    "firefox",
    None,
    webbrowser.BackgroundBrowser("C:\\Program Files\\Mozilla Firefox\\firefox.exe")
)

if __name__ == '__main__':
    generate_forecast_html(output_file_forecast)
    generate_current_html(output_file_current)
