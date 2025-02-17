# stdlib
from enum import Enum
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

# third party
from bcrypt import checkpw
from bcrypt import gensalt
from bcrypt import hashpw
import pydantic
from pydantic.networks import EmailStr

# relative
from ....core.node.common.node_table.syft_object import SYFT_OBJECT_VERSION_1
from ....core.node.common.node_table.syft_object import SyftObject
from ....core.node.common.node_table.syft_object import transform
from ...common.serde.serializable import serializable
from ...common.uid import UID
from .credentials import SyftSigningKey
from .credentials import SyftVerifyKey
from .transforms import drop
from .transforms import keep
from .transforms import make_set_default


class ServiceRoleCapability(Enum):
    CAN_MAKE_DATA_REQUESTS = 1
    CAN_TRIAGE_DATA_REQUESTS = 2
    CAN_MANAGE_PRIVACY_BUDGET = 4
    CAN_CREATE_USERS = 8
    CAN_MANAGE_USERS = 16
    CAN_EDIT_ROLES = 32
    CAN_MANAGE_INFRASTRUCTURE = 64
    CAN_UPLOAD_DATA = 128
    CAN_UPLOAD_LEGAL_DOCUMENT = 256
    CAN_EDIT_DOMAIN_SETTINGS = 512


@serializable(recursive_serde=True)
class ServiceRole(Enum):
    GUEST = 1


@serializable(recursive_serde=True)
class User(SyftObject):
    # version
    __canonical_name__ = "User"
    __version__ = SYFT_OBJECT_VERSION_1

    @pydantic.validator("email", pre=True, always=True)
    def make_email(cls, v: EmailStr) -> EmailStr:
        return EmailStr(v)

    # fields
    email: Optional[EmailStr]
    name: Optional[str]
    hashed_password: Optional[str]
    salt: Optional[str]
    signing_key: Optional[SyftSigningKey]
    verify_key: Optional[SyftVerifyKey]
    role: Optional[ServiceRole]
    institution: Optional[str]
    website: Optional[str] = None
    created_at: Optional[str]

    # serde / storage rules
    __attr_state__ = [
        "email",
        "name",
        "hashed_password",
        "salt",
        "signing_key",
        "verify_key",
        "role",
        "created_at",
    ]
    __attr_searchable__ = ["name", "email"]
    __attr_unique__ = ["email", "signing_key", "verify_key"]


def default_role(role: ServiceRole) -> Callable:
    return make_set_default(key="role", value=role)


def hash_password(_self: Any, output: Dict) -> Dict:
    if output["password"] is not None and (
        output["password"] == output["password_verify"]
    ):
        salt, hashed = __salt_and_hash_password(output["password"], 12)
        output["hashed_password"] = hashed
        output["salt"] = salt
    return output


def generate_key(_self: Any, output: Dict) -> Dict:
    signing_key = SyftSigningKey.generate()
    output["signing_key"] = signing_key
    output["verify_key"] = signing_key.verify_key
    return output


def generate_id(_self: Any, output: Dict) -> Dict:
    if not isinstance(output["id"], UID):
        output["id"] = UID()
    return output


def __salt_and_hash_password(password: str, rounds: int) -> Tuple[str, str]:
    bytes_pass = password.encode("UTF-8")
    salt = gensalt(rounds=rounds)
    hashed = hashpw(bytes_pass, salt)
    hashed_bytes = hashed.decode("UTF-8")
    salt_bytes = salt.decode("UTF-8")
    return salt_bytes, hashed_bytes


def check_pwd(password: str, hashed_password: str) -> bool:
    return checkpw(
        password=password.encode("utf-8"),
        hashed_password=hashed_password.encode("utf-8"),
    )


def validate_email(_self: Any, output: Dict) -> Dict:
    if output["email"] is not None:
        output["email"] = EmailStr(output["email"])
        EmailStr.validate(output["email"])
    return output


@serializable(recursive_serde=True)
class UserUpdate(SyftObject):
    __canonical_name__ = "UserUpdate"
    __version__ = SYFT_OBJECT_VERSION_1

    id: Optional[UID] = None

    @pydantic.validator("email", pre=True, always=True)
    def make_email(cls, v: EmailStr) -> EmailStr:
        return EmailStr(v) if v is not None else v

    email: Optional[EmailStr]
    name: Optional[str]
    role: Optional[ServiceRole] = None  # make sure role cant be set without uid
    password: Optional[str] = None
    password_verify: Optional[str] = None
    verify_key: Optional[SyftVerifyKey] = None
    institution: Optional[str] = None
    website: Optional[str] = None


@serializable(recursive_serde=True)
class UserCreate(UserUpdate):
    __canonical_name__ = "UserCreate"
    __version__ = SYFT_OBJECT_VERSION_1

    email: EmailStr
    name: str
    role: Optional[ServiceRole] = None  # make sure role cant be set without uid
    password: str
    password_verify: str
    verify_key: Optional[SyftVerifyKey] = None
    institution: Optional[str] = None
    website: Optional[str] = None


class UserView(UserUpdate):
    __canonical_name__ = "UserView"
    __version__ = SYFT_OBJECT_VERSION_1


@transform(UserUpdate, User)
def user_update_to_user() -> List[Callable]:
    return [
        validate_email,
        hash_password,
        drop(["password", "password_verify"]),
    ]


@transform(UserCreate, User)
def user_create_to_user() -> List[Callable]:
    return [
        generate_id,
        validate_email,
        hash_password,
        generate_key,
        default_role(ServiceRole.GUEST),
        drop(["password", "password_verify"]),
    ]


@transform(User, UserView)
def user_to_view_user() -> List[Callable]:
    return [keep(["id", "email", "name", "role"])]


@serializable(recursive_serde=True)
class UserPrivateKey(SyftObject):
    __canonical_name__ = "UserPrivateKey"
    __version__ = SYFT_OBJECT_VERSION_1

    email: str
    signing_key: SyftSigningKey


@transform(User, UserPrivateKey)
def user_to_user_verify() -> List[Callable]:
    return [keep(["email", "signing_key"])]
