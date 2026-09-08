cmake_minimum_required(VERSION 3.16)

project(engine-cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_compile_options(-Wall -Wextra -Wpedantic)

# Usage:
# cmake -S . -B build -DENABLE_SANITIZERS=ON
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

# Core library: pure business logic, no networking, no I/O.
add_library(engine_core
    src/orderbook/Order.cpp
    src/orderbook/PriceLevel.cpp
)

# ------------------------------------------------------------
# Testing
# ------------------------------------------------------------

enable_testing()

# Order tests
add_executable(test_order
    tests/unit/test_order.cpp
)

target_link_libraries(test_order
    PRIVATE engine_core
)

add_test(
    NAME test_order
    COMMAND test_order
)

# Price level tests
add_executable(test_price_level
    tests/unit/test_price_level.cpp
)

target_link_libraries(test_price_level
    PRIVATE engine_core
)

add_test(
    NAME test_price_level
    COMMAND test_price_level
)