import sys
import importlib
import logging

log = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(name)-12s %(message)s', level=logging.INFO)

    if len(sys.argv) < 2:
        print('$> python serve.py {service_name}')

    log.info(f'serving "{sys.argv[1]}" service')

    service = importlib.import_module(f'{sys.argv[1]}.service')
    service.serve()
