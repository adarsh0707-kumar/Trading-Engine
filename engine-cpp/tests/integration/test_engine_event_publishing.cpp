#include "engine/Engine.hpp"
#include "engine/EngineConfig.hpp"
#include "network/Protocol.hpp"
#include "serialization/JsonSerializer.hpp"

#include "../TestCheck.hpp"

#include <chrono>
#include <cstring>
#include <iostream>
#include <thread>
#include <vector>

#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

using namespace trading;


static std::string receiveMessage(int fd)
{
    std::vector<std::uint8_t> buffer;

    for (;;)
    {
        std::uint8_t temp[4096];

        const ssize_t received =
            ::recv(
                fd,
                temp,
                sizeof(temp),
                0);

        if (received <= 0)
        {
            return "";
        }

        buffer.insert(
            buffer.end(),
            temp,
            temp + received);

        std::string payload;

        if (network::Protocol::extractFrame(
                buffer,
                payload))
        {
            return payload;
        }
    }
}

// Preserve unread bytes between calls and return an empty string on socket timeout.
static std::string receiveMessage(
    int fd,
    std::vector<std::uint8_t> &buffer)
{
    for (;;)
    {
        std::string payload;
        if (network::Protocol::extractFrame(buffer, payload))
        {
            return payload;
        }

        std::uint8_t temp[4096];
        const ssize_t received = ::recv(fd, temp, sizeof(temp), 0);
        if (received <= 0)
        {
            return "";
        }

        buffer.insert(buffer.end(), temp, temp + received);
    }
}

static int connectToServer(
    std::uint16_t port)
{
    const int fd =
        ::socket(
            AF_INET,
            SOCK_STREAM,
            0);

    CHECK(fd >= 0);

    sockaddr_in address{};

    address.sin_family =
        AF_INET;

    address.sin_port =
        htons(port);

    address.sin_addr.s_addr =
        htonl(INADDR_LOOPBACK);

    const int result =
        ::connect(
            fd,
            reinterpret_cast<sockaddr *>(&address),
            sizeof(address));

    CHECK(result == 0);

    return fd;
}

static void test_engine_broadcasts_trades()
{
    engine_runtime::EngineConfig config;

    config.symbol = "TEST";
    config.port = 0;
    config.tick_interval_ms = 10;
    config.market_seed = 999;
    config.min_price = 100.0;
    config.max_price = 100.0;
    config.min_quantity = 5;
    config.max_quantity = 5;

    engine_runtime::Engine engine(config);

    CHECK(engine.start());

    std::this_thread::sleep_for(
        std::chrono::milliseconds(50));

    const int clientFd =
        connectToServer(engine.port());

    const std::string hello =
        receiveMessage(clientFd);

    CHECK(!hello.empty());

    const serialization::Message helloMsg =
        serialization::JsonSerializer::deserialize(
            hello);

    CHECK(
        helloMsg.type ==
        serialization::MessageType::HELLO);

    std::string tradeJson;

    for (int i = 0; i < 50; ++i)
    {
        tradeJson =
            receiveMessage(clientFd);

        if (!tradeJson.empty())
        {
            break;
        }

        std::this_thread::sleep_for(
            std::chrono::milliseconds(10));
    }

    CHECK(!tradeJson.empty());

    const serialization::Message tradeMsg =
        serialization::JsonSerializer::deserialize(
            tradeJson);

    CHECK(
        tradeMsg.type ==
        serialization::MessageType::TRADE);

    CHECK(tradeMsg.payload.find("TEST") !=
           std::string::npos);

    CHECK(tradeMsg.payload.find("100") !=
           std::string::npos);

    ::close(clientFd);

    engine.stop();
}

static void test_engine_returns_order_book_snapshot()
{
    engine_runtime::EngineConfig config;
    config.symbol = "TEST";
    config.port = 0;
    config.tick_interval_ms = 10;
    config.market_seed = 999;
    config.min_price = 100.0;
    config.max_price = 100.0;
    config.min_quantity = 5;
    config.max_quantity = 5;

    engine_runtime::Engine engine(config);
    CHECK(engine.start());

    const int clientFd = connectToServer(engine.port());
    const std::string hello = receiveMessage(clientFd);
    CHECK(!hello.empty());

    serialization::Message request;
    request.type = serialization::MessageType::BOOK_SNAPSHOT;
    request.requestId = "book-test-1";
    request.timestamp = "2026-10-06T00:00:00Z";
    request.payload = "REQUEST";

    const auto frame = network::Protocol::frame(
        serialization::JsonSerializer::serialize(request));

    CHECK(::send(clientFd, frame.data(), frame.size(), MSG_NOSIGNAL) ==
          static_cast<ssize_t>(frame.size()));

    serialization::Message response;
    for (int i = 0; i < 50; ++i)
    {
        const std::string payload = receiveMessage(clientFd);
        CHECK(!payload.empty());
        response = serialization::JsonSerializer::deserialize(payload);
        if (response.type == serialization::MessageType::BOOK_SNAPSHOT)
        {
            break;
        }
    }

    CHECK(response.type == serialization::MessageType::BOOK_SNAPSHOT);
    CHECK(response.requestId == "book-test-1");
    CHECK(response.payload.find("\"symbol\":\"TEST\"") != std::string::npos);
    CHECK(response.payload.find("\"bids\":") != std::string::npos);
    CHECK(response.payload.find("\"asks\":") != std::string::npos);

    ::close(clientFd);
    engine.stop();
}

static bool isTradeMessage(const std::string &json)
{
    if (json.empty())
    {
        return false;
    }

    const serialization::Message message =
        serialization::JsonSerializer::deserialize(json);
    return message.type == serialization::MessageType::TRADE;
}

static void test_engine_stops_matching_after_risk_halt()
{
    engine_runtime::EngineConfig config;
    config.symbol = "TEST";
    config.port = 0;
    config.tick_interval_ms = 10;
    config.market_seed = 999;
    config.min_price = 80.0;
    config.max_price = 120.0;
    config.min_quantity = 5;
    config.max_quantity = 5;
    config.risk_max_position = 1000;
    config.risk_max_position_value = 10000000.0;
    config.risk_max_drawdown = 0.01;
    config.risk_max_daily_loss = 1000000.0;
    config.risk_initial_equity = 10000.0;

    engine_runtime::Engine engine(config);
    CHECK(engine.start());

    const int clientFd = connectToServer(engine.port());
    timeval timeout{};
    timeout.tv_usec = 20000;
    CHECK(::setsockopt(clientFd, SOL_SOCKET, SO_RCVTIMEO,
                       &timeout, sizeof(timeout)) == 0);

    std::vector<std::uint8_t> buffer;
    const std::string hello = receiveMessage(clientFd, buffer);
    CHECK(!hello.empty());
    CHECK(serialization::JsonSerializer::deserialize(hello).type ==
          serialization::MessageType::HELLO);

    bool sawTrade = false;
    const auto haltDeadline =
        std::chrono::steady_clock::now() + std::chrono::seconds(3);

    while (!engine.is_risk_halted() &&
           std::chrono::steady_clock::now() < haltDeadline)
    {
        const std::string json = receiveMessage(clientFd, buffer);
        if (json.empty())
        {
            continue;
        }

        if (isTradeMessage(json))
        {
            sawTrade = true;
        }
    }

    CHECK(engine.is_risk_halted());

    // Drain events already generated by the matching operation that caused the halt.
    int drainedTrades = 0;
    for (;;)
    {
        const std::string json = receiveMessage(clientFd, buffer);
        if (json.empty())
        {
            break;
        }

        if (isTradeMessage(json))
        {
            ++drainedTrades;
        }
    }
    CHECK(sawTrade || drainedTrades > 0);

    // Once the engine reports the halt branch, subsequent ticks must not match.
    int tradesAfterHalt = 0;
    const auto observationDeadline =
        std::chrono::steady_clock::now() + std::chrono::milliseconds(100);

    while (std::chrono::steady_clock::now() < observationDeadline)
    {
        const std::string json = receiveMessage(clientFd, buffer);
        if (!json.empty() && isTradeMessage(json))
        {
            ++tradesAfterHalt;
        }
    }

    CHECK(tradesAfterHalt == 0);

    ::close(clientFd);
    engine.stop();
}

int main()
{
    test_engine_broadcasts_trades();
    test_engine_returns_order_book_snapshot();
    test_engine_stops_matching_after_risk_halt();

    std::cout
        << "Engine event publishing test passed\n";

    return 0;
}
