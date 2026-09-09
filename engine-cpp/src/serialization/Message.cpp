#include "serialization/Message.hpp"

namespace trading
{
namespace serialization
{

bool Message::operator==(const Message &other) const
{
    return
        type == other.type &&
        requestId == other.requestId &&
        timestamp == other.timestamp &&
        payload == other.payload;
}

std::string messageTypeToString(MessageType type)
{
    switch (type)
    {
    case MessageType::HELLO:
        return "HELLO";

    case MessageType::HEARTBEAT:
        return "HEARTBEAT";

    case MessageType::ORDER:
        return "ORDER";

    case MessageType::TRADE:
        return "TRADE";

    case MessageType::MARKET_DATA:
        return "MARKET_DATA";

    case MessageType::BOOK_SNAPSHOT:
        return "BOOK_SNAPSHOT";

    case MessageType::ERROR:
        return "ERROR";

    case MessageType::SHUTDOWN:
        return "SHUTDOWN";

    case MessageType::UNKNOWN:
    default:
        return "UNKNOWN";
    }
}

MessageType messageTypeFromString(const std::string &value)
{
    if (value == "HELLO")
    {
        return MessageType::HELLO;
    }

    if (value == "HEARTBEAT")
    {
        return MessageType::HEARTBEAT;
    }

    if (value == "ORDER")
    {
        return MessageType::ORDER;
    }

    if (value == "TRADE")
    {
        return MessageType::TRADE;
    }

    if (value == "MARKET_DATA")
    {
        return MessageType::MARKET_DATA;
    }

    if (value == "BOOK_SNAPSHOT")
    {
        return MessageType::BOOK_SNAPSHOT;
    }

    if (value == "ERROR")
    {
        return MessageType::ERROR;
    }

    if (value == "SHUTDOWN")
    {
        return MessageType::SHUTDOWN;
    }

    return MessageType::UNKNOWN;
}

} // namespace serialization
} // namespace trading
