# third party
# third party
import torch as th

# syft absolute
import syft as sy
from syft import serialize
from syft.core.common.uid import UID
from syft.core.node.common.action.save_object_action import SaveObjectAction
from syft.core.store.storeable_object import StorableObject


def test_save_object_action_serde() -> None:
    obj = th.tensor([1, 2, 3])
    addr = UID()

    storable = StorableObject(id=UID(), data=obj)
    msg = SaveObjectAction(obj=storable, address=addr)

    blob = serialize(msg)

    msg2 = sy.deserialize(blob=blob)

    assert (msg2.obj.data == msg.obj.data).all()

    # Tensors do not automatically get IDs anymore
    # assert msg2.obj.id == msg.obj.id
    assert msg2.address == msg.address
