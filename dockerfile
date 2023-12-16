FROM ghcr.io/coqui-ai/tts
LABEL Maintainer="AceMouse"
RUN apt-get update &&\
    apt-get upgrade -y &&\
    apt-get install -y wget bzip2 libxtst6 libgtk-3-0 libx11-xcb-dev libdbus-glib-1-2 libxt6 libpci-dev curl &&\
    apt-get install -y ffmpeg espeak 

RUN GECKOVERSION='0.33.0' &&\
    wget https://github.com/mozilla/geckodriver/releases/download/v${GECKOVERSION}/geckodriver-v${GECKOVERSION}-linux64.tar.gz &&\
    tar -zxf geckodriver-v${GECKOVERSION}-linux64.tar.gz -C /usr/local/bin &&\
    chmod +x /usr/local/bin/geckodriver &&\
    rm geckodriver-v${GECKOVERSION}-linux64.tar.gz

RUN FIREFOX_SETUP=firefox-setup.tar.bz2 && \
    apt-get purge firefox && \
    wget -O $FIREFOX_SETUP "https://download.mozilla.org/?product=firefox-latest&os=linux64" && \
    tar xjf $FIREFOX_SETUP -C /opt/ && \
    ln -s /opt/firefox/firefox /usr/bin/firefox && \
    rm $FIREFOX_SETUP

WORKDIR /playa
COPY requirements.txt ./
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt 
COPY edit.py ./
COPY player.py ./
COPY stats.py ./
COPY synth.py ./
