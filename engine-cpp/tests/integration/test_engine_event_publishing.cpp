#include "engine/Engine.hpp"
#include "engine/EngineConfig.hpp"
#include "network/Protocol.hpp"
#include "serialization/JsonSerializer.hpp"

#include <cassert>
#include <chrono>
#include <cstring>
#include <iostream>
#include <thread>
#include <vector>

#include <arpa/inet.h>
#include <sys/socket.h>
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

static int connectToServer(
    std::uint16_t port)
{
    const int fd =
        ::socket(
            AF_INET,
            SOCK_STREAM,
            0);

    assert(fd >= 0);

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

    assert(result == 0);

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

    assert(engine.start());

    std::this_thread::sleep_for(
        std::chrono::milliseconds(50));

    const int clientFd =
        connectToServer(engine.port());

    const std::string hello =
        receiveMessage(clientFd);

    assert(!hello.empty());

    const serialization::Message helloMsg =
        serialization::JsonSerializer::deserialize(
            hello);

    assert(
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

    assert(!tradeJson.empty());

    const serialization::Message tradeMsg =
        serialization::JsonSerializer::deserialize(
            tradeJson);

    assert(
        tradeMsg.type ==
        serialization::MessageType::TRADE);

    assert(tradeMsg.payload.find("TEST") !=
           std::string::npos);

    assert(tradeMsg.payload.find("100") !=
           std::string::npos);

    ::close(clientFd);

    engine.stop();
}

int main()
{
    test_engine_broadcasts_trades();

    std::cout
        << "Engine event publishing test passed\n";

    return 0;
}
