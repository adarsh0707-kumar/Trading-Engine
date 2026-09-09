#pragma once

#include "serialization/Message.hpp"

#include <string>

namespace trading
{
namespace serialization
{

class JsonSerializer
{
public:
    static std::string serialize(
        const Message &message);

    static Message deserialize(
        const std::string &json);

private:
    static std::string escape(
        const std::string &value);

    static std::string extractString(
        const std::string &json,
        const std::string &key);
};

} // namespace serialization
} // namespace trading
