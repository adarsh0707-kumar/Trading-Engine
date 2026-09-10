#include "network/SocketServer.hpp"

#include <cerrno>
#include <chrono>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <thread>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

namespace trading
{
namespace network
{

SocketServer::SocketServer(
    std::uint16_t port,
    std::uint64_t heartbeat_interval_ms,
    std::uint64_t heartbeat_timeout_sec)
    : requestedPort_(port),
      heartbeatIntervalMs_(heartbeat_interval_ms),
      heartbeatTimeoutSec_(heartbeat_timeout_sec)
{
}

SocketServer::~SocketServer()
{
    stop();
}

bool SocketServer::start()
{
    if (running_.exchange(true))
    {
        return false;
    }

    try
    {
        serverFd_ =
            createListeningSocket();

        acceptThread_ =
            std::thread(
                &SocketServer::acceptLoop,
                this);

        heartbeatThread_ =
            std::thread(
                &SocketServer::heartbeatLoop,
                this);

        return true;
    }
    catch (...)
    {
        running_ = false;

        if (serverFd_ >= 0)
        {
            ::close(serverFd_);
            serverFd_ = -1;
        }

        throw;
    }
}

void SocketServer::stop()
{
    if (!running_.exchange(false))
    {
        return;
    }

    if (serverFd_ >= 0)
    {
        ::shutdown(
            serverFd_,
            SHUT_RDWR);

        ::close(serverFd_);

        serverFd_ = -1;
    }

    if (acceptThread_.joinable())
    {
        acceptThread_.join();
    }

    if (heartbeatThread_.joinable())
    {
        heartbeatThread_.join();
    }

    std::unordered_map<std::uint64_t, std::shared_ptr<ClientConnection>> clients;

    {
        std::lock_guard<std::mutex> lock(
            clientsMutex_);

        clients.swap(clients_);
    }

    for (auto &[id, client] : clients)
    {
        (void)id;

        client->stop();
    }

    boundPort_ = 0;
}

bool SocketServer::isRunning() const
{
    return running_.load();
}

std::uint16_t SocketServer::port() const
{
    return boundPort_;
}

std::size_t SocketServer::clientCount() const
{
    std::lock_guard<std::mutex> lock(
        clientsMutex_);

    return clients_.size();
}

void SocketServer::broadcast(
    const serialization::Message &message)
{
    std::lock_guard<std::mutex> lock(
        clientsMutex_);

    for (auto it = clients_.begin();
         it != clients_.end();)
    {
        if (!it->second->sendMessage(message))
        {
            it = clients_.erase(it);
        }
        else
        {
            ++it;
        }
    }
}

void SocketServer::acceptLoop()
{
    while (running_)
    {
        sockaddr_in clientAddress{};
        socklen_t clientLength =
            sizeof(clientAddress);

        const int clientFd =
            ::accept(
                serverFd_,
                reinterpret_cast<sockaddr *>(
                    &clientAddress),
                &clientLength);

        if (clientFd < 0)
        {
            if (!running_)
            {
                break;
            }

            if (errno == EINTR)
            {
                continue;
            }

            continue;
        }

        const std::uint64_t connectionId =
            nextConnectionId_++;

        auto client =
            std::make_shared<ClientConnection>(
                clientFd,
                connectionId);

        {
            std::lock_guard<std::mutex> lock(
                clientsMutex_);

            clients_[connectionId] = client;
        }

        client->start(
            [this](
                std::shared_ptr<ClientConnection> connection,
                const serialization::Message &message)
            {
                handleMessage(
                    std::move(connection),
                    message);
            },
            [this](
                std::shared_ptr<ClientConnection> connection)
            {
                handleDisconnect(
                    std::move(connection));
            });

        serialization::Message hello;

        hello.type =
            serialization::MessageType::HELLO;

        hello.payload =
            "Trading Engine transport connected";

        client->sendMessage(hello);

        client->markHeartbeatAck();
    }
}

void SocketServer::heartbeatLoop()
{
    while (running_)
    {
        std::this_thread::sleep_for(
            std::chrono::milliseconds(
                heartbeatIntervalMs_));

        if (!running_)
        {
            break;
        }

        {
            std::lock_guard<std::mutex> lock(
                clientsMutex_);

            serialization::Message heartbeat;

            heartbeat.type =
                serialization::MessageType::HEARTBEAT;

            heartbeat.payload = "PING";

            for (auto &[id, client] : clients_)
            {
                (void)id;

                client->sendMessage(heartbeat);
            }
        }

        {
            std::lock_guard<std::mutex> lock(
                clientsMutex_);

            std::vector<std::uint64_t> timedout;

            for (auto &[id, client] : clients_)
            {
                if (client->isHeartbeatTimeout(
                        std::chrono::seconds(
                            heartbeatTimeoutSec_)))
                {
                    timedout.push_back(id);
                }
            }

            for (std::uint64_t id : timedout)
            {
                clients_[id]->stop();
                clients_.erase(id);
            }
        }
    }
}

void SocketServer::handleMessage(
    std::shared_ptr<ClientConnection> client,
    const serialization::Message &message)
{
    switch (message.type)
    {
    case serialization::MessageType::HEARTBEAT:
    {
        serialization::Message response;

        response.type =
            serialization::MessageType::HEARTBEAT;

        response.requestId =
            message.requestId;

        response.timestamp =
            message.timestamp;

        response.payload =
            "OK";

        client->markHeartbeatAck();

        client->sendMessage(response);

        break;
    }

    default:
        break;
    }
}

void SocketServer::handleDisconnect(
    std::shared_ptr<ClientConnection> client)
{
    std::lock_guard<std::mutex> lock(
        clientsMutex_);

    clients_.erase(client->id());
}

int SocketServer::createListeningSocket()
{
    const int fd =
        ::socket(
            AF_INET,
            SOCK_STREAM,
            0);

    if (fd < 0)
    {
        throw std::runtime_error(
            "Failed to create socket: " +
            std::string(std::strerror(errno)));
    }

    int reuse = 1;

    if (::setsockopt(
            fd,
            SOL_SOCKET,
            SO_REUSEADDR,
            &reuse,
            sizeof(reuse)) < 0)
    {
        ::close(fd);

        throw std::runtime_error(
            "Failed to set SO_REUSEADDR");
    }

    sockaddr_in address{};

    address.sin_family =
        AF_INET;

    address.sin_addr.s_addr =
        htonl(INADDR_LOOPBACK);

    address.sin_port =
        htons(requestedPort_);

    if (::bind(
            fd,
            reinterpret_cast<sockaddr *>(&address),
            sizeof(address)) < 0)
    {
        ::close(fd);

        throw std::runtime_error(
            "Failed to bind socket: " +
            std::string(std::strerror(errno)));
    }

    if (::listen(fd, 64) < 0)
    {
        ::close(fd);

        throw std::runtime_error(
            "Failed to listen on socket");
    }

    sockaddr_in boundAddress{};
    socklen_t boundLength =
        sizeof(boundAddress);

    if (::getsockname(
            fd,
            reinterpret_cast<sockaddr *>(&boundAddress),
            &boundLength) == 0)
    {
        boundPort_ =
            ntohs(boundAddress.sin_port);
    }

    return fd;
}

} // namespace network
} // namespace trading
