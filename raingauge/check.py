from __future__ import unicode_literals

import os
import os.path
import argparse
import serial
import io
import time
from collections import namedtuple
from datetime import datetime
import ssl, smtplib
import subprocess
from six.moves import map

from .util import *


def main():
    args = get_args()

    conf = Config(args.config_file)
    setup_logging(conf.storage_dir, args.verbose or 0)

    package = collect_data(conf)
    files = store_data(conf, package)

    if conf.sdb_enabled:
        send_data(conf, package)

    if conf.mail_enabled:
        mail_data(conf, files)

DataPackage = namedtuple("DataPackage", ["status", "data", "timestamp", "station_id"])
FileOutput = namedtuple("FileOutput", ["status", "data"])


def write_cmd(ser, station_id, cmd, delay):
    line = "#%s#%s\r\n" % (station_id, cmd)
    logger.info("Sending %s" % line.strip())
    for c in bytes(line):
        ser.write(c)
        time.sleep(delay)


def collect_data(conf):
    """
    Sends a command to the rain collector and gathers the returned
    data.
    """
    logger.info("Opening %(port)s" % conf.serial)
    ser = serial.Serial(**conf.serial)
    sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser),
                           encoding="utf-8", errors="ignore",
                           newline=None, line_buffering=True)

    write_cmd(ser, conf.station_id, "rm", conf.serial_char_delay)

    end_marker = "+" + conf.station_id + "+"

    d = DataPackage([], [], datetime.now(), conf.station_id)

    logger.debug("Reading...")

    count = 0
    for line in map(unicode.strip, sio):
        count += 1
        logger.debug("got line: " + line)
        parts = line.split(";")
        if len(parts) == 1 and parts[0] == end_marker:
            logger.debug("finished")
            break
        elif len(parts) <= 5:
            d.status.append(line)
        else:
            d.data.append(parts)

    logger.info("Received %d lines" % count)

    return d


def store_data(conf, package):
    d = setup_dirs(conf, package)
    prefix = package.timestamp.strftime("%H%M%S-")
    status_file = os.path.join(d, prefix + "status.txt")
    data_file = os.path.join(d, prefix + "data.txt")

    if package.status:
        logger.info("Writing %s" % status_file)
        with open(status_file, "w") as f:
            for line in package.status:
                f.write(line + "\n")

    if package.data:
        logger.info("Writing %s" % data_file)
        with open(data_file, "w") as f:
            for row in package.data:
                f.write(";".join(row) + "\n")

    return FileOutput(status_file, data_file)

def output_dir(conf, date):
    return os.path.join(conf.storage_dir,
                        date.strftime("%Y"),
                        date.strftime("%m"),
                        date.strftime("%d"))


def setup_dirs(conf, package):
    d = output_dir(conf, package.timestamp)
    if not os.path.exists(d):
        logger.info("Making directory %s" % d)
        os.makedirs(d)
    return d


def get_sdb_conn(conf):
    import boto.sdb
    return boto.sdb.connect_to_region(conf.aws_region,
                                      aws_access_key_id=conf.aws_access_key_id,
                                      aws_secret_access_key=conf.aws_secret_access_key)


def ensure_domains(conf):
    logger.info("Checking domains")
    conn = get_sdb_conn(conf)
    domains = conn.get_all_domains()

    def ensure_domain(name):
        doms = list(filter(lambda d: d.name == name, domains))
        if len(doms) == 0:
            logger.info("Creating domain %s" % name)
            return conn.create_domain(name)
        return doms[0]

    data = ensure_domain(conf.sdb_domain)
    status = ensure_domain(conf.sdb_domain + "_status")

    return data, status


def find_last_entry(domain):
    logger.info("Checking for previously sent samples")
    q = "select * from %s where datetime is not null order by datetime desc" % domain.name
    rs = list(domain.select(q, max_items=1))
    return rs[0] if len(rs) > 0 else None


def fmt_localtime(dt):
    return dt.strftime("%Y%m%d-%H%M%S")


def get_make_name(timestamp):
    prefix = fmt_localtime(timestamp)
    def make_name(index):
        return "%s-%03d" % (prefix, index + 1)
    return make_name


def make_status_attributes(package):
    make_name = get_make_name(package.timestamp)
    collected = package.timestamp.isoformat()
    for i, line in enumerate(package.status):
        attrs = {
            "index": i,
            "line": line,
            "collected": collected,
            "station_id": package.station_id,
        }
        yield (make_name(i), attrs)


def get_row_time(row):
    try:
        return datetime.strptime(" ".join(row[:2]), "%d.%m.%y %H:%M:%S")
    except ValueError:
        return None


def parse_iso(s):
    try:
        return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


def make_data_attributes(package, last=None):
    make_name = get_make_name(package.timestamp)
    collected = package.timestamp.isoformat()
    last_time = parse_iso(last["datetime"]) if last else None
    for i, row in enumerate(package.data):
        dt = get_row_time(row)
        if last_time is None or dt > last_time:
            attrs = dict(("col_%d" % (j+1), c) for (j, c) in enumerate(row))
            attrs.update({
                "collected": collected,
                "index": i,
                "station_id": package.station_id,
            })
            if dt:
                attrs["datetime"] = dt.isoformat()
                if len(row) > 8:
                    attrs["amount"] = row[8].lstrip("+")

            yield (make_name(i), attrs)


def chunks(l, n):
    "Divide a list into even-sized chunks"
    for i in range(0, len(l), n):
        yield l[i:i+n]


def pluck(d, keys):
    return dict((k, d[k]) for k in keys)


BATCH_MAX = 25
def batch_put_attributes(dom, attrs):
    "SDB supports a maximum of 25 attributes per put"
    keys = sorted(attrs)
    for chunk in chunks(keys, BATCH_MAX):
        logger.info("Putting %d items to %s" % (len(chunk), dom.name))
        dom.batch_put_attributes(pluck(attrs, chunk))


def send_data(conf, package):
    data, status = ensure_domains(conf)

    status_attrs = dict(make_status_attributes(package))
    logger.info("Putting %d status items" % len(status_attrs))
    batch_put_attributes(status, status_attrs)

    last = find_last_entry(data)
    data_attrs = dict(make_data_attributes(package, last))
    logger.info("Putting %d data items" % len(data_attrs))
    batch_put_attributes(data, data_attrs)

def link_path(conf):
    return os.path.join(conf.storage_dir, "%s.sent" % conf.station_id)

def get_prev_link(conf):
    prev_link = link_path(conf)
    if os.path.exists(prev_link):
        logger.info("Previously sent file was %s" % os.path.realpath(prev_link))
    else:
        logger.info("No previous mail was sent.")
        prev_link = None
    return prev_link

def make_prev_link(conf, files):
    prev_link = link_path(conf)
    logger.info("Symlinking %s -> %s" % (files.data, prev_link))
    if os.path.exists(prev_link):
        os.remove(prev_link)
    os.symlink(files.data, prev_link)

def get_diff(filea, fileb):
    with open(filea) as a:
        existing = set(a)
        with open(fileb) as b:
            return "".join(line for line in b if line not in existing)

def mail_data(conf, files):
    prev_link = get_prev_link(conf)
    diff = get_diff(prev_link or "/dev/null", files.data)
    msg = "\n".join([
        "Subject: Rain gauge reading for %s" % conf.station_id,
        "From: %s" % conf.mail_username,
        "To: %s" % (conf.mail_to or conf.mail_username),
        "",
        "Station ID: %s" % conf.station_id,
        "",
        "---",
        "Status file:",
        open(files.status).read().strip(),
        "---",
        "",
        "New data:",
        "---",
        diff,
        "---",
        "",
        "Uptime:",
        subprocess.check_output(["uptime"], universal_newlines=True),
        "",
        "-- ",
        "checkrainpi",
        "https://github.com/rvl/checkrainpi",
    ])
    send_mail(conf, msg)
    make_prev_link(conf, files)

def send_mail(conf, msg):
    logger.info("Connecting to SMTP %s:%s" % (conf.mail_host, conf.mail_port))
    smtp = smtplib.SMTP(conf.mail_host, port=conf.mail_port)
    # context = ssl.create_default_context()
    # smtp.starttls(context=context)
    smtp.starttls()
    if conf.mail_username:
        smtp.login(conf.mail_username, conf.mail_password)

    to = conf.mail_to or conf.mail_username
    logger.info("Sending message to %s" % to)
    smtp.sendmail(conf.mail_username, [to], msg)
    logger.info("Sent")

def get_args():
    parser = argparse.ArgumentParser(description='Check rain collector and send results.')
    parser.add_argument('--conf', dest='config_file', metavar="FILE",
                        type=str, required=True,
                        help="Path to config file")
    # parser.add_argument("--collect", dest="collect_only",
    #                     type=bool, action="store_true",
    #                     help="Only read data, don't send")
    # parser.add_argument("--send", dest="send_only",
    #                     type=bool, action="store_true",
    #                     help="Only send data, don't collect")
    parser.add_argument('--verbose', '-v', action='count')
    return parser.parse_args()


if __name__ == "__main__":
    main()
