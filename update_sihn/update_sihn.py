import requests
from a5client import Crud
import json
import argparse
import os
from datetime import datetime, timedelta
import sys
#import logging
from .logger import Logger
from pathlib import Path

logger = Logger(level='DEBUG')

def validate_date(date_str):
    """Validate and parse a date string."""
    formats = [
        "%Y-%m-%d",             # Date only
        "%Y-%m-%d %H:%M",       # Date and time without seconds
        "%Y-%m-%d %H:%M:%S",    # Date and time with seconds
        "%Y-%m-%d %H:%M:%S%z",  # Date, time, and timezone
        "%Y-%m-%dT%H:%M:%S",    # ISO 8601 without timezone (asumes UTC)
        "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601 with timezone
        "%Y-%m-%d %H:%M:%S.%f%z",  # Date, time, and timezone
        "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO 8601 with timezone
        "%m-%d-%Y"              # date only, US format
    ]
    for format in formats:
        try:
            return datetime.strptime(date_str, format)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: '{date_str}'. Expected formats: YYYY-MM-DD, YYYY-MM-DD HH:MM, YYYY-MM-DD HH:MM:SS, YYYY-MM-DD HH:MM:SSZZZ, YYYY-MM-DDTHH:MM:SS, YYYY-MM-DDTHH:MM:SSZZZ, YYYY-MM-DD HH:MM:SS.mmmZZZ, YYYY-MM-DDTHH:MM:SS.mmmZZZ.")

def valid_date(date_str):
    if date_str is None:
        return None
    try:
        return validate_date(date_str)
    except ValueError as e:
        raise argparse.ArgumentTypeError(e)

# load config

def load_config(file_path):
    with open(file_path, 'r') as config_file:
        config = json.load(config_file)
    return config

configfile = Path(__file__).parent / "../config/config.json"
if not configfile.is_file():
    logger.warning("Falta el archivo config/config.json. Cargando config/default.json")
    configfile = Path(__file__).parent / "../config/default.json"

config = load_config(configfile)

# logging.basicConfig(
#     level=logging.DEBUG,  # Set the logging level
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     stream=sys.stdout  # Set output to stdout
# )

codigos = config["codigos"]

def startSession():
    session = requests.Session()
    session.get(config["source_url"])
    return session

def downloadValoresGrafico(cod_mareografo : str = "SFER", date : datetime = datetime.now(), session : requests.Session = None):
    
    if session is None:
        # get cookies
        session = startSession()
    
    # Format the date and time into a string of the form 'YYYYMMDDHHMM'
    _fecha = date.strftime('%Y%m%d%H%M')
    
    # URL for the request
    # https://shn.geoportal.hidro.gob.ar/shnapi/v1/AlturasHorarias/ValoresGrafico/SFER/202502111303
    url = '%s/api/v1/AlturasHorarias/ValoresGrafico/%s/%s' % (config["api_url"], cod_mareografo, _fecha) # ?_=1731069352396
    
    logger.debug("get: %s" % url)
    # Make the GET request
    response = session.get(url) # , headers=headers)
    
    # Check the status code of the response
    if response.status_code == 200:
        # If the request is successful, print the JSON response
        data = response.json()
        return data
    else:
        raise Exception(f"Request failed with status code {response.status_code}")


def parseData(data : dict = None, filename : str = None, series_id : int = 52):
    if data is None:
        if filename is None:
            raise ValueError("missing data or filename")
        f = open(filename,"r")
        data = json.load(f)
    obs = []
    for l in data["lecturas"]:
        obs.append({
            "timestart": "%s.000-0300" % l["fecha"], 
            "timeend": "%s.000-0300" % l["fecha"], 
            "valor": l["altura"], 
            "series_id": series_id
        })
    return obs

def uploadObs(obs, series_id, tipo : str = "puntual", url : str = config["api"]["url"], token : str = config["api"]["token"]):
    if not len(obs):
        raise ValueError("obs must be of length > 0")
    client = Crud(url, token )
    return client.createObservaciones(obs, series_id, tipo)

def valid_file_path(path):
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"The file '{path}' does not exist.")
    return path

def downloadParseAndUpload(cod_mareografo : str, series_id : int = None, test : bool = False, begin_date : datetime = None, end_date : datetime = None, session : requests.Session = None) -> list:
    if session is None:
        session = startSession()
    if series_id is None:
        if cod_mareografo not in codigos:
            raise("Codigo de mareógrafo no encontrado")
        series_id = codigos[cod_mareografo]
    if begin_date is None:
        data = downloadValoresGrafico(cod_mareografo, session = session)
    else:
        dt = timedelta(hours=config["dt_hours"]) if "dt_hours" in config else timedelta(hours=10)
        end_date = end_date if end_date is not None else datetime.now()
        current_date = begin_date
        lecturas = []
        dates = set()
        while current_date <= end_date:
            api_response = downloadValoresGrafico(cod_mareografo, current_date, session = session)
            current_date += dt
            for obs in api_response["lecturas"]:
                if obs["fecha"] not in dates:
                    dates.add(obs["fecha"])
                    lecturas.append(obs)
        data = {"lecturas": lecturas}
    obs = parseData(data = data, series_id = series_id)
    if test:
        logger.info("got %i observaciones for series_id %i, cod_mareografo: %s" % (len(obs), series_id, cod_mareografo))
        return obs
    # filter out nulls
    obs = [ o for o in obs if o["valor"] is not None]
    if not len(obs):
        logger.warning("No observations found. Skipping")
        return []
    try:
        result = uploadObs(obs, series_id)
    except Exception as e:
        logger.warning(e)
        result = []
    return result


def downloadParseAndUploadAll(
        test : bool = False, 
        begin_date : datetime = None, 
        end_date : datetime = None):
    session = startSession()
    results = []
    for cod_mareografo, series_id in codigos.items():
        results.append(
            downloadParseAndUpload(
                cod_mareografo, 
                series_id, 
                test = test,
                begin_date = begin_date,
                end_date = end_date,
                session = session))
    return results

def main():
    parser = argparse.ArgumentParser(description="Parse a file path argument.")

    # Add the argument for the file path
    parser.add_argument(
        '-o',
        '--output',                   # The argument name
        # type=valid_file_path,     # Custom type function to validate the file path
        help="Path to the output file"
    )
    parser.add_argument(
        '-c',
        '--cod_mareografo',
        default=None,
        help="Codigo mareografo, p. ej SFER"
    )
    parser.add_argument(
        '-t',
        '--test',
        action = "store_true",
        help="Testear, no actualizar a5"
    )
    parser.add_argument(
        '-b',
        '--begin_date',
        default=None,
        type=valid_date,
        help="Fecha inicio, p. ej 2024-01-01"
    )
    parser.add_argument(
        '-r',
        '--relative_begin_date',
        default=None,
        type=int,
        help="Fecha inicio relativa en días"
    )
    parser.add_argument(
        '-e',
        '--end_date',
        default=None,
        type=valid_date,
        help="Fecha fin, p. ej 2024-01-01"
    )
    
    # Parse the command-line arguments
    args = parser.parse_args()

    if args.begin_date is None and args.relative_begin_date is not None:
        args.begin_date = datetime.now()
        args.begin_date += timedelta(days = -1 * args.relative_begin_date)

    if args.cod_mareografo is not None:
        result = [ downloadParseAndUpload(args.cod_mareografo, test = args.test, begin_date = args.begin_date, end_date = args.end_date) ]
    else:
        result = downloadParseAndUploadAll(test = args.test, begin_date = args.begin_date, end_date = args.end_date)
    if args.output:
        f = open(args.output,"w")
        json.dump(result, f)
        f.close()
    else:
        json.dump(result, sys.stdout)

if __name__ == "__main__":
    main()

