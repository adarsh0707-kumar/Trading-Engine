#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace trading
{
namespace network
{

class Protocol
{
public:
    static constexpr std::uint32_t HEADER_SIZE = sizeof(std::uint32_t);
    static constexpr std::uint32_t MAX_PAYLOAD_SIZE = 1024 * 1024;

    static std::vector<std::uint8_t> frame(const std::string &payload);

    static bool extractFrame(
        std::vector<std::uint8_t> &buffer,
        std::string &payload);

    static bool validatePayloadSize(std::size_t size);

private:
    static void appendUint32(
        std::vector<std::uint8_t> &buffer,
        std::uint32_t value);

    static std::uint32_t readUint32(
        const std::vector<std::uint8_t> &buffer,
        std::size_t offset);
};

} // namespace network
} // namespace trading
