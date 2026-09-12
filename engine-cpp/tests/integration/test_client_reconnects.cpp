#include "network/Protocol.hpp"
#include "network/SocketServer.hpp"
#include "serialization/JsonSerializer.hpp"
#include "serialization/Message.hpp"

#include <arpa/inet.h>
#include "../TestCheck.hpp"

#include <chrono>
#include <cstdint>
#include <iostream>
#include <thread>
#include <vector>

#include <sys/socket.h>
#include <unistd.h>

using namespace trading::network;
using namespace trading::serialization;

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

        CHECK(received > 0);

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

static int connectToServer(std::uint16_t port)
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

static bool waitForClientCount(
    const SocketServer &server,
    std::size_t expectedCount,
    std::chrono::milliseconds timeout)
{
    const auto deadline =
        std::chrono::steady_clock::now() + timeout;

    while (std::chrono::steady_clock::now() < deadline)
    {
        if (server.clientCount() == expectedCount)
        {
            return true;
        }

        std::this_thread::sleep_for(
            std::chrono::milliseconds(10));
    }

    return server.clientCount() == expectedCount;
}

static void test_client_reconnects()
{
    /*
     * Use a short heartbeat interval so the test does not
     * unnecessarily delay server shutdown.
     */
    SocketServer server(
        0,
        100,
        2);

    CHECK(server.start());
    CHECK(server.isRunning());
    CHECK(server.port() != 0);

    /*
     * --------------------------------------------------------
     * First client connection
     * --------------------------------------------------------
     */
    const int firstClientFd =
        connectToServer(server.port());

    CHECK(
        waitForClientCount(
            server,
            1,
            std::chrono::milliseconds(1000)));

    const std::string firstHello =
        receiveMessage(firstClientFd);

    const Message firstMessage =
        JsonSerializer::deserialize(firstHello);

    CHECK(
        firstMessage.type ==
        MessageType::HELLO);

    /*
     * Close the first client.
     *
     * The server should detect the disconnect and remove
     * the client from its active client collection.
     */
    ::shutdown(
        firstClientFd,
        SHUT_RDWR);

    ::close(firstClientFd);

    CHECK(
        waitForClientCount(
            server,
            0,
            std::chrono::milliseconds(1000)));

    /*
     * --------------------------------------------------------
     * Second client connection
     * --------------------------------------------------------
     *
     * This verifies that the server continues accepting
     * connections after the first client disconnects.
     */
    const int secondClientFd =
        connectToServer(server.port());

    CHECK(
        waitForClientCount(
            server,
            1,
            std::chrono::milliseconds(1000)));

    const std::string secondHello =
        receiveMessage(secondClientFd);

    const Message secondMessage =
        JsonSerializer::deserialize(secondHello);

    CHECK(
        secondMessage.type ==
        MessageType::HELLO);

    /*
     * The server must still be operational after reconnect.
     */
    CHECK(server.isRunning());

    /*
     * Clean up the second client.
     */
    ::shutdown(
        secondClientFd,
        SHUT_RDWR);

    ::close(secondClientFd);

    CHECK(
        waitForClientCount(
            server,
            0,
            std::chrono::milliseconds(1000)));

    /*
     * Stop the server and verify its final state.
     */
    server.stop();

    CHECK(!server.isRunning());
    CHECK(server.clientCount() == 0);
}

int main()
{
    test_client_reconnects();

    std::cout
        << "Client reconnection integration test passed\n";

    return 0;
}
