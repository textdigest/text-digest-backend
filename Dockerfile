FROM public.ecr.aws/lambda/python:3.13

COPY ./pyproject.toml ./
COPY ./src ./src

RUN pip install .

CMD [ "src.main.handler" ]