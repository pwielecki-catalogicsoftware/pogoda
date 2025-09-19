import locale
import platform
from datetime import datetime

locale.setlocale(locale.LC_ALL, "pl_PL.UTF-8")

if platform.system() == "Windows":
    DAY_FORMAT = "%#d"
else:
    DAY_FORMAT = "%-d"

def localize_and_round(value, ndigits=1):
    return locale.format_string(f"%.{ndigits}f", value)

MONTHS_GENITIVE = {
    1: "stycznia",
    2: "lutego",
    3: "marca",
    4: "kwietnia",
    5: "maja",
    6: "czerwca",
    7: "lipca",
    8: "sierpnia",
    9: "września",
    10: "października",
    11: "listopada",
    12: "grudnia",
    13: "failfailfail"
}

def format_datetime_pl_genitive(dt, capitalize=False):
    day = dt.day
    month_full = MONTHS_GENITIVE[dt.month]
    year = dt.year
    weekday = dt.strftime("%A")
    if capitalize:
        return f"{weekday.capitalize()}, {day} {month_full} {year} r."
    else:
        return f"{weekday}, {day} {month_full} {year} r."