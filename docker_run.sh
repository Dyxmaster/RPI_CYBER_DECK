docker run -d \
  --name my-dashboardv-1227 \
  --restart always \
  --pid host \
  --privileged \
  --network host \
  -v /home/pi/Desktop/RPI_CYBER_DECK:/app \
  -v /home/pi/.vscode-server:/root/.vscode-server \
  -v /home/pi/.vscode:/root/.vscode \
  -v /var/run/docker.sock:/var/run/docker.sock \
  rpi-dashboard:1227

# 打包指令
docker build -t rpi-dashboard:1130 .
docker build -t rpi-dashboard:1202 .
docker build -t rpi-dashboard:1227 .