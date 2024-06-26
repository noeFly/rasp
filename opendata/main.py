from datetime import datetime
from os import getenv
from time import sleep
from urllib.request import urlretrieve

import pygsheets
from dotenv import load_dotenv

from alert import main as alert
from handle.xml import parse_xml
from handle.zip import unzip as unzip
from toolbox import get_file_list, make_dir, remove_dir, unix_timestamp, log, list2str

apikey: str
file_format_list: list
now: int


def unix() -> int:
    return round((datetime.now() - datetime(1970, 1, 1)).total_seconds())


def grab_data(data_id: str, file_format: str):
    make_dir(f'./data/cwa/{data_id}/')
    global now
    global file_format_list
    sub_file_name = file_format_list[f'{file_format}']
    log(0, 1, f'正在獲取資料 {data_id}')
    urlretrieve(
        url=f'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/{data_id}?Authorization={apikey}&format={file_format}',
        filename=f'data/cwa/{data_id}/{now}.{sub_file_name}')
    return [data_id, now]


def write_data(data) -> None:
    gc = pygsheets.authorize(service_file='./apikey.json')
    sheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1oOXiGIKsZaeckzPxZSUjAzNiLEC5CgEnqusLuRHMfao')
    worksheet = sheet.worksheet_by_title('opendata')
    worksheet.append_table(values=[unix(), data])


def main():
    remove_dir(['./data', './__pycache__', './handle/__pycache__'])
    load_dotenv('./.env')
    global apikey, file_format_list
    apikey = getenv('CWA_KEY')
    file_format_list = {'JSON': 'json', 'XML': 'xml', 'ZIP': 'zip'}
    while True:
        global now
        now = unix_timestamp()
        # O-A0002-002
        value: list = grab_data(data_id='O-A0002-002', file_format='ZIP')
        make_dir(f'./data/cwa/{value[0]}/{value[1]}/')
        unzip(file_path=f'./data/cwa/{value[0]}/', folder_name=f'{value[1]}/', file_name=f'{value[1]}.zip')
        xml_file = get_file_list(path=f'./data/cwa/{value[0]}/{value[1]}/')[-1]
        data = list2str(parse_xml(file_path=f'./data/cwa/{value[0]}/{value[1]}/{xml_file}', data_id='O-A0002-002'))
        write_data(data)
        sleep(5)
        ndata: list[float] = list[float](data.split(' ', -1))
        if float(ndata[0]) >= 5.0:
            alert(False)
        sleep(60)


if __name__ == '__main__':
    main()
