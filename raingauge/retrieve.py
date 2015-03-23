import argparse
import sys
import logging

from .util import logger, get_sdb_conn, Config


def main():
    args = get_args()
    setup_logging(args)
    conf = Config(args.config_file)

    retrieve(conf, args.outfile)


def retrieve(conf, outfile):
    logger.info("Checking domains")
    conn = get_sdb_conn(conf)

    try:
        domain = conn.get_domain(conf.sdb_domain)
    except:
        domain = None

    if domain:
        print_domain(domain, outfile)
    else:
        sys.stdout.write("Domain %s doesn't exist" % conf.sdb_domain)
        sys.exit(1)


def print_domain(domain, outf):
    result = domain.select("select * from %s where datetime is not null order by datetime" % domain.name)
    for smp in result:
        outf.write("%(datetime)s\t%(amount)s\n" % smp)


def get_args():
    parser = argparse.ArgumentParser(description='Retrieve previously stored results.')
    parser.add_argument('--conf', dest='config_file', metavar="FILE",
                        type=str, required=True,
                        help="Path to config file")
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout)
    parser.add_argument('--verbose', '-v', action='count', default=0)
    return parser.parse_args()


def setup_logging(args):
    if args.verbose == 0:
        loglevel = logging.WARNING
    elif args.verbose == 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.DEBUG

    logging.basicConfig(format="%(message)s", level=loglevel)


if __name__ == "__main__":
    main()
