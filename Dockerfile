FROM python:3.7

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY common.py .
COPY *_implementation.py ./

EXPOSE 53
CMD python -m socket_implmentation.py