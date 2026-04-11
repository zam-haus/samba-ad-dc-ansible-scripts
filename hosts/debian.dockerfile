FROM docker.io/debian:trixie
RUN apt update && apt install locales openssh-server sudo python3 -y
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8
RUN useradd -rm -d /home/ansible -s /bin/bash -g root -G sudo ansible
RUN  echo 'ansible:logmein' | chpasswd
# This keeps the host key the same across container restarts
RUN service ssh start
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
WORKDIR /home/ansible/
EXPOSE 22
CMD ["/usr/sbin/sshd","-D"]