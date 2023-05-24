#!/bin/bash

# Clone the GitHub repo "https://github.com/c-Gah/MiniGPT-4" into /usr/local/minigpt4
git clone https://github.com/c-Gah/MiniGPT-4 /usr/local/minigpt4

# Create a group named "minigpt"
sudo groupadd minigpt

# Create a user named "minigpt" with no login shell and belonging to the "minigpt" group
sudo useradd -r -s /bin/false -g minigpt minigpt

# Set ownership of /usr/local/minigpt/ to the "minigpt" user and group
sudo chown -R minigpt:minigpt /usr/local/minigpt/

# Set permissions on /home/minigpt to 755 recursively
sudo chmod 755 -R /home/minigpt

# Set permissions on /home/minigpt to 775 recursively
sudo chmod 775 -R /home/minigpt

# Install nano text editor
sudo apt-get update
sudo apt-get install -y nano

# Install uvicorn
sudo apt-get install -y uvicorn

# Install gdown using pip3
sudo pip3 install gdown

# Download the llama-7b-minigpt.tar file from Google Drive using gdown
file_id="1vbpJ9cRxZPTQMMs9N6UAE2ygBP85ct3U"
file_name="llama-7b-minigpt.tar"
output_file="/usr/local/minigpt4/llama/$file_name"
gdown --id "$file_id" --output "$output_file"

# Create the /usr/local/minigpt4/llama directory
sudo mkdir -p /usr/local/minigpt4/llama

# Extract the contents of the llama-7b-minigpt.tar file to /usr/local/minigpt4/llama
sudo tar -xf "$output_file" -C /usr/local/minigpt4/llama

# Create the minigpt.service file with the updated service contents
cat <<EOF | sudo tee /etc/systemd/system/minigpt.service
[Unit]
Description=MiniGPT4
After=network.target

[Service]
ExecStart=/opt/conda/envs/minigpt4/bin/uvicorn main:app --host 0.0.0.0 --port 8000
WorkingDirectory=/home/minigpt/
User=minigpt
Group=minigpt
Restart=on-failure
RestartSec=360s

[Install]
WantedBy=multi-user.target
EOF

# Enable the minigpt service to start on boot
# sudo systemctl enable minigpt.service
sudo service minigpt enable

# Start the minigpt service
# sudo systemctl start minigpt.service
sudo service minigpt start
