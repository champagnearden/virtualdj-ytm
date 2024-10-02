# CMakeList.txt : CMake project for virtualdj-ytm, include source and define
# project specific logic here.
#
cmake_minimum_required(VERSION 3.10)

# Enable Hot Reload for MSVC compilers if supported.
if(POLICY CMP0141)
  cmake_policy(SET CMP0141 NEW)
  set(CMAKE_MSVC_DEBUG_INFORMATION_FORMAT "$<IF:$<AND:$<C_COMPILER_ID:MSVC>,$<CXX_COMPILER_ID:MSVC>>,$<$<CONFIG:Debug,RelWithDebInfo>:EditAndContinue>,$<$<CONFIG:Debug,RelWithDebInfo>:ProgramDatabase>>")
endif()

project(virtualdj-ytm)

# Specify C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Use vcpkg toolchain if available (assuming vcpkg is installed and set up)
if(DEFINED ENV{VCPKG_ROOT})
  set(CMAKE_TOOLCHAIN_FILE "$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake" CACHE STRING "Vcpkg toolchain file")
endif()

# Add executable
add_executable(virtualdj-ytm "virtualdj-ytm.cpp" "virtualdj-ytm.h")

# Find CPR and JSON packages installed by vcpkg
find_package(CPR CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)

# Link CPR library to your executable
target_link_libraries(virtualdj-ytm PRIVATE cpr::cpr nlohmann_json::nlohmann_json)

# TODO: Add tests and install targets if needed.
