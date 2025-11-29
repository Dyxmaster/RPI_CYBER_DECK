docker run -d \
  --name my-dashboardv-3 \
  --restart always \
  --network host \
  --pid host \
  --privileged \
  -v /home/pi/Desktop/RPI_CYBER_DECK:/app \
  -v /home/pi/.vscode-server:/root/.vscode-server \
  -v /home/pi/.vscode:/root/.vscode \
  -v /var/run/docker.sock:/var/run/docker.sock \
  rpi-dashboard:v2