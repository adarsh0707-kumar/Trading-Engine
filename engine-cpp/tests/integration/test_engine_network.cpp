#include "network/Protocol.hpp"
#include "network/SocketServer.hpp"
#include "serialization/JsonSerializer.hpp"
#include "serialization/Message.hpp"

#include <cassert>
#include <chrono>
#include <cstring>
#include <iostream>
#include <thread>
#include <vector>

#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>

using namespace trading::network;
using namespace trading::serialization;

static bool sendAll(
    int fd,
    const std::vector<std::uint8_t> &data)
{
    std::size_t sent = 0;

    while (sent < data.size())
    {
        const ssize_t result =
            ::send(
                fd,
                data.data() + sent,
                data.size() - sent,
                MSG_NOSIGNAL);

        if (result <= 0)
        {
            return false;
        }

        sent +=
            static_cast<std::size_t>(result);
    }

    return true;
}

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

        assert(received > 0);

        buffer.insert(
            buffer.end(),
            temp,
            temp + received);

        std::string payload;

        if (Protocol::extractFrame(
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

static void test_server_accepts_client()
{
    SocketServer server(0);

    assert(server.start());
    assert(server.isRunning());
    assert(server.port() != 0);

    const int clientFd =
        connectToServer(server.port());

    for (int i = 0; i < 100; ++i)
    {
        if (server.clientCount() == 1)
        {
            break;
        }

        std::this_thread::sleep_for(
            std::chrono::milliseconds(5));
    }

    assert(server.clientCount() == 1);

    const std::string hello =
        receiveMessage(clientFd);

    const Message message =
        JsonSerializer::deserialize(hello);

    assert(
        message.type ==
        MessageType::HELLO);

    ::close(clientFd);

    server.stop();

    assert(!server.isRunning());
}

static void test_heartbeat()
{
    SocketServer server(0);

    assert(server.start());

    const int clientFd =
        connectToServer(server.port());

    const std::string hello =
        receiveMessage(clientFd);

    (void)hello;

    Message heartbeat;

    heartbeat.type =
        MessageType::HEARTBEAT;

    heartbeat.requestId =
        "heartbeat-1";

    heartbeat.payload =
        "PING";

    const std::string json =
        JsonSerializer::serialize(
            heartbeat);

    const auto frame =
        Protocol::frame(json);

    assert(
        sendAll(
            clientFd,
            frame));

    const std::string responseJson =
        receiveMessage(clientFd);

    const Message response =
        JsonSerializer::deserialize(
            responseJson);

    assert(
        response.type ==
        MessageType::HEARTBEAT);

    assert(
        response.requestId ==
        "heartbeat-1");

    assert(
        response.payload ==
        "OK");

    ::close(clientFd);

    server.stop();
}

static void test_broadcast()
{
    SocketServer server(0);

    assert(server.start());

    const int clientFd =
        connectToServer(server.port());

    const std::string hello =
        receiveMessage(clientFd);

    (void)hello;

    Message trade;

    trade.type =
        MessageType::TRADE;

    trade.requestId =
        "trade-1";

    trade.payload =
        "price=101.5 quantity=10";

    server.broadcast(trade);

    const std::string responseJson =
        receiveMessage(clientFd);

    const Message received =
        JsonSerializer::deserialize(
            responseJson);

    assert(
        received.type ==
        MessageType::TRADE);

    assert(
        received.requestId ==
        "trade-1");

    assert(
        received.payload ==
        "price=101.5 quantity=10");

    ::close(clientFd);

    server.stop();
}

int main()
{
    test_server_accepts_client();
    test_heartbeat();
    test_broadcast();

    std::cout
        << "All engine network integration tests passed\n";

    return 0;
}
