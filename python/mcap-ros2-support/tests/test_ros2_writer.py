from io import BytesIO

import json
import base64

from mcap_ros2.decoder import DecoderFactory
from mcap_ros2.writer import Writer as Ros2Writer

from mcap.reader import make_reader


def read_ros2_messages(stream: BytesIO):
    reader = make_reader(stream, decoder_factories=[DecoderFactory()])
    return reader.iter_decoded_messages()


def test_write_messages():
    output = BytesIO()
    ros_writer = Ros2Writer(output=output)
    schema = ros_writer.register_msgdef("test_msgs/TestData", "string a\nint32 b")
    for i in range(0, 10):
        ros_writer.write_message(
            topic="/test",
            schema=schema,
            message={"a": f"string message {i}", "b": i},
            log_time=i,
            publish_time=i,
            sequence=i,
        )
    ros_writer.finish()

    output.seek(0)
    for index, msg in enumerate(read_ros2_messages(output)):
        assert msg.channel.topic == "/test"
        assert msg.schema.name == "test_msgs/TestData"
        assert msg.decoded_message.a == f"string message {index}"
        assert msg.decoded_message.b == index
        assert msg.message.log_time == index
        assert msg.message.publish_time == index
        assert msg.message.sequence == index


def test_write_std_msgs_empty_messages():
    output = BytesIO()
    ros_writer = Ros2Writer(output=output)
    schema = ros_writer.register_msgdef("std_msgs/msg/Empty", "")
    for i in range(0, 10):
        ros_writer.write_message(
            topic="/test",
            schema=schema,
            message={},
            log_time=i,
            publish_time=i,
            sequence=i,
        )
    ros_writer.finish()

    output.seek(0)
    for index, msg in enumerate(read_ros2_messages(output)):
        assert msg.channel.topic == "/test"
        assert msg.schema.name == "std_msgs/msg/Empty"
        assert msg.message.log_time == index
        assert msg.message.publish_time == index
        assert msg.message.sequence == index


def test_write_bytes_object_from_json_deserialization():
    output = BytesIO()
    ros_writer = Ros2Writer(output=output)
    schema = ros_writer.register_msgdef("test_msgs/BytesMsg", "uint8[] data")

    sample_bytes = bytes([0x77, 0x67, 0x65, 0x80])
    to_serialize_dict = {"data": base64.b64encode(sample_bytes).decode("utf-8")}
    sample_json = json.dumps(to_serialize_dict)
    deserialized_dict = json.loads(sample_json)

    for i in range(0, 10):
        ros_writer.write_message(
            topic="/test",
            schema=schema,
            message=deserialized_dict,
            log_time=i,
            publish_time=i,
            sequence=i,
        )
    ros_writer.finish()

    output.seek(0)
    for index, msg in enumerate(read_ros2_messages(output)):
        assert msg.channel.topic == "/test"
        assert msg.schema.name == "test_msgs/BytesMsg"
        assert msg.decoded_message.data == sample_bytes
        assert msg.message.log_time == index
        assert msg.message.publish_time == index
        assert msg.message.sequence == index
