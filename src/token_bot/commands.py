from functools import wraps
from typing import Callable

from flask import jsonify

from token_bot.exceptions import TokenAlreadyAcquired, TokenNotYours, TokenNotAcquired
from token_bot.models import Token


class CommandReply:
    _ephemeral: bool
    _text: str

    def __init__(self, text: str, ephemeral: bool = True):
        self._text = text
        self._ephemeral = ephemeral

    @property
    def json(self):
        return jsonify(
            response_type="ephemeral" if self._ephemeral else "in_channel",
            text=self._text,
        )


def requires_token(
    command: Callable[[str, Token], CommandReply]
) -> Callable[[str, str], CommandReply]:
    @wraps(command)
    def inner(user_id: str, name: str) -> CommandReply:
        try:
            token = Token.get(name)
            return command(user_id, token)

        except Token.DoesNotExist:
            return CommandReply(
                f"Token {name} does not exist. Use `/token create {name}` to create it."
            )

    return inner


def create(user_id: str, name: str) -> CommandReply:
    """
    `/token create [name]` - Creates a new token. Does nothing if a token with this name already exists.
    """

    try:
        Token.get(name)
        return CommandReply(f"Token {name} already exists.")

    except Token.DoesNotExist:
        token = Token(name)
        token.save()
        return CommandReply(f"<@{user_id}> just created token {name}.", ephemeral=False)


@requires_token
def acquire(user_id: str, token: Token) -> CommandReply:
    """
    `/token acquire [name]` - Acquires an existing token. Fails if the token is already acquired or does not exist.
    """

    try:
        token.acquire(user_id)
        return CommandReply(
            f"Token {token.name} is now in possession of <@{user_id}>.", ephemeral=False
        )

    except TokenAlreadyAcquired:
        if token.acquired_by == user_id:
            return CommandReply(f"Token {token.name} is already in your possession.")
        return CommandReply(
            f"Token {token.name} is already in possession of <@{token.acquired_by}>."
        )


@requires_token
def release(user_id: str, token: Token) -> CommandReply:
    """
    `/token release [name]` - Releases a token. Fails if the token does not exist or is in possession of somebody else.
    """
    try:
        token.release(user_id)
        return CommandReply(f"Token {token.name} is now free to take.", ephemeral=False)

    except TokenNotAcquired:
        return CommandReply(
            f"Token {token.name} is not currently in anyone's possession."
        )

    except TokenNotYours:
        return CommandReply(
            f"Token {token.name} is currently in <@{token.acquired_by}>'s possession."
        )


@requires_token
def kick(user_id: str, token: Token) -> CommandReply:
    """
    `/token kick [name]` - Release a token that is presently in someone else's possession. Use sparingly.
    """
    try:
        token.release(user_id, force=True)
        return CommandReply(
            f"Token {token.name} (in  <@{token.acquired_by}>'s possession) "
            f"has been forcefully released by <@{user_id}> and is now free to take.",
            ephemeral=False,
        )

    except TokenNotAcquired:
        return CommandReply(
            f"Token {token.name} is not currently in anyone's possession."
        )


@requires_token
def show(user_id: str, token: Token) -> CommandReply:
    """
    `/token show [name]` - Show token status.
    """
    status = (
        f"in <@{token.acquired_by}>'s possession"
        if token.acquired_by
        else "free to take"
    )
    return CommandReply(f"Token {token.name} is {status}")


def help(_: str):
    """
    `/token help`
    """
    return CommandReply(
        "\n".join(
            command.__doc__.strip()
            for command in [create, acquire, release, kick, show]
        )
    )
