from datetime import datetime
from os import path
import logging
from string import Formatter

import requests
from retrying import retry
from tinydb import TinyDB, Query
import ujson as json
requests.models.json = json #https://github.com/kennethreitz/requests/issues/1595


from prosper.common.prosper_config import get_config

HERE = path.abspath(path.dirname(__file__))
CONFIG_ABSPATH = path.join(HERE, 'crest_config.cfg')

CONFIG = get_config(CONFIG_ABSPATH)
DEFAULT_LOGGER = logging.getLogger('NULL')
DEFAULT_LOGGER.addHandler(logging.NullHandler())
USERAGENT = CONFIG.get('GLOBAL', 'useragent')

class CrestFormatter(Formatter):
    '''http://stackoverflow.com/questions/23407295/default-kwarg-values-for-pythons-str-format-method'''
    def __init__(self):
        Formatter.__init__(self)

    def get_value(self, key, args, kwds):
        if isinstance(key, str):
            try:
                return kwds[key]
            except KeyError:
                return key
        else:
            Formatter.get_value(key, args, kwds)

crest_format = CrestFormatter()

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

CREST_BASEURL = CONFIG.get('CREST', 'base_url')
#PAGE_URI = CONFIG.get('CREST', )
class CrestRequest(object):
    def __init__(self, endpoint_name, logger=DEFAULT_LOGGER):
        self.base_url = CREST_BASEURL
        self.endpoint_name = endpoint_name
        self.logger = logger
        try:
            self.endpoint_url = CONFIG.get('CREST', endpoint_name)
        except Exception as error_msg:
            self.logger.error(
                'unable to resolve endpoint_name' +
                'endpoint_name={0}'.format(endpoint_name) +
                'exception={0}'.format(error_msg)
            )
            raise error_msg
        #self.logger.debug(
        print(
            'CrestRequest.__init__' +
            '\r\tbase_url={0}'.format(self.base_url) +
            '\r\tendpoint_name={0}'.format(self.endpoint_name) +
            '\r\tendpoint_url={0}'.format(self.endpoint_url)
        )
        self.current_page = 0
        self.all_items = []
        self.fetch_time = ''

    def fetch_data(self, **kwargs):
        '''deal with grabbing all the data from a request endpoint'''
        print(kwargs)
        request_url = self.base_url + crest_format.format(self.endpoint_url, **kwargs)
        self.logger.info('fetching data from: ' + request_url)
        try:
            first_page = fetch_crest_page(
                request_url,
                logger=self.logger
            )
        except Exception as error_msg:
            self.logger.error(
                'unable to fetch page:' +
                '\r\turl={0}'.format(request_url) +
                '\r\texception={0}'.format(error_msg)
            )
            raise error_msg
        self.fetch_time = first_page['request_time']
        if 'items' in first_page: #TODO better test?
            self.all_items.extend(first_page['items'])
        else:
            self.all_items = first_page

        if 'pageCount' in first_page: #TODO better test?
            page_count = first_page['pageCount']
            if page_count != 1:
                self.logger.info('multiple pages to fetch: ' + str(first_page['pageCount']))
                page_num = 1
                while page_num < page_count:
                    page_num += 1
                    #page_url = request_url + PAGE_URI.format(page_number=page_num)
                    self.logger.info('fetching page number: ' + str(page_num))
                    try:
                        current_page = fetch_crest_page(
                            request_url,
                            page=page_num,
                            logger=self.logger
                        )
                    except Exception as error_msg:
                        self.logger.error(
                            'unable to fetch page:' +
                            '\r\turl={0}?page={1}'.format(request_url, page_num) +
                            '\r\texception={0}'.format(error_msg)
                        )
                        raise error_msg
                    self.all_items.extend(current_page['items'])

        return self.all_items


RETRY_TIME = CONFIG.get('GLOBAL', 'retry_time')
RETRY_COUNT = CONFIG.get('GLOBAL', 'retry_count')
@retry(
    wait_exponential_multiplier=1000,
    wait_exponential_max=RETRY_TIME,
    stop_max_attempt_number=RETRY_COUNT)
def fetch_crest_page(
        crest_url,
        page=None,
        useragent=USERAGENT,
        logger=DEFAULT_LOGGER
):
    '''fetch CREST address and return data'''
    response = None
    header = {
        'User-Agent': useragent
    }
    param = {}
    if page:
        param = {'page':page}
    logger.info('-- Fetching ' + crest_url)
    try:
        request = requests.get(
            crest_url,
            params=param,
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

    LOGGER = create_logger(
        'debug_crest_utilities',
        '.',
        None,
        'DEBUG'
    )

    CRESTOBJ = CrestRequest('solarsystems', logger=LOGGER)
    LOGGER.debug(CRESTOBJ.fetch_data(systemid=30000142))
