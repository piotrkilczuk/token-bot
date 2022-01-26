from os import environ

from pendulum import now
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute
from pynamodb.models import Model

from token_bot.exceptions import TokenAlreadyAcquired, TokenNotAcquired, TokenNotYours


class Token(Model):
    class Meta:
        table_name = environ["USERS_TABLE"]

    name = UnicodeAttribute(hash_key=True)
    acquired_by = UnicodeAttribute(null=True)
    acquired_at = UTCDateTimeAttribute(null=True)

    def acquire(self, user_id: str):
        if self.acquired_by:
            raise TokenAlreadyAcquired()
        self.update([Token.acquired_at.set(now()), Token.acquired_by.set(user_id)])

    def release(self, user_id: str, force: bool = False):
        if not self.acquired_by:
            raise TokenNotAcquired()
        if self.acquired_by != user_id and not force:
            raise TokenNotYours()
        self.update([Token.acquired_at.set(None), Token.acquired_by.set(None)])
