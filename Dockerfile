FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg wget yt-dlp
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY convertmain.py .
CMD ["python", "convertmain.py"]
