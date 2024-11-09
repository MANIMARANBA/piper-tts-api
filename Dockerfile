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
COPY . .

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
        ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install fastapi uvicorn piper-tts

# Copy files from build stage
COPY --from=build /build/install /app/piper
COPY --from=build /build/models /app/models

WORKDIR /app

# Create output directory
RUN mkdir -p output && chmod 777 output

# Set environment variables
ENV PATH="/app/piper/bin:${PATH}"
ENV LD_LIBRARY_PATH="/app/piper/lib"
ENV ESPEAK_DATA_PATH="/usr/share/espeak-ng-data"

# Expose API port
EXPOSE 8000

# Copy API service file
COPY api_service.py .

# Start FastAPI server
CMD ["uvicorn", "api_service:app", "--host", "0.0.0.0", "--port", "8000"]