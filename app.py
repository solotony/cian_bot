import argparse
import logging
import os

if __name__ == '__main__':

    import settings

    def start_server(**kw):

        from web.app import create_app

        app = create_app()

        app.run(**kw)

    parser = argparse.ArgumentParser()

    parser.add_argument('--host', dest='host', default='', type=str,
                        action='store', help='Server IP address.')
    parser.add_argument('-p', '--port', dest='port', default='5000', type=int,
                        action='store', help='Server port.')
    parser.add_argument('-b', '--bot', dest='bot', default=1, type=int,
                        action='store', help='Bot instance that will run with the server.')

    cmd_args = vars(parser.parse_args())

    bot_instance = cmd_args.pop('bot')

    if bot_instance == 2:

        logging.warning("Run second bot instance.")

        settings.second_bot_set()

    start_server(**cmd_args)
