import webbrowser
import os
from config import (
    output_file_current,
    output_file_forecast,
    output_png_current,
    output_png_forecast,
)
from generate_current_html import generate_current_html
from generate_forecast_html import generate_forecast_html
from epaper_image_from_html import render_html_to_epaper
from time import sleep

from utils import kill_previous_instances, get_cpu_temp

this_script = os.path.basename(__file__)
kill_previous_instances(this_script)

# webbrowser.register(
#     "firefox",
#     None,
#     webbrowser.BackgroundBrowser("C:\\Program Files\\Mozilla Firefox\\firefox.exe")
# )

if __name__ == '__main__':
    
    generate_forecast_html(output_file_forecast)
    render_html_to_epaper(output_file_forecast, output_png_forecast)
# generate_current_html(output_file_current)

# import buttons
