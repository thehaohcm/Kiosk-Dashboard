# Cài đặt dependencies cho Raspbian
sudo apt update
sudo apt install python3-pip python3-dev libasound2-dev portaudio19-dev

# Cài đặt các công cụ volume control
sudo ap install pulseaudio-utils alsa-utils wireplumber

# Cài đặt Python dependencies
pip3 install -r requirements.txt