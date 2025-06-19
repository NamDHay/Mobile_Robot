#!/bin/bash

# Tên session tmux
SESSION="robot_launcher"

# Tạo session mới (chạy ngầm)
tmux new-session -d -s $SESSION

# Cửa sổ 1: roscore
tmux rename-window -t $SESSION:1 'roscore'
tmux send-keys -t $SESSION:1 'roscore' C-m

# Cửa sổ 2: roslaunch controller bringup
tmux new-window -t $SESSION:2 -n 'bringup'
tmux send-keys -t $SESSION:2 'sleep 2 && roslaunch controller bringup.launch' C-m

# Cửa sổ 3: roslaunch controller nav.launch
tmux new-window -t $SESSION:3 -n 'nav'
tmux send-keys -t $SESSION:3 '
sleep 2
if [ -f "$HOME/.ros/rtabmap.db" ]; then
  echo "Found rtabmap.db — Launching with localization"
  roslaunch controller nav.launch localization:=true
else
  echo "rtabmap.db not found — Launching with mapping"
  roslaunch controller nav.launch localization:=false
fi
' C-m

# Cửa sổ 4: python3 test_full.py
tmux new-window -t $SESSION:4 -n 'test_script'
tmux send-keys -t $SESSION:4 'sleep 6 && python3 ~/test_full.py' C-m

# Gắn tmux session vào terminal
tmux attach-session -t $SESSION
