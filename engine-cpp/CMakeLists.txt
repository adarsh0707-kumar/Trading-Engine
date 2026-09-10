cmake_minimum_required(VERSION 3.16)

project(engine-cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_compile_options(
    -Wall
    -Wextra
    -Wpedantic
)

option(
    ENABLE_SANITIZERS
    "Build with AddressSanitizer/UndefinedBehaviorSanitizer"
    OFF
)

if(ENABLE_SANITIZERS)

    add_compile_options(
        -fsanitize=address,undefined
        -g
        -O0
    )

    add_link_options(
        -fsanitize=address,undefined
    )

endif()

include_directories(include)

# ============================================================
# Core Library
# ============================================================

add_library(
    engine_core

    src/orderbook/Order.cpp
    src/orderbook/PriceLevel.cpp
    src/orderbook/OrderBook.cpp
    src/orderbook/Trade.cpp
    src/orderbook/BookSnapshot.cpp

    src/matching/MatchingEngine.cpp

    src/market/Tick.cpp
    src/market/MarketData.cpp
    src/market/MockMarketGenerator.cpp

    src/network/Protocol.cpp
    src/network/ClientConnection.cpp
    src/network/SocketServer.cpp

    src/serialization/Message.cpp
    src/serialization/JsonSerializer.cpp
)

# ============================================================
# Testing
# ============================================================

enable_testing()

# -------------------------
# Order tests
# -------------------------

add_executable(
    test_order
    tests/unit/test_order.cpp
)

target_link_libraries(
    test_order
    PRIVATE
    engine_core
)

add_test(
    NAME test_order
    COMMAND test_order
)

# -------------------------
# PriceLevel tests
# -------------------------

add_executable(
    test_price_level
    tests/unit/test_price_level.cpp
)

target_link_libraries(
    test_price_level
    PRIVATE
    engine_core
)

add_test(
    NAME test_price_level
    COMMAND test_price_level
)

# -------------------------
# OrderBook tests
# -------------------------

add_executable(
    test_orderbook
    tests/unit/test_orderbook.cpp
)

target_link_libraries(
    test_orderbook
    PRIVATE
    engine_core
)

add_test(
    NAME test_orderbook
    COMMAND test_orderbook
)

# -------------------------
# Matching engine tests
# -------------------------

add_executable(
    test_matching_engine
    tests/unit/test_matching_engine.cpp
)

target_link_libraries(
    test_matching_engine
    PRIVATE
    engine_core
)

add_test(
    NAME test_matching_engine
    COMMAND test_matching_engine
)

# -------------------------
# Book snapshot tests
# -------------------------

add_executable(
    test_book_snapshot
    tests/unit/test_book_snapshot.cpp
)

target_link_libraries(
    test_book_snapshot
    PRIVATE
    engine_core
)

add_test(
    NAME test_book_snapshot
    COMMAND test_book_snapshot
)

# -------------------------
# Order cancellation tests
# -------------------------

add_executable(
    test_order_cancellation
    tests/unit/test_order_cancellation.cpp
)

target_link_libraries(
    test_order_cancellation
    PRIVATE
    engine_core
)

add_test(
    NAME test_order_cancellation
    COMMAND test_order_cancellation
)

# -------------------------
# OrderBook cancellation tests
# -------------------------

add_executable(
    test_orderbook_cancellation
    tests/unit/test_orderbook_cancellation.cpp
)

target_link_libraries(
    test_orderbook_cancellation
    PRIVATE
    engine_core
)

add_test(
    NAME test_orderbook_cancellation
    COMMAND test_orderbook_cancellation
)

# -------------------------
# Market generator tests
# -------------------------

add_executable(
    test_market_generator
    tests/unit/test_market_generator.cpp
)

target_link_libraries(
    test_market_generator
    PRIVATE
    engine_core
)

add_test(
    NAME test_market_generator
    COMMAND test_market_generator
)

# -------------------------
# Market pipeline integration tests
# -------------------------

add_executable(
    test_market_pipeline
    tests/integration/test_market_pipeline.cpp
)

target_link_libraries(
    test_market_pipeline
    PRIVATE
    engine_core
)

add_test(
    NAME test_market_pipeline
    COMMAND test_market_pipeline
)


# Phase 1.15 - Performance Benchmark
add_executable(benchmark_matching_engine
    tests/performance/benchmark_matching_engine.cpp
)

target_link_libraries(benchmark_matching_engine
    PRIVATE engine_core
)

# -------------------------
# Serialization unit tests (Phase 2.1)
# -------------------------

add_executable(
    test_serialization
    tests/unit/test_serialization.cpp
)

target_link_libraries(
    test_serialization
    PRIVATE
    engine_core
)

add_test(
    NAME test_serialization
    COMMAND test_serialization
)

# -------------------------
# Engine network integration tests (Phase 2.1)
# -------------------------

add_executable(
    test_engine_network
    tests/integration/test_engine_network.cpp
)

target_link_libraries(
    test_engine_network
    PRIVATE
    engine_core
)

add_test(
    NAME test_engine_network
    COMMAND test_engine_network
)

# ============================================================
# Phase 2.2 - Engine Runtime and Event Publishing
# ============================================================

target_sources(engine_core PRIVATE
    src/utils/Time.cpp
    src/logging/Logger.cpp
    src/engine/EngineConfig.cpp
    src/engine/EngineState.cpp
    src/engine/Engine.cpp
)

add_executable(
    engine
    src/main.cpp
)

target_link_libraries(
    engine
    PRIVATE
    engine_core
)


add_executable(
    test_engine_event_publishing
    tests/integration/test_engine_event_publishing.cpp
)

target_link_libraries(
    test_engine_event_publishing
    PRIVATE
    engine_core
)

add_test(
    NAME test_engine_event_publishing
    COMMAND test_engine_event_publishing
)

