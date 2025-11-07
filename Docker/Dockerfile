FROM python:3.9-slim

WORKDIR /toolwindow_analysis

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME /toolwindow_analysis

CMD ["python", "Python/toolwindow_analysis.py"]