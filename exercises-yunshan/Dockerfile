FROM ubuntu:24.04

RUN apt-get update\
 && apt-get install -y nasm gcc expect build-essential make python3 python3-pip gdb git radare2

RUN pip install pycryptodomex pyzipper --break-system-packages

WORKDIR /root
CMD ["bash"]
