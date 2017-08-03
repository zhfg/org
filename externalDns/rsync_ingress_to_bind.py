#!/bin/env python
#-*- coding: utf8
from kubernetes import client, config
from sqlalchemy import create_engine, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, BigInteger
from sqlalchemy.orm import sessionmaker
import logging


Base = declarative_base()

#{'api_version': None,
# 'kind': None,
# 'metadata': {'annotations': {u'kubectl.kubernetes.io/last-applied-configuration': '{"apiVersion":"extensions/v1beta1","kind":"Ingress","metadata":{"annotations":{},"name":"monitoring-influxdb","namespace":"kube-system"},"spec":{"rules":[{"host":"influxdb.cloud.ixicar.cn","http":{"paths":[{"backend":{"serviceName":"monitoring-influxdb","servicePort":8088},"path":"/"}]}}]}}\n'},
#              'cluster_name': None,
#              'creation_timestamp': datetime.datetime(2017, 7, 27, 11, 9, 56, tzinfo=tzutc()),
#              'deletion_grace_period_seconds': None,
#              'deletion_timestamp': None,
#              'finalizers': None,
#              'generate_name': None,
#              'generation': 3,
#              'labels': None,
#              'name': 'monitoring-influxdb',
#              'namespace': 'kube-system',
#              'owner_references': None,
#              'resource_version': '3432768',
#              'self_link': '/apis/extensions/v1beta1/namespaces/kube-system/ingresses/monitoring-influxdb',
#              'uid': '1f5c6ace-72bc-11e7-b94b-0017fa009d15'},
# 'spec': {'backend': None,
#          'rules': [{'host': 'influxdb.cloud.ixicar.cn',
#                     'http': {'paths': [{'backend': {'service_name': 'monitoring-influxdb',
#                                                     'service_port': '8088'},
#                                         'path': '/'}]}}],
#          'tls': None},
# 'status': {'load_balancer': {'ingress': [{'hostname': None,
#                                           'ip': '10.20.0.7'}]}}}

class DnsRecord(Base):

#+-------------+------------------+------+-----+---------+----------------+
#| Field       | Type             | Null | Key | Default | Extra          |
#+-------------+------------------+------+-----+---------+----------------+
#| id          | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
#| zone        | varchar(255)     | NO   | MUL | NULL    |                |
#| host        | varchar(255)     | NO   | MUL | @       |                |
#| type        | varchar(255)     | NO   | MUL | NULL    |                |
#| data        | text             | YES  |     | NULL    |                |
#| ttl         | int(11)          | NO   |     | 86400   |                |
#| mx_priority | int(11)          | YES  |     | NULL    |                |
#| refresh     | int(11)          | YES  |     | NULL    |                |
#| retry       | int(11)          | YES  |     | NULL    |                |
#| expire      | int(11)          | YES  |     | NULL    |                |
#| minimum     | int(11)          | YES  |     | NULL    |                |
#| serial      | bigint(20)       | YES  |     | NULL    |                |
#| resp_person | varchar(255)     | YES  |     | NULL    |                |
#| primary_ns  | varchar(255)     | YES  |     | NULL    |                |
#| view        | varchar(20)      | YES  |     | NULL    |                |
#| region      | varchar(255)     | YES  |     | NULL    |                |
#+-------------+------------------+------+-----+---------+----------------+

    __tablename__ = 'dns_records'
    
    id = Column(Integer, primary_key=True)
    zone = Column(String(255))
    host = Column(String(255))
    type = Column(String(255))
    data = Column(Text)
    ttl = Column(Integer)
    mx_priority = Column(Integer)
    refresh = Column(Integer)
    retry = Column(Integer)
    expire = Column(Integer)
    minimum = Column(Integer)
    serial = Column(BigInteger)
    resp_person = Column(String(255))
    primary_ns = Column(String(255))
    view = Column(String(20))
    region = Column(String(255))


engine = create_engine('mysql+pymysql://bind_w:bind_w@10.20.0.21/bind9_dlz')
Session = sessionmaker(bind=engine)
session = Session()
region = "k8s"
dns_data = '42.159.246.234'

def getIngress():
    config.load_kube_config()
    ingress = []
    v1 = client.ExtensionsV1beta1Api()
    ret = v1.list_ingress_for_all_namespaces(watch=False)
    for i in ret.items:
        for rule in i.spec.rules:
           ingress.append(rule.host) 
    return ingress


def parseIngress(ing):
    
    hostBeg = 0
    hostEnd = ing.find('.')
    host = ing[hostBeg:hostEnd]
    zone = ing[hostEnd+1:len(ing)]
    return host,zone

def AddZone(zone):
    pass


def AddHost(host, zone, data='42.159.205.160'):
    logging.info("Recived a request to add host %s for zone %s" % (host, zone))
    logging.info("Check if %s.%s existing" % (host, zone))
    records = session.query(DnsRecord).filter(and_(DnsRecord.host==host, DnsRecord.zone==zone,DnsRecord.region==region))
    record_count = records.count()
    if record_count == 0:
        logging.info("domain %s.%s is not existing, adding it" % (host,zone))
        domain = DnsRecord(host=host, zone=zone, type='A', view="external", region=region, ttl=180, data=dns_data)
        try:
            session.add(domain)
        except Exectipon,e:
            logging.error("Error: %s", e)
        finally:
            logging.info("domain %s.%s added" % (host, zone))
    else:
        for record in records:
            record.data=dns_data
    session.commit()

def main():
    ings = getIngress()
    logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='/tmp/ingresstodns.log',
                filemode='a')
    for ing in ings:
        host, zone = parseIngress(ing)
        logging.info("Find ingress host %s for domain %s" % (host, zone))
        
        domain = ".".join((host, zone))
        AddHost(host,zone)

if __name__ == '__main__':
    main()
    session.close()
