    @echo off
   set PYTHONPATH=%CD%
   poetry run pytest --cov=app tests