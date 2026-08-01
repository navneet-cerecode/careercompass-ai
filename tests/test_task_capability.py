from uuid import uuid4

from api.services.task_capability import TaskCapability


def test_task_capability_is_scoped_to_one_task():
    capability = TaskCapability(b"x" * 32)
    first = uuid4()
    second = uuid4()

    token = capability.issue(first)

    assert capability.verify(first, token) is True
    assert capability.verify(second, token) is False
    assert str(first) not in token
