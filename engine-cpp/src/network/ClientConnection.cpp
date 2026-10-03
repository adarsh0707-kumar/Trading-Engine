#include "network/ClientConnection.hpp"

#include "network/Protocol.hpp"
#include "serialization/JsonSerializer.hpp"

#include <cerrno>
#include <cstring>
#include <iostream>
#include <thread>

#include <sys/socket.h>
#include <unistd.h>

namespace trading
{
namespace network
{

ClientConnection::ClientConnection(
    int socketFd,
    std::uint64_t connectionId)
    : socketFd_(socketFd),
      connectionId_(connectionId),
      lastHeartbeatAckTime_(
          std::chrono::system_clock::now())
{
}

ClientConnection::~ClientConnection()
{
    stop();

    if (socketFd_ >= 0)
    {
        ::close(socketFd_);

        socketFd_ = -1;
    }
}

std::uint64_t ClientConnection::id() const
{
    return connectionId_;
}

int ClientConnection::socketFd() const
{
    return socketFd_;
}

bool ClientConnection::sendMessage(
    const serialization::Message &message)
{
    if (!running_)
    {
        return false;
    }

    const std::string json =
        serialization::JsonSerializer::serialize(message);

    const std::vector<std::uint8_t> frame =
        Protocol::frame(json);

    std::lock_guard<std::mutex> lock(sendMutex_);

    return sendAll(frame);
}

void ClientConnection::start(
    MessageHandler messageHandler,
    DisconnectHandler disconnectHandler)
{
    if (running_.exchange(true))
    {
        return;
    }

    messageHandler_ = std::move(messageHandler);
    disconnectHandler_ = std::move(disconnectHandler);

    std::thread(
        &ClientConnection::receiveLoop,
        shared_from_this())
        .detach();
}

void ClientConnection::stop()
{
    if (!running_.exchange(false))
    {
        return;
    }

    /*
     * The descriptor is only shut down here, never closed: the receive
     * thread may be blocked in recv() on it, and a closed descriptor
     * number is immediately reusable by the operating system. Shutting
     * the socket down unblocks the thread and closes the connection at
     * the protocol level; the descriptor itself is released by the
     * destructor, which cannot run before the receive thread exits
     * because that thread holds a shared_ptr to this connection.
     */
    if (socketFd_ >= 0)
    {
        ::shutdown(
            socketFd_,
            SHUT_RDWR);
    }
}

bool ClientConnection::isRunning() const
{
    return running_.load();
}

void ClientConnection::markHeartbeatAck()
{
    std::lock_guard<std::mutex> lock(
        heartbeatMutex_);

    lastHeartbeatAckTime_ =
        std::chrono::system_clock::now();
}

bool ClientConnection::isHeartbeatTimeout(
    std::chrono::seconds timeout) const
{
    std::lock_guard<std::mutex> lock(
        heartbeatMutex_);

    const auto now =
        std::chrono::system_clock::now();

    const auto elapsed =
        now - lastHeartbeatAckTime_;

    return elapsed > timeout;
}

std::chrono::system_clock::time_point
ClientConnection::lastHeartbeatAckTime() const
{
    std::lock_guard<std::mutex> lock(
        heartbeatMutex_);

    return lastHeartbeatAckTime_;
}

void ClientConnection::receiveLoop()
{
    while (running_)
    {
        if (!receiveSome())
        {
            break;
        }

        while (running_)
        {
            std::string payload;

            bool extracted = false;

            try
            {
                extracted =
                    Protocol::extractFrame(
                        receiveBuffer_,
                        payload);
            }
            catch (const std::exception &)
            {
                running_ = false;
                break;
            }

            if (!extracted)
            {
                break;
            }

            try
            {
                const serialization::Message message =
                    serialization::JsonSerializer::deserialize(
                        payload);

                if (message.type ==
                    serialization::MessageType::HEARTBEAT)
                {
                    markHeartbeatAck();
                }

                if (messageHandler_)
                {
                    messageHandler_(
                        shared_from_this(),
                        message);
                }
            }
            catch (const std::exception &)
            {
                serialization::Message error;
                error.type =
                    serialization::MessageType::ERROR;
                error.payload =
                    "Invalid message";

                sendMessage(error);
            }
        }
    }

    const bool wasRunning =
        running_.exchange(false);

    if (socketFd_ >= 0)
    {
        ::shutdown(
            socketFd_,
            SHUT_RDWR);
    }

    if (wasRunning && disconnectHandler_)
    {
        disconnectHandler_(
            shared_from_this());
    }
}

bool ClientConnection::sendAll(
    const std::vector<std::uint8_t> &data)
{
    std::size_t totalSent = 0;

    while (totalSent < data.size())
    {
        const ssize_t sent =
            ::send(
                socketFd_,
                data.data() + totalSent,
                data.size() - totalSent,
                MSG_NOSIGNAL);

        if (sent < 0)
        {
            if (errno == EINTR)
            {
                continue;
            }

            return false;
        }

        if (sent == 0)
        {
            return false;
        }

        totalSent +=
            static_cast<std::size_t>(sent);
    }

    return true;
}

bool ClientConnection::receiveSome()
{
    std::uint8_t buffer[8192];

    const ssize_t received =
        ::recv(
            socketFd_,
            buffer,
            sizeof(buffer),
            0);

    if (received == 0)
    {
        return false;
    }

    if (received < 0)
    {
        if (errno == EINTR)
        {
            return true;
        }

        return false;
    }

    receiveBuffer_.insert(
        receiveBuffer_.end(),
        buffer,
        buffer + received);

    return true;
}

} // namespace network
} // namespace trading
