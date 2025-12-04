import logging 

LOG_FILE = 'kU_academic_run.log'

def init_logger():
    
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%d/%m/%Y %I:%M:%S',
        filemode='w',
        encoding='utf-8'
    )
    logging.info(' New run started ')


def log_message(msg: str, level: str = 'info') -> None:
    
    if level == 'error':
        logging.error(msg)
    elif level == 'warning':
        logging.warning(msg)
    else:
        logging.info(msg)