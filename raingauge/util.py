import os
import os.path
import logging
import logging.handlers
from six.moves.configparser import ConfigParser
import boto.sdb

__all__ = ["setup_logging", "logger", "Config", "get_sdb_conn"]

logger = logging.getLogger("checkrainpi")


def get_sdb_conn(conf):
    return boto.sdb.connect_to_region(conf.aws_region,
                                      aws_access_key_id=conf.aws_access_key_id,
                                      aws_secret_access_key=conf.aws_secret_access_key)


class Config(object):
    def __init__(self, config_file):
        config = ConfigParser()
        config.read(config_file)

        self.serial = {
            "port": config.get('device', 'port'),
            "baudrate": config.getint('device', 'baudrate'),
            "parity": config.get('device', 'parity'),
            "bytesize": config.getint('device', 'bytesize'),
            "stopbits": config.getint('device', 'stopbits'),
        }

        self.storage_dir = config.get("storage", "dir")
        self.sdb_domain = config.get("simpledb", "domain")

        self.aws_access_key_id = config.get("aws", "access_key_id")
        self.aws_secret_access_key = config.get("aws", "secret_access_key")
        self.aws_region = config.get("aws", "region")


def setup_logging(storage_dir, verbose):
    loglevel = 'DEBUG' if verbose >= 2 else 'INFO'
    logger.setLevel(loglevel)

    fmt = logging.Formatter(fmt='%(asctime)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    ch = logging.StreamHandler()
    ch.setLevel(loglevel)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    if not os.path.exists(storage_dir):
        logger.info("Making directory %s" % storage_dir)
        os.makedirs(storage_dir)

    fh = logging.FileHandler(os.path.join(storage_dir, "checkrain.log"))
    fh.setLevel(loglevel)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch.setLevel(logging.WARNING if verbose == 0 else loglevel)

    logger.info("Started")
    logger.debug("Verbosity = %d" % verbose)
