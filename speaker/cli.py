# -*- coding: utf-8 -*-

"""Console script for rps."""

import click
from .log import get_log
from .routermq import RouterMQ
from .speaker_spon import Speaker_Spon
from .speaker_bosch import Speaker_Bosch
from .speaker_adam import Speaker_Adam
from .api import Api
import asyncio


def validate_url(ctx, param, value):
    try:
        return value
    except ValueError:
        raise click.BadParameter('url need to be format: tcp://ipv4:port')


@click.command()
@click.option('--svr_type', default='spon',
              envvar='SVR_TYPE',
              help='Speaker Server Device Type, ENV: SVR_TYPE, \
              option: spon|bosch|adam etc')
@click.option('--spk_svr', default='tcp://localhost:2048',
              callback=validate_url,
              envvar='SPK_SVR',
              help='Speaker Server URL, \n \
              ENV: SPK_SVR, default: tcp://localhost:2048')
@click.option('--release_time', default=20,
              envvar='RELEASE_TIME',
              help='Release time for action, default=20, ENV: RELEASE_TIME')
@click.option('--amqp', default='amqp://guest:guest@rabbit:5672//',
              callback=validate_url,
              envvar='SVC_AMQP',
              help='Amqp url, also ENV: SVC_AMQP')
@click.option('--port', default=80,
              envvar='SVC_PORT',
              help='Api port, default=80, ENV: SVC_PORT')
@click.option('--qid', default=0,
              envvar='SVC_QID',
              help='ID for amqp queue name, default=0, ENV: SVC_QID')
@click.option('--debug', is_flag=True)
@click.option('--user', default='admin',
              envvar='SVR_USER',
              help='User name for speaker server, \
              ENV: SVR_USER')
@click.option('--passwd', default='admin',
              envvar='SVR_PASSWD',
              help='User passwd for speaker server, \
              ENV: SVR_PASSWD')
def main(svr_type, spk_svr, release_time, amqp, port, qid, debug,
         user, passwd):
    """Publisher for PM-1 with IPP protocol"""

    click.echo("See more documentation at http://www.mingvale.com")

    info = {
        'server type': svr_type,
        'server url': spk_svr,
        'release time': release_time,
        'api_port': port,
        'amqp': amqp,
    }
    log = get_log(debug)
    log.info('Basic Information: {}'.format(info))

    loop = asyncio.get_event_loop()
    loop.set_debug(0)

    # main process
    try:
        _svr_type = svr_type.upper()
        if _svr_type == 'SPON':
            log.info('Server type: Spon')
            site = Speaker_Spon(loop, spk_svr, release_time)
        elif _svr_type == 'BOSCH':
            log.info('Server type: Bosch')
            site = Speaker_Bosch(loop, spk_svr, release_time,
                                 user, passwd)
        elif _svr_type == 'ADAM':
            log.info('Server type: Adam-6017')
            site = Speaker_Adam(loop, spk_svr, release_time)
        else:
            log.warn('Undefined server type, use default.')
            site = Speaker_Spon(loop, spk_svr, release_time)
        router = RouterMQ(outgoing_key='Alarms.speaker',
                          routing_keys=['Actions.speaker'],
                          queue_name='speaker_'+str(qid),
                          url=amqp)
        router.set_callback(site.got_command)
        site.set_publish(router.publish)
        api = Api(loop=loop, port=port, site=site, amqp=router)
        site.start()
        amqp_task = loop.create_task(router.reconnector())
        api.start()
        loop.run_forever()
    except KeyboardInterrupt:
        if amqp_task:
            amqp_task.cancel()
            loop.run_until_complete(amqp_task)
        site.stop()
    finally:
        loop.stop()
        loop.close()
