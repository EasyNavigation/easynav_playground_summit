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

# Map building tools (ros2 run easynav_playground_summit <script>)
install(PROGRAMS
  scripts/map_builder.py
  scripts/map2d_from_pcd.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
