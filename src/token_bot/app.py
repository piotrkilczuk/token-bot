from os import environ
from typing import Callable

from flask import Flask, jsonify, make_response, request, abort

from token_bot import commands

app = Flask(__name__)


# Ensure all environment variables are set at import time
for var in {"API_KEY", "USERS_TABLE"}:
    if var not in environ:
        raise EnvironmentError(f"{var} must be set!")


def require_api_key(view: Callable):
    def inner(*args, **kwargs):
        if request.values.get("API_KEY") != environ.get("API_KEY", object()):
            abort(401)
        return view(*args, **kwargs)

    return inner


@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error="Not found!"), 404)


@app.route("/")
def health_check():
    # @TODO: can I access the DynamoDB table?
    return make_response(jsonify(status="OK"))


@app.route("/token", methods=["POST"])
def command_router():
    command, *params = request.form["text"].strip().split()
    user_id = request.form["user_id"]

    if not hasattr(commands, command):
        return make_response(
            jsonify(
                {
                    "response_type": "ephemeral",
                    "text": f"There is no such command: {command}",
                }
            )
        )

    command_callable = getattr(commands, command)

    try:
        response = command_callable(user_id, *params)
        return make_response(response.json)

    except TypeError as exc:
        return make_response(command_callable.__doc__)
