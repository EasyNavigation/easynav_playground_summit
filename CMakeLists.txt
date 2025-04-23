cmake_minimum_required(VERSION 3.20)
project(easynav_playground_summit)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch
        DESTINATION share/${PROJECT_NAME})

ament_package()