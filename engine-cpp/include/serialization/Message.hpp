#pragma once

#include <cstdint>
#include <string>

namespace trading
{
namespace serialization
{

enum class MessageType : std::uint8_t
{
    UNKNOWN = 0,
    HELLO = 1,
    HEARTBEAT = 2,
    ORDER = 3,
    TRADE = 4,
    MARKET_DATA = 5,
    BOOK_SNAPSHOT = 6,
    ERROR = 7,
    SHUTDOWN = 8
};

struct Message
{
    MessageType type{MessageType::UNKNOWN};
    std::string requestId;
    std::string timestamp;
    std::string payload;

    bool operator==(const Message &other) const;
};

std::string messageTypeToString(MessageType type);

MessageType messageTypeFromString(const std::string &value);

} // namespace serialization
} // namespace trading
