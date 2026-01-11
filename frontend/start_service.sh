#!/bin/bash
# Wrapper for Systemd to load NVM/User environment
# This ensures we use the Node version installed by the user (v20+)
# instead of the system default (v18)

# Load NVM for ec2-user
export NVM_DIR="/home/ec2-user/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Explicitly add NVM bin to PATH just in case
export PATH="/home/ec2-user/.nvm/versions/node/v20.*/bin:$PATH"

# Navigate to app dir
cd /home/ec2-user/cbse-AI-study-app/frontend

# Run production server
# 'exec' replaces the shell with the process, keeping signal handling correct
exec npm start -- -H 0.0.0.0 -p 3000
