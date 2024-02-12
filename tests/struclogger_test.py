from __future__ import annotations

import datetime
import json

from pytest import LogCaptureFixture

from objeggtives import struclogger


def test_string_encoder_with_datetime() -> None:
    now = datetime.datetime.now()
    expected = now.strftime("%Y-%m-%dT%H:%M:%S%z")

    result = struclogger._StringEncoder().default(now)

    assert result == expected


def test_string_encoder_with_serializable_object() -> None:
    test_json = {"key": None}
    expected = '{"key": null}'

    result = json.dumps(test_json, cls=struclogger._StringEncoder)

    assert result == expected


def test_string_encoder_with_non_serializable_object() -> None:
    test_json = {"key": object()}
    object_str = str(test_json["key"])
    expected = f'{{"key": "{object_str}"}}'

    result = json.dumps(test_json, cls=struclogger._StringEncoder)

    assert result == expected


def test_struc_factory_with_caplop(caplog: LogCaptureFixture) -> None:
    struclogger.init_struclogger()
    logger = struclogger.get_logger("test_logger")
    logger.error("This is a test error message.")

    record = json.loads(caplog.records[0].json_formatted)  # type: ignore  # Custom attribute

    assert record["level"] == "ERROR"
    assert record["message"] == "This is a test error message."


def test_struc_factory_with_exception(caplog: LogCaptureFixture) -> None:
    struclogger.init_struclogger()
    logger = struclogger.get_logger("test_logger")

    try:
        raise ValueError("This is a test exception.")

    except ValueError:
        logger.exception("This is a test exception message.")

    record = json.loads(caplog.records[0].json_formatted)  # type: ignore  # Custom attribute

    assert record["level"] == "ERROR"
    assert record["message"] == "This is a test exception message."
    assert record["exception"] is not None
    assert record["traceback"] is not None
