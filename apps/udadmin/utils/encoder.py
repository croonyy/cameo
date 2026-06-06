from datetime import datetime


custom_encoder = {datetime: lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S")}
