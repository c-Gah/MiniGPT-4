#!/bin/bash

# Clone the GitHub repo "https://github.com/c-Gah/MiniGPT-4" into /usr/local/minigpt4
git clone https://github.com/c-Gah/MiniGPT-4 /usr/local/minigpt4

# Create a group named "minigpt4_g"
sudo groupadd minigpt4_g

# Create a user named "minigpt4_u" with no login shell and belonging to the "minigpt4_g" group
sudo useradd -r -s /bin/false -g minigpt4_g minigpt4_u

# Set ownership of /usr/local/minigpt4/ to the "minigpt4_u" user and group
sudo chown -R minigpt4_u:minigpt4_g /usr/local/minigpt4/

# Set permissions on /home/minigpt4_u to 755 recursively
# sudo chmod 755 -R /home/minigpt4_u

# Set permissions on /home/minigpt4_u to 775 recursively
sudo chmod 775 -R /usr/local/minigpt4

# Install nano text editor
sudo apt-get update
sudo apt-get install -y nano
sudo apt-get install -y build-essential
sudo apt-get install -y libgl1-mesa-glx


# Create the /usr/local/minigpt4/llama directory
sudo mkdir -p /usr/local/minigpt4/llama/7b
sudo mkdir -p /usr/local/minigpt4/llama/checkpoint

# Download the llama-7b-minigpt.tar file from Google Cloud Storage using wget
file_name="llama-7b-minigpt.tar"
output_file="/usr/local/minigpt4/llama/7b/$file_name"
sudo wget https://storage.googleapis.com/poc_llama/llama-7b-minigpt.tar -O "$output_file"

# Extract the contents of the llama-7b-minigpt.tar file to /usr/local/minigpt4/llama/7b
sudo tar -xf "$output_file" -C /usr/local/minigpt4/llama/7b

# Download the llama-7b-minigpt.tar file from Google Cloud Storage using wget
file_name="prerained_minigpt4_7b.pth"
output_file="/usr/local/minigpt4/llama/checkpoint/$file_name"
sudo wget https://storage.googleapis.com/poc_llama/prerained_minigpt4_7b.pth -O "$output_file"

# file_name="Anaconda3-2023.03-1-Linux-x86_64.sh"
# output_file="/usr/local/$file_name"
# sudo wget https://repo.anaconda.com/archive/Anaconda3-2023.03-1-Linux-x86_64.sh -O "$output_file"
# bash "/usr/local/$file_name" -b -p /usr/local/anaconda3
# sudo rm "/usr/local/$file_name"

file_name="miniconda.sh"
output_file="/usr/local/$file_name"
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O "$output_file"
bash "$output_file" -b -p /usr/local/miniconda
sudo rm "/usr/local/$file_name"

export PATH="/usr/local/miniconda/bin:/usr/local/miniconda/condabin:$PATH"

conda env create -f /usr/local/minigpt4/environment.yml
conda init bash
conda activate minigpt4

# Create the minigpt.service file with the updated service contents
cat <<EOF | sudo tee /etc/systemd/system/minigpt.service
[Unit]
Description=MiniGPT4
After=network.target

[Service]
ExecStart=/opt/conda/envs/minigpt4/bin/uvicorn main:app --host 0.0.0.0 --port 8000
WorkingDirectory=/home/minigpt4_u/
User=minigpt4_u
Group=minigpt4_g
Restart=on-failure
RestartSec=360s

[Install]
WantedBy=multi-user.target
EOF

# Enable the minigpt service to start on boot
# sudo systemctl enable minigpt.service
sudo systemctl enable minigpt

# Start the minigpt service
# sudo systemctl start minigpt.service
sudo systemctl start minigpt
