#include "network/Protocol.hpp"
#include "network/SocketServer.hpp"
#include "serialization/JsonSerializer.hpp"
#include "serialization/Message.hpp"

#include "../TestCheck.hpp"

#include <chrono>
#include <cstring>
#include <iostream>
#include <thread>
#include <vector>

#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>

using namespace trading;

static std::string receiveMessage(int fd, int timeout_ms)
{
    std::vector<std::uint8_t> buffer;

    for (int elapsed = 0; elapsed < timeout_ms; elapsed += 10)
    {
        std::uint8_t temp[4096];

        const ssize_t received =
            ::recv(
                fd,
                temp,
                sizeof(temp),
                MSG_DONTWAIT);

        if (received > 0)
        {
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

        std::this_thread::sleep_for(
            std::chrono::milliseconds(10));
    }

    return "";
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

static void test_heartbeat_sent_and_acked()
{
    network::SocketServer server(
        0,
        500,
        2);

    CHECK(server.start());

    const int clientFd =
        connectToServer(server.port());

    const std::string hello =
        receiveMessage(clientFd, 100);

    CHECK(!hello.empty());

    const serialization::Message helloMsg =
        serialization::JsonSerializer::deserialize(
            hello);

    CHECK(
        helloMsg.type ==
        serialization::MessageType::HELLO);

    const std::string heartbeat =
        receiveMessage(clientFd, 1000);

    CHECK(!heartbeat.empty());

    const serialization::Message hbMsg =
        serialization::JsonSerializer::deserialize(
            heartbeat);

    CHECK(
        hbMsg.type ==
        serialization::MessageType::HEARTBEAT);

    CHECK(hbMsg.payload == "PING");

    serialization::Message response;

    response.type =
        serialization::MessageType::HEARTBEAT;

    response.payload = "PONG";

    const std::string json =
        serialization::JsonSerializer::serialize(
            response);

    const auto frame =
        network::Protocol::frame(json);

    ssize_t sent = ::send(
        clientFd,
        frame.data(),
        frame.size(),
        MSG_NOSIGNAL);

    CHECK(sent > 0);

    std::this_thread::sleep_for(
        std::chrono::milliseconds(100));

    CHECK(server.clientCount() == 1);

    ::close(clientFd);

    server.stop();
}

static void test_heartbeat_timeout_disconnects()
{
    network::SocketServer server(
        0,
        200,
        1);

    CHECK(server.start());

    const int clientFd =
        connectToServer(server.port());

    const std::string hello =
        receiveMessage(clientFd, 100);

    CHECK(!hello.empty());

    CHECK(server.clientCount() == 1);

    std::this_thread::sleep_for(
        std::chrono::milliseconds(400));

    const std::string heartbeat =
        receiveMessage(clientFd, 500);

    CHECK(!heartbeat.empty());

    std::this_thread::sleep_for(
        std::chrono::milliseconds(1500));

    CHECK(server.clientCount() == 0);

    ::close(clientFd);

    server.stop();
}

int main()
{
    test_heartbeat_sent_and_acked();
    test_heartbeat_timeout_disconnects();

    std::cout
        << "All connection heartbeat tests passed\n";

    return 0;
}
