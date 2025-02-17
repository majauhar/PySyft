# future
from __future__ import annotations

# stdlib
from typing import Any
from typing import Union

# third party
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey
from nacl.signing import VerifyKey

# relative
from ...common.serde.serializable import serializable
from .base import SyftBaseModel

SIGNING_KEY_FOR = "SigningKey for"


@serializable(recursive_serde=True)
class SyftVerifyKey(SyftBaseModel):
    verify_key: VerifyKey

    def __str__(self) -> str:
        return self.verify_key.encode(encoder=HexEncoder).decode("utf-8")

    @staticmethod
    def from_string(key_str: str) -> SyftVerifyKey:
        return SyftVerifyKey(verify_key=VerifyKey(bytes.fromhex(key_str)))

    @property
    def verify(self) -> str:
        return str(self)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SyftVerifyKey):
            return False
        return self.verify_key == other.verify_key

    def __repr__(self) -> str:
        return str(self)

    def __hash__(self) -> int:
        return self.verify_key.__hash__()


@serializable(recursive_serde=True)
class SyftSigningKey(SyftBaseModel):
    signing_key: SigningKey

    @property
    def verify_key(self) -> SyftVerifyKey:
        return SyftVerifyKey(verify_key=self.signing_key.verify_key)

    def __str__(self) -> str:
        return self.signing_key.encode(encoder=HexEncoder).decode("utf-8")

    @staticmethod
    def generate() -> SyftSigningKey:
        return SyftSigningKey(signing_key=SigningKey.generate())

    @staticmethod
    def from_string(key_str: str) -> SyftSigningKey:
        return SyftSigningKey(signing_key=SigningKey(bytes.fromhex(key_str)))

    def __repr__(self) -> str:
        return f"<{SIGNING_KEY_FOR}: {self.verify}>"

    @property
    def verify(self) -> str:
        return str(self.verify_key)

    def __hash__(self) -> int:
        return self.signing_key.__hash__()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SyftSigningKey):
            return False
        return self.signing_key == other.signing_key


SyftCredentials = Union[SyftVerifyKey, SyftSigningKey]


@serializable(recursive_serde=True)
class UserLoginCredentials(SyftBaseModel):

    email: str
    password: str
