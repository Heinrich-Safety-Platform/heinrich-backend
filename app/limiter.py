from slowapi import Limiter
from slowapi.util import get_remote_address

# config_filename을 명시해 slowapi가 .env를 자동 탐색하지 않도록 방지
# (starlette.Config가 인코딩 미지정으로 .env를 열어 cp949/UTF-8 충돌 발생)
limiter = Limiter(key_func=get_remote_address, config_filename="slowapi.env")
