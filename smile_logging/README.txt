Installation
***********************
1. Move the file smile_logging.py in [OpenERPServerHome]/bin/
2. Add the following lines in the file [OpenERPServerHome]/bin/netsvc.py at the end of the method init_logger()
    if tools.config.get('log2db', ''):
        from smile_logging import SmileDBHandler
        handler = SmileDBHandler()
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, tools.config['log2db'].upper()))
3. Add the key 'log2db' in the configuration file