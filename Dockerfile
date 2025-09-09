FROM public.ecr.aws/lambda/python:3.13

COPY ./requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

COPY ./src ./src

CMD [ "src.main.handler" ]