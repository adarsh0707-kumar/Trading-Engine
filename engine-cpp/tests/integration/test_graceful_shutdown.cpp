#include "network/Protocol.hpp"
#include "network/SocketServer.hpp"
#include "serialization/JsonSerializer.hpp"
#include "serialization/Message.hpp"

#include <arpa/inet.h>
#include <cassert>
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

static int connectToServer(std::uint16_t port)
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

static void test_graceful_shutdown()
{
    /*
     * Use a short heartbeat interval so that the test
     * does not depend on the production default interval.
     */
    SocketServer server(
        0,
        100,
        2);

    assert(server.start());
    assert(server.isRunning());
    assert(server.port() != 0);

    /*
     * Connect a client so shutdown is tested while
     * an active connection exists.
     */
    const int clientFd =
        connectToServer(server.port());

    assert(
        waitForClientCount(
            server,
            1,
            std::chrono::milliseconds(1000)));

    /*
     * Confirm that the newly connected client completed
     * the initial server handshake.
     */
    const std::string hello =
        receiveMessage(clientFd);

    const Message message =
        JsonSerializer::deserialize(hello);

    assert(
        message.type ==
        MessageType::HELLO);

    /*
     * The server should currently have one active client.
     */
    assert(server.isRunning());
    assert(server.clientCount() == 1);

    /*
     * --------------------------------------------------------
     * Graceful shutdown
     * --------------------------------------------------------
     *
     * SocketServer::stop() is responsible for:
     *
     * 1. Stopping the server loops.
     * 2. Closing the listening socket.
     * 3. Stopping active client connections.
     * 4. Clearing the client collection.
     * 5. Resetting the bound port.
     */
    server.stop();

    /*
     * Verify the final server state.
     */
    assert(!server.isRunning());
    assert(server.clientCount() == 0);
    assert(server.port() == 0);

    /*
     * The client socket should also be safe to close after
     * the server has completed its shutdown sequence.
     */
    ::shutdown(
        clientFd,
        SHUT_RDWR);

    ::close(clientFd);

    /*
     * Calling stop() again should be harmless and should
     * leave the server in the same stopped state.
     */
    server.stop();

    assert(!server.isRunning());
    assert(server.clientCount() == 0);
    assert(server.port() == 0);
}

int main()
{
    test_graceful_shutdown();

    std::cout
        << "Graceful shutdown integration test passed\n";

    return 0;
}
