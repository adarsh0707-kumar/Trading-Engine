#include "network/Protocol.hpp"
#include "serialization/JsonSerializer.hpp"
#include "serialization/Message.hpp"

#include <cassert>
#include <iostream>
#include <string>
#include <vector>

using namespace trading::network;
using namespace trading::serialization;

static void test_message_round_trip()
{
    Message original;

    original.type =
        MessageType::TRADE;

    original.requestId =
        "req-42";

    original.timestamp =
        "2026-09-08T18:00:00Z";

    original.payload =
        "BTCUSD trade price=100 quantity=5";

    const std::string json =
        JsonSerializer::serialize(original);

    const Message restored =
        JsonSerializer::deserialize(json);

    assert(restored == original);
}

static void test_protocol_frame()
{
    const std::string payload =
        "{\"type\":\"TRADE\"}";

    const std::vector<std::uint8_t> frame =
        Protocol::frame(payload);

    std::vector<std::uint8_t> buffer =
        frame;

    std::string restored;

    assert(
        Protocol::extractFrame(
            buffer,
            restored));

    assert(restored == payload);
    assert(buffer.empty());
}

static void test_partial_frame()
{
    const std::string payload =
        "hello";

    const auto frame =
        Protocol::frame(payload);

    std::vector<std::uint8_t> buffer(
        frame.begin(),
        frame.begin() + 3);

    std::string restored;

    assert(
        !Protocol::extractFrame(
            buffer,
            restored));

    buffer.insert(
        buffer.end(),
        frame.begin() + 3,
        frame.end());

    assert(
        Protocol::extractFrame(
            buffer,
            restored));

    assert(restored == payload);
}

static void test_multiple_frames()
{
    const auto first =
        Protocol::frame("first");

    const auto second =
        Protocol::frame("second");

    std::vector<std::uint8_t> buffer;

    buffer.insert(
        buffer.end(),
        first.begin(),
        first.end());

    buffer.insert(
        buffer.end(),
        second.begin(),
        second.end());

    std::string payload;

    assert(
        Protocol::extractFrame(
            buffer,
            payload));

    assert(payload == "first");

    assert(
        Protocol::extractFrame(
            buffer,
            payload));

    assert(payload == "second");

    assert(buffer.empty());
}

int main()
{
    test_message_round_trip();
    test_protocol_frame();
    test_partial_frame();
    test_multiple_frames();

    std::cout
        << "All serialization tests passed\n";

    return 0;
}
