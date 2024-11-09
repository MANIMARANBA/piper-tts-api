# Stage 1: Build Piper
FROM debian:bullseye AS build

# Install necessary dependencies
RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
        build-essential \
        cmake \
        ca-certificates \
        curl \
        pkg-config \
        git \
        python3 \
        python3-pip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Clone Piper repository
RUN git clone https://github.com/rhasspy/piper.git . && \
    git checkout master

# Build Piper
RUN cmake -Bbuild -DCMAKE_INSTALL_PREFIX=install && \
    cmake --build build --config Release && \
    cmake --install build

# Download model
RUN mkdir -p models && \
    cd models && \
    curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/kathleen/low/en_US-kathleen-low.onnx" \
        -o en_US-kathleen-low.onnx && \
    curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/kathleen/low/en_US-kathleen-low.onnx.json" \
        -o en_US-kathleen-low.onnx.json

# Stage 2: Runtime
FROM debian:bullseye

# Install runtime dependencies
RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
        python3 \
        python3-pip \
        espeak-ng \
        espeak-ng-data \
        libespeak-ng1 \
        libgomp1 \
        ca-certificates \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Download requirements.txt and install Python packages
RUN curl -L "https://raw.githubusercontent.com/MANIMARANBA/piper-tts-api/main/requirements.txt" -o /tmp/requirements.txt && \
    pip3 install -r /tmp/requirements.txt

WORKDIR /app

# Copy files from build stage
COPY --from=build /build/install /app/piper
COPY --from=build /build/models /app/models

# Download API service file
RUN curl -L "https://raw.githubusercontent.com/MANIMARANBA/piper-tts-api/main/api_service.py" -o api_service.py && \
    chmod +x api_service.py

# Create output directory with proper permissions
RUN mkdir -p output && \
    chmod 777 output && \
    chown -R nobody:nogroup /app

# Set environment variables
ENV PATH="/app/piper/bin:${PATH}"
ENV LD_LIBRARY_PATH="/app/piper/lib"
ENV ESPEAK_DATA_PATH="/usr/share/espeak-ng-data"

# Switch to non-root user
USER nobody

# Expose API port
EXPOSE 8000

# Start FastAPI server with debug logging
CMD ["uvicorn", "api_service:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]
