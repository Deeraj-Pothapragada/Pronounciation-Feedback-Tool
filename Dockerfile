FROM continuumio/miniconda3

RUN conda create -y -n mfa -c conda-forge python=3.9 montreal-forced-aligner=2.2.17 ffmpeg

RUN conda run -n mfa pip install \
    flask gunicorn gtts pandas \
    praatio praat-parselmouth

WORKDIR /app

COPY . /app

EXPOSE 5000

CMD ["conda", "run", "--no-capture-output", "-n", "mfa", \
     "gunicorn", "-b", "0.0.0.0:5000", "app:app"]



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













