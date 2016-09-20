import logging
import sys
import os

def get_logger(name='paas.log'):
    logging.basicConfig(filename=os.path.join(os.environ['PAAS_LOGDIR'], name),
                        level=logging.DEBUG,
                        format = '[%(asctime)s] [%(levelname)s] %(message)s')
    log_obj = logging.getLogger(name)

    return log_obj

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)

    level = sys.argv[1]
    msg = sys.argv[2]

    log = get_logger()

    if level.lower() == 'debug':
        log.debug(msg)
    if level.lower() == 'info':
        log.info(msg)
    if level.lower() == 'warning':
        log.warning(msg)
    if level.lower() == 'error':
        log.error(msg)
    if level.lower() == 'critical':
        log.critical(msg)

    sys.exit(0)


