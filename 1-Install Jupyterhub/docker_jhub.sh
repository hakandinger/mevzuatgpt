#!/bin/bash

# JupyterHub Docker Konteyneri Başlatma
docker run -d \
    -p 8000:8000 \
    -v /home/user/my_jupyterhub:/home/jhub/work \
    --name jupyterhub_container \
    jupyter/datascience-notebook

# Conda environment'ı oluşturma
docker exec -it jupyterhub_container bash -c "conda create --name myenv python=3.9"

# Jupyter Notebook için environment ekleme
docker exec -it jupyterhub_container bash -c "conda install -n myenv ipykernel && \
python -m ipykernel install --user --name myenv --display-name 'Python (myenv)'"
