FROM continuumio/miniconda3:latest

WORKDIR /app

COPY . /app

RUN conda create -y -n mfa python=3.9 \
    && conda install -y -n mfa -c conda-forge montreal-forced-aligner ffmpeg cmake make pkg-config sentencepiece \
    && conda run -n mfa pip install flask gunicorn gtts pandas

EXPOSE 10000

ENV PATH /opt/conda/envs/mfa/bin:$PATH

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
