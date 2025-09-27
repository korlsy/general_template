import logging
import importlib

# logging.basicConfig(
#     level=logging.INFO,  # 기본 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
#     format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
# )

# sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

# common.py
def with_task_logging(logger):
    def _decorator(fn):   # 실제 함수를 감싸는 래퍼
        def _wrap(**context):
            try:
                logger.info("작업 시작")
                return fn(**context)
            except Exception as e:
                logger.error("에러 발생", e, exc_info=True)
                raise
            finally:
                logger.info("작업 종료")
        return _wrap
    return _decorator



def check_port(ip, port, timeout=3):
    """
    방화벽 점검
    """
    import socket
    try:
        logging.info("start check_port, host: %s, port : %d", ip, port)
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception as e:
        return False

def ensure_package(package_name: str, version: str = None, install_name: str = None):
    """
    - package_name : import 시 사용할 이름 (예: 'pymysql')
    - version=None : 설치 여부만 확인 후 없으면 최신 설치
    - version 지정 : 해당 버전 없으면 pip install <install_name>==<version>
    - install_name : pip install 시 사용할 패키지명 (PyPI명과 import명이 다를 때)
                     지정하지 않으면 package_name 그대로 사용
                     
    지원기능)
        버전 지정 → ensure_package("requests", "2.31.0")
        버전 미지정 → ensure_package("pytz")
        PyPI명과 import명이 다를 때 → ensure_package("MySQLdb", install_name="mysqlclient")                     
    """
    try:
        pkg = importlib.import_module(package_name)
        installed_version = getattr(pkg, "__version__", None)

        if version:
            if installed_version == version:
                logging.info("%s %s 이미 설치되어 있음", package_name, version)
                return
            else:
                logging.info(
                    "%s 버전이 다름 (현재=%s, 요구=%s) → 재설치",
                    package_name, installed_version, version
                )
        else:
            logging.info("%s 이미 설치되어 있음 (버전=%s)", package_name, installed_version)
            return
    except ImportError:
        logging.info("%s 설치되지 않음 → 설치 진행", package_name)

    # 설치 타겟 문자열 구성
    target = install_name or package_name
    if version:
        target = f"{target}=={version}"

    subprocess.check_call([sys.executable, "-m", "pip", "install", target])


