# FLlib

FLlib는 간단하게 원하는 연합 학습을 구현하도록 도와주는 강력한 프레임워크입니다.
모델 처리를 위해 널리 사용되는 텐서플로우를 사용하며, 연합 학습 통신은 C/C++로 구현된 저수준 통신을 사용합니다.

※ FLlib를 사용하기 위해서는 C/C++ build 도구와 텐서플로우 환경이 필요합니다.

<br/>

## build
make를 통해 FLlib에 필요한 공유 라이브러리들을 빌드합니다.

```
$> make
```

성공적으로 수행되었다면 통신용 라이브러리 `module/libc_server.so` 와 `module/libc_client.so` 가 생성됩니다.
build에 실패한 경우 release에 있는 `module/libc_server.so`, `module/libc_client.so`를 받아 사용할 수 있지만 작업이 제대로 수행되는 것을 보장할 수 없습니다.

<br/>

## example

FLlib를 사용하기 위해서 필요한 것은 module 파일들과 FLlib.py입니다. client.py와 server.py는 예시 코드입니다.

예시 서버는 아래 명령어로 실행될 수 있습니다.
```
$> python3 server.py
```

예시 클라이언트는 아래 명령어로 실행될 수 있습니다.
```
$> python3 client.py
```

<br/>

## usage

연합 학습 서버와 클라이언트는 FLlib의 클래스를 상속받아 구현할 수 있습니다. 예시 코드 `server.py`와 `client.py`를 예시로 설명합니다.

```
Child < Parent

MNISTModel (in server.py) < FLModel
MNISTModel (in client.py) < FLModel
MNISTServer < FLServer
MNISTClient < FLClient
```

FLlib 내의 클래스를 상속받아 내부 함수를 적절하게 수정하는 것으로 원하는 연합 학습을 구성할 수 있습니다.

아래는 클래스 FLServer가 가지고 있는 함수의 설명입니다.

```
FLServer

__init__ 초기화를 위해 반드시 호출되어야 합니다.

```
