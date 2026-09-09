#include "serialization/JsonSerializer.hpp"

#include <stdexcept>

namespace trading
{
namespace serialization
{

std::string JsonSerializer::serialize(
    const Message &message)
{
    return
        "{"
        "\"type\":\"" +
        escape(messageTypeToString(message.type)) +
        "\","
        "\"request_id\":\"" +
        escape(message.requestId) +
        "\","
        "\"timestamp\":\"" +
        escape(message.timestamp) +
        "\","
        "\"payload\":\"" +
        escape(message.payload) +
        "\""
        "}";
}

Message JsonSerializer::deserialize(
    const std::string &json)
{
    Message message;

    message.type =
        messageTypeFromString(
            extractString(json, "type"));

    message.requestId =
        extractString(json, "request_id");

    message.timestamp =
        extractString(json, "timestamp");

    message.payload =
        extractString(json, "payload");

    return message;
}

std::string JsonSerializer::escape(
    const std::string &value)
{
    std::string result;

    for (char c : value)
    {
        switch (c)
        {
        case '\\':
            result += "\\\\";
            break;

        case '"':
            result += "\\\"";
            break;

        case '\n':
            result += "\\n";
            break;

        case '\r':
            result += "\\r";
            break;

        case '\t':
            result += "\\t";
            break;

        default:
            result += c;
            break;
        }
    }

    return result;
}

std::string JsonSerializer::extractString(
    const std::string &json,
    const std::string &key)
{
    const std::string prefix =
        "\"" + key + "\":\"";

    const std::size_t start =
        json.find(prefix);

    if (start == std::string::npos)
    {
        throw std::invalid_argument(
            "Missing JSON field: " + key);
    }

    const std::size_t valueStart =
        start + prefix.size();

    std::string result;
    bool escaped = false;

    for (std::size_t i = valueStart;
         i < json.size();
         ++i)
    {
        const char c = json[i];

        if (escaped)
        {
            switch (c)
            {
            case 'n':
                result += '\n';
                break;

            case 'r':
                result += '\r';
                break;

            case 't':
                result += '\t';
                break;

            case '\\':
                result += '\\';
                break;

            case '"':
                result += '"';
                break;

            default:
                result += c;
                break;
            }

            escaped = false;
            continue;
        }

        if (c == '\\')
        {
            escaped = true;
            continue;
        }

        if (c == '"')
        {
            return result;
        }

        result += c;
    }

    throw std::invalid_argument(
        "Invalid JSON string field: " + key);
}

} // namespace serialization
} // namespace trading
