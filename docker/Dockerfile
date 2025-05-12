# Use the official Python image with full system tools
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNSUPPORTED=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies including CAN tools and udev
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    can-utils \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libpcap0.8-dev \
    libsdl2-net-dev \
    udev \
    usbutils \
    iproute2 \
    net-tools \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create the target directory for the script
RUN mkdir -p /usr/local/bin

# Copy the CANable setup script (needed for entrypoint)
COPY --chmod=755 scripts/setup_canable.sh /usr/local/bin/setup_canable

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create udev rules for CANable
RUN echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1d50", ATTRS{idProduct}=="606f", MODE="0666"' > /etc/udev/rules.d/75-canable.rules && \
    echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="1d50", ATTRS{idProduct}=="606f", MODE="0666"' >> /etc/udev/rules.d/75-canable.rules

# Expose ports for NiceGUI and MeshCat
EXPOSE 8080
EXPOSE 7000

# Set up entrypoint to handle USB device permissions
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["python", "src/main.py"]
