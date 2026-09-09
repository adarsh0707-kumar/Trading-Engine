#include "network/Protocol.hpp"

#include <stdexcept>

namespace trading
{
namespace network
{

std::vector<std::uint8_t> Protocol::frame(const std::string &payload)
{
    if (!validatePayloadSize(payload.size()))
    {
        throw std::invalid_argument("Payload exceeds maximum frame size");
    }

    std::vector<std::uint8_t> buffer;
    buffer.reserve(HEADER_SIZE + payload.size());

    appendUint32(
        buffer,
        static_cast<std::uint32_t>(payload.size()));

    buffer.insert(
        buffer.end(),
        payload.begin(),
        payload.end());

    return buffer;
}

bool Protocol::extractFrame(
    std::vector<std::uint8_t> &buffer,
    std::string &payload)
{
    if (buffer.size() < HEADER_SIZE)
    {
        return false;
    }

    const std::uint32_t payloadSize =
        readUint32(buffer, 0);

    if (!validatePayloadSize(payloadSize))
    {
        throw std::runtime_error(
            "Invalid frame payload size");
    }

    const std::size_t totalSize =
        HEADER_SIZE + static_cast<std::size_t>(payloadSize);

    if (buffer.size() < totalSize)
    {
        return false;
    }

    payload.assign(
        buffer.begin() + HEADER_SIZE,
        buffer.begin() + totalSize);

    buffer.erase(
        buffer.begin(),
        buffer.begin() + totalSize);

    return true;
}

bool Protocol::validatePayloadSize(std::size_t size)
{
    return size <= MAX_PAYLOAD_SIZE;
}

void Protocol::appendUint32(
    std::vector<std::uint8_t> &buffer,
    std::uint32_t value)
{
    buffer.push_back(
        static_cast<std::uint8_t>((value >> 24) & 0xFF));

    buffer.push_back(
        static_cast<std::uint8_t>((value >> 16) & 0xFF));

    buffer.push_back(
        static_cast<std::uint8_t>((value >> 8) & 0xFF));

    buffer.push_back(
        static_cast<std::uint8_t>(value & 0xFF));
}

std::uint32_t Protocol::readUint32(
    const std::vector<std::uint8_t> &buffer,
    std::size_t offset)
{
    return
        (static_cast<std::uint32_t>(buffer[offset]) << 24) |
        (static_cast<std::uint32_t>(buffer[offset + 1]) << 16) |
        (static_cast<std::uint32_t>(buffer[offset + 2]) << 8) |
        static_cast<std::uint32_t>(buffer[offset + 3]);
}

} // namespace network
} // namespace trading
