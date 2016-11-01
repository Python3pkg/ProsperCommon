from datetime import datetime
from os import path
import logging

import requests
from retrying import retry
from tinyDB import TinyDB, Query
import ujson as json
requests.models.json = json #https://github.com/kennethreitz/requests/issues/1595


from prosper.common.prosper_config import get_config

HERE = path.abspath(path.dirname(__file__))
CONFIG_ABSPATH = path.join(HERE, 'crest_config.cfg')

CONFIG = get_config(CONFIG_ABSPATH)
DEFAULT_LOGGER = logging.getLogger('NULL')
DEFAULT_LOGGER.addHandler(logging.NullHandler())
USERAGENT = CONFIG.get('GLOBAL', 'useragent')
def build_sde_types(
        get_npc_trade_info=False,
        user_agent_override=None,
        config_override=None,
        logger=DEFAULT_LOGGER
):
    '''fetch all data from CREST to build SDE
    returns: json (for tinydb)
    return_json = {
        typeid:{
            id:int,
            name:str,
            volume:float,
            groupid:int,
            groupname:str
            categoryid:int,
            categoryname:str,
            cache_datetime:datetime,
            is_npc:bool,
            prosper_filter:bool #TODO
        }
    }
    '''
    useragent = USERAGENT
    if user_agent_override:
        useragent = user_agent_override

    config = CONFIG
    if config_override:
        config = config_override


def build_sde_map(
        user_agent_override=None,
        config_override=None,
        logger=DEFAULT_LOGGER
):
    '''fetch all map endpoint data from CREST
    returns: json (for tinydb)
    return_json = {
        solarsystemid:{
            id:int,
            name:str,
            security:float,
            constellationid:int,
            constellationname:str,
            regionid:int,
            regionname:str,
            cache_datetime:datetime,
            is_npc:bool,
            is_sov:bool,
            is_fw:bool,
            connected:[
                int(solarsystemid),
                int(solarsystemid)
            ],
            stations:[#TODO
                int(stationid)
            ]
            x:float,
            y:float,
            z:float
        }
    }
    '''
    useragent = USERAGENT
    if user_agent_override:
        useragent = user_agent_override

    config = CONFIG
    if config_override:
        config = config_override

RETRY_TIME = CONFIG.get('GLOBAL', 'retry_time')
RETRY_COUNT = CONFIG.get('GLOBAL', 'retry_count')
@retry(
    wait_exponential_multiplier=1000,
    wait_exponential_max=RETRY_TIME,
    stop_max_attempt_number=RETRY_COUNT)
def fetch_crest_page(
        crest_url,
        useragent=USERAGENT,
        logger=DEFAULT_LOGGER
):
    '''fetch CREST address and return data'''
    response = None
    header = {
        'User-Agent': useragent
    }
    logger.info('-- Fetching ' + crest_url)
    try:
        request = requests.get(
            crest_url,
            headers=header
        )
    except Exception as error_msg:
        logger.error(
            'EXCEPTION: request failed ' +
            '\r\texception={0} '.format(error_msg) +
            '\r\turl={0} '.format(crest_url)
        )
        raise error_msg #exception triggers @retry

    if request.status_code == requests.codes.ok:
        try:
            response = request.json()
        except Exception as error_msg:
            logger.error(
                'EXCEPTION: payload error ' +
                '\r\texception={0} '.format(error_msg) +
                '\r\turl={0} '.format(crest_url)
            )
            raise error_msg #exception triggers @retry
    else:
        logger.error(
            'EXCEPTION: bad status code ' +
            '\r\texception={0} '.format(request.status_code) +
            '\r\turl={0} '.format(crest_url)
        )
        raise Exception('BAD STATUS CODE: ' + str(requests.status_code))

    try:
        #add request_time on to the response object for record keeping
        tmp_date = request.headers['Date']
        fetch_time = datetime.strptime(tmp_date, '%a, %d %b %Y %H:%M:%S %Z')
        response['request_time'] = fetch_time.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as error_msg:
        logger.warning(
            'WARNING: unable to get date from request object' +
            '\r\texception={0}'.format(error_msg)
        )
        logger.debug(request.headers)

    return response

def update_tinydb(
        data_payload,
        tinydb_handle,
        force_overwrite=False,
        logger=DEFAULT_LOGGER
):
    '''push data to tinydb.  update/overwrite'''
    pass

if __name__ == '__main__':
    from prosper.common.prosper_logging import create_logger

