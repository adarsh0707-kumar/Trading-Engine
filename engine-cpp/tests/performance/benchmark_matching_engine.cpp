#include "matching/MatchingEngine.hpp"
#include "orderbook/Order.hpp"
#include "orderbook/OrderBook.hpp"

#include <chrono>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <memory>
#include <string>

namespace
{
    using Clock = std::chrono::steady_clock;

    constexpr std::int64_t ITERATIONS = 100000;

    struct BenchmarkResult
    {
        std::string name;
        std::int64_t operations;
        double elapsed_seconds;
        double operations_per_second;
        double nanoseconds_per_operation;
    };

    void print_result(const BenchmarkResult &result)
    {
        std::cout << std::left
                  << std::setw(42) << result.name
                  << std::right
                  << std::setw(12) << result.operations
                  << std::setw(18) << std::fixed
                  << std::setprecision(3)
                  << result.elapsed_seconds
                  << std::setw(20)
                  << std::setprecision(2)
                  << result.operations_per_second
                  << std::setw(20)
                  << std::setprecision(2)
                  << result.nanoseconds_per_operation
                  << '\n';
    }

    BenchmarkResult benchmark_single_level()
    {
        engine::MatchingEngine matching_engine;

        std::int64_t total_trades = 0;

        const auto start = Clock::now();

        for (std::int64_t i = 0; i < ITERATIONS; ++i)
        {
            engine::OrderBook order_book("TEST");

            auto resting_order = std::make_shared<engine::Order>(
                "S-" + std::to_string(i),
                "TEST",
                engine::Side::SELL,
                engine::OrderType::LIMIT,
                100.0,
                100,
                i * 2);

            order_book.add_order(resting_order);

            auto incoming_order = std::make_shared<engine::Order>(
                "B-" + std::to_string(i),
                "TEST",
                engine::Side::BUY,
                engine::OrderType::LIMIT,
                100.0,
                100,
                i * 2 + 1);

            const auto result =
                matching_engine.match(order_book, incoming_order);

            total_trades += static_cast<std::int64_t>(result.trades.size());
        }

        const auto end = Clock::now();

        const double elapsed =
            std::chrono::duration<double>(end - start).count();

        if (total_trades == 0)
        {
            std::cerr << "Benchmark error: no trades executed\n";
        }

        return {
            "Single-level full match",
            ITERATIONS,
            elapsed,
            static_cast<double>(ITERATIONS) / elapsed,
            (elapsed * 1'000'000'000.0) /
                static_cast<double>(ITERATIONS)};
    }

    BenchmarkResult benchmark_multi_level()
    {
        engine::MatchingEngine matching_engine;

        std::int64_t total_trades = 0;

        const auto start = Clock::now();

        for (std::int64_t i = 0; i < ITERATIONS; ++i)
        {
            engine::OrderBook order_book("TEST");

            for (int level = 0; level < 5; ++level)
            {
                auto resting_order = std::make_shared<engine::Order>(
                    "S-" + std::to_string(i) + "-" +
                        std::to_string(level),
                    "TEST",
                    engine::Side::SELL,
                    engine::OrderType::LIMIT,
                    100.0 + level,
                    20,
                    i * 10 + level);

                order_book.add_order(resting_order);
            }

            auto incoming_order = std::make_shared<engine::Order>(
                "B-" + std::to_string(i),
                "TEST",
                engine::Side::BUY,
                engine::OrderType::LIMIT,
                104.0,
                100,
                i * 10 + 9);

            const auto result =
                matching_engine.match(order_book, incoming_order);

            total_trades +=
                static_cast<std::int64_t>(result.trades.size());
        }

        const auto end = Clock::now();

        const double elapsed =
            std::chrono::duration<double>(end - start).count();

        if (total_trades == 0)
        {
            std::cerr << "Benchmark error: no trades executed\n";
        }

        return {
            "Five-level full match",
            ITERATIONS,
            elapsed,
            static_cast<double>(ITERATIONS) / elapsed,
            (elapsed * 1'000'000'000.0) /
                static_cast<double>(ITERATIONS)};
    }

    BenchmarkResult benchmark_partial_fill_and_rest()
    {
        engine::MatchingEngine matching_engine;

        std::int64_t total_trades = 0;

        const auto start = Clock::now();

        for (std::int64_t i = 0; i < ITERATIONS; ++i)
        {
            engine::OrderBook order_book("TEST");

            auto resting_order = std::make_shared<engine::Order>(
                "S-" + std::to_string(i),
                "TEST",
                engine::Side::SELL,
                engine::OrderType::LIMIT,
                100.0,
                50,
                i * 2);

            order_book.add_order(resting_order);

            auto incoming_order = std::make_shared<engine::Order>(
                "B-" + std::to_string(i),
                "TEST",
                engine::Side::BUY,
                engine::OrderType::LIMIT,
                100.0,
                100,
                i * 2 + 1);

            const auto result =
                matching_engine.match(order_book, incoming_order);

            total_trades +=
                static_cast<std::int64_t>(result.trades.size());
        }

        const auto end = Clock::now();

        const double elapsed =
            std::chrono::duration<double>(end - start).count();

        if (total_trades == 0)
        {
            std::cerr << "Benchmark error: no trades executed\n";
        }

        return {
            "Partial fill + GTC rest",
            ITERATIONS,
            elapsed,
            static_cast<double>(ITERATIONS) / elapsed,
            (elapsed * 1'000'000'000.0) /
                static_cast<double>(ITERATIONS)};
    }
}

int main()
{
    std::cout << "\n";
    std::cout << "Trading Engine - Phase 1.15 Performance Benchmark\n";
    std::cout << "===================================================\n";
    std::cout << "Iterations: " << ITERATIONS << "\n";
    std::cout << "\n";

    std::cout << std::left
              << std::setw(42) << "Benchmark"
              << std::right
              << std::setw(12) << "Ops"
              << std::setw(18) << "Seconds"
              << std::setw(20) << "Ops/sec"
              << std::setw(20) << "ns/op"
              << '\n';

    std::cout << std::string(112, '-') << '\n';

    print_result(benchmark_single_level());
    print_result(benchmark_multi_level());
    print_result(benchmark_partial_fill_and_rest());

    std::cout << "\nBenchmark complete.\n";

    return 0;
}
