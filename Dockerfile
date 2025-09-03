FROM continuumio/miniconda3

RUN conda create -y -n mfa -c conda-forge python=3.9 montreal-forced-aligner=2.2.17 ffmpeg cmake make pkg-config libsndfile

RUN conda create -y -n app -c conda-forge \
    python=3.9 \
    flask gunicorn gtts pandas praatio praat-parselmouth

ENV PATH /opt/conda/envs/app/bin:$PATH

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]



# FROM continuumio/miniconda3:latest

# WORKDIR /app

# COPY . /app

# RUN conda create -y -n mfa python=3.9
# RUN conda install -y -n mfa -c conda-forge \
#     montreal-forced-aligner \
#     ffmpeg \
#     cmake \
#     make \
#     pkg-config \
#     sentencepiece \
#     libsndfile
# RUN conda run -n mfa pip install \
#     "numpy<1.23" "scipy<1.11" "numba<0.67" "librosa<0.11"\
#     flask gunicorn gtts pandas \
#     praatio praat-parselmouth

# EXPOSE 10000

# ENV PATH /opt/conda/envs/mfa/bin:$PATH

# CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]














