FROM python:3
WORKDIR /usr/src/search
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT ["./make_search.sh"]
CMD []
