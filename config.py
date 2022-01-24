from pydantic import BaseSettings, PostgresDsn


class Settings(BaseSettings):
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    pg_dsn: PostgresDsn = 'postgresql://postgres:brutehorse@localhost/postgres'
    server_cert_path: str = 'server.crt'
    server_key_path: str = 'server.key'
    server_listening_interface: str = '[::]:50051'


def setup(settings: Settings):
    import models

    models.configure(settings.pg_dsn)
