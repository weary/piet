cmake_minimum_required (VERSION 2.8)

project(pietbot)

find_package(Boost COMPONENTS system REQUIRED)
find_package(PythonLibs 2.7.5 EXACT REQUIRED)
find_package(OpenSSL)
find_library(SQLITE3 NAMES sqlite3)
find_package(Threads)

add_definitions(-Wall)
add_definitions(-std=gnu++0x)
add_definitions(-march=native)
add_definitions(-pthread)

include_directories(${PYTHON_INCLUDE_DIRS})

add_executable(pietbot
	bot.cpp
	feedback.cpp
	main.cpp
	piet_db.cpp
	piet_py_handler.cpp
	privmsg_and_log.cpp
	sender.cpp
	pietconnection.cpp
	)
target_link_libraries(pietbot 
	${PYTHON_LIBRARIES}
	${SQLITE3}
	${Boost_SYSTEM_LIBRARY}
	${OPENSSL_LIBRARIES}
	${CMAKE_THREAD_LIBS_INIT}
	)
