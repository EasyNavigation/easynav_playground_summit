cmake_minimum_required(VERSION 3.20)
project(easynav_playground_summit)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  launch
  config
  params
  maps
  rviz
  urdf
  meshes
  worlds
  models
  DESTINATION share/${PROJECT_NAME}
)

install(FILES LICENSE LICENSE-BSD DESTINATION share/${PROJECT_NAME})

ament_package()
