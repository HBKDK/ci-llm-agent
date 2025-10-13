#!/bin/bash

# Rust 바이너리 다운로드 스크립트
set -e

echo "🚀 Rust 바이너리 다운로드 중..."

# 다운로드 디렉토리 생성
mkdir -p rust-installer

# Rust 설치 스크립트 다운로드
echo "📥 Rust 설치 스크립트 다운로드..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o rust-installer/rustup-init

# 실행 권한 부여
chmod +x rust-installer/rustup-init

echo "✅ Rust 바이너리 다운로드 완료!"
echo "📁 위치: ./rust-installer/rustup-init"
