FROM python:3.7

COPY requirements.txt .
COPY *_implementation.py ./
COPY common.py .

RUN pip install -r requirements.txt

EXPOSE 53
CMD python -m open_source_implementation