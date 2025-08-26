FROM public.ecr.aws/lambda/python:3.13

COPY ./src ./src

RUN pip install -r ./src/requirements.txt

CMD [ "src.main.handler" ]