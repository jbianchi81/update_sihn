# Actualiza alturas de mareógrafos SIHN

## Instalación

    python3 -m venv .
    bin/python -m pip install -r requirements.txt
    chmod ugo+x run.py

## Configuración

    cp config/default.json config/config.json
    nano config/config.json # editar variables url y token

## Uso

### Activa el ambiente

    source bin/activate

### Actualiza todas las estaciones

    ./run.py -o tmp/results_sihn.json

### Actualiza una estación

    ./run.py -c SFER -o tmp/results_sihn_sfer.json

### Descarga todas las estaciones sin actualizar

    ./run.py -o tmp/results_sihn.json -t

