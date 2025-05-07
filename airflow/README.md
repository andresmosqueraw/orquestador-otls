## 🧪 Pruebas

### Opción A: Ejecutar pruebas localmente (sin Docker)

1. Crear entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecutar pruebas:

```bash
python3 -m unittest -b tests.test_utils
# o todas
coverage run -m unittest discover -s tests -t .
```

4. Reporte de cobertura:

```bash
coverage report -m
coverage xml
coverage html
```

---

### Opción B: Ejecutar pruebas con Docker

1. Levantar servicios:

```bash
docker compose up -d
```

2. Ejecutar pruebas:

```bash
docker compose run --rm test-runner
```