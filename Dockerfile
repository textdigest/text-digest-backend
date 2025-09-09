FROM public.ecr.aws/lambda/python:3.13

COPY ./src ./src

RUN pip install -r ./requirements.txt

CMD [ "src.main.handler" ]