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

    src/matching/MatchingEngine.cpp

    src/market/Tick.cpp
    src/market/MarketData.cpp
    src/market/MockMarketGenerator.cpp
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
