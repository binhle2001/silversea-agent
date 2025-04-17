### Install amd64 emulator
# docker run --privileged --rm tonistiigi/binfmt --install amd64 
### Build docker image
# docker buildx build --platform=linux/amd64 -t tims-ai .
### Run docker container
# docker run --platform=linux/amd64 -p 9000:9000 --name=tims-ai tims-ai
#model arcFace for Face recognition: https://drive.google.com/file/d/1cLIh-n_q_R7yJ-rpLM4n2IbVltxLm5YN/view?usp=sharing
# pull docker image
FROM --platform=linux/amd64 python:3.11-slim-bullseye AS COMPILE-IMAGE
# set work directory
WORKDIR /app
# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# install dependencies
COPY ./requirements.txt ./requirements.txt
RUN pip install --user --upgrade pip
RUN pip3 install --user torch==2.5.1+cu118 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
RUN pip install --disable-pip-version-check --no-compile --user -r ./requirements.txt
FROM --platform=linux/amd64 python:3.11-slim-bullseye AS BUILD-IMAGE
COPY --from=COMPILE-IMAGE /root/.local /root/.local
# set work directory
WORKDIR /app
ENV PATH="/root/.local/bin:$PATH"
# copy project
COPY . .
EXPOSE 8080
CMD uvicorn main:app --host 0.0.0.0 --port 8080