from serverless_wsgi import handle_request

from token_bot.app import app


def handler(event, context):
    return handle_request(app, event, context)
