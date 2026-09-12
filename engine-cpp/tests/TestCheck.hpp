// Assertion helper for the engine test suite.
//
// Unlike <cassert>, CHECK always evaluates its condition, including in
// builds that define NDEBUG (for example -DCMAKE_BUILD_TYPE=Release).

#pragma once

#include <cstdlib>
#include <iostream>

#define CHECK(condition)                          \
    do                                            \
    {                                             \
        if (!(condition))                         \
        {                                         \
            std::cerr                             \
                << "CHECK failed: " << #condition \
                << "\n  at " << __FILE__          \
                << ":" << __LINE__ << "\n";       \
            std::abort();                         \
        }                                         \
    } while (false)
