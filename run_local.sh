#!/bin/bash

set -e

echo " ✅ Starting  INeuroChat API (local dev)"


# Start Server
uvicorn app.main:app --reload  
