# --- STAGE 1: Builder (Compiles C++) ---
FROM python:3.10-slim as builder

# 1. Install System Compilers
RUN apt-get update && apt-get install -y \
    cmake \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Pybind11
RUN pip install --no-cache-dir pybind11

# 3. Copy C++ Source
WORKDIR /build
COPY cpp_engine/ ./cpp_engine/

# 4. Clean previous builds (Vital for preventing Mac vs Linux conflicts)
RUN rm -rf cpp_engine/build && mkdir -p cpp_engine/build

# 5. Compile for Linux
WORKDIR /build/cpp_engine/build

# We explicitly calculate the pybind11 directory using Python and pass it to CMake
RUN cmake .. \
    -DPYTHON_EXECUTABLE=$(which python3) \
    -Dpybind11_DIR=$(python3 -m pybind11 --cmakedir) \
    && make

# --- STAGE 2: Runner (Runs Python) ---
FROM python:3.10-slim

WORKDIR /app

# Install Python Deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend Code
COPY backend/ .

# Copy Compiled C++ Engine from Stage 1
COPY --from=builder /build/cpp_engine/build/recommender*.so ./

# Copy Frontend Code
COPY frontend/ ./frontend/

# Expose Port
EXPOSE 8000

# Start App
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]