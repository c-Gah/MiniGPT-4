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

# Download the llama-7b-minigpt.tar file from Google Drive
file_id="1vbpJ9cRxZPTQMMs9N6UAE2ygBP85ct3U"
file_name="llama-7b-minigpt.tar"
output_file="/usr/local/minigpt4/llama/$file_name"
temp_dir=$(mktemp -d)
wget --no-check-certificate "https://docs.google.com/uc?export=download&id=$file_id" -O "$temp_dir/$file_name"

# Create the /usr/local/minigpt4/llama directory
sudo mkdir -p /usr/local/minigpt4/llama

# Extract the contents of the llama-7b-minigpt.tar file to /usr/local/minigpt4/llama
sudo tar -xf "$temp_dir/$file_name" -C /usr/local/minigpt4/llama

# Clean up the temporary directory
rm -rf "$temp_dir"

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

sudo systemctl enable minigpt.service
sudo systemctl start minigpt.service