# FLlib

FLlib is a powerful framework that makes it simple to implement the federated learning you want.
The framework uses TensorFlow used widely for model processing, and low-level communication implemented in C/C++ for federated learning weights.

※ C/C++ build tools and Tensorflow environment are required to use FLlib framework.

<br/>

## build

Build the shared libraries required by FLlib through make.

```
$> make
```

Communication libraries, `module/libc_server.so` and `module/libc_client.so` are created if the build succeeds
In an environment where build is not possible, you can download and use `module/libc_server.so` and `module/libc_client.so` in the Release package, but normal operation cannot be guaranteed.

<br/>

## example

FLlib framework consists of files in `module` folder and `FLlib.py`. `client.py` and `server.py` are example codes.

The example server can be run with the command below.
```
$> python3 server.py
```

The example client can be run with the command below.
```
$> python3 client.py
```

<br/>

## usage

Federated learning server and client can be implemented by inheriting classes from FLlib.

```
Child < Parent

MNISTModel (in server.py) < FLModel
MNISTModel (in client.py) < FLModel
MNISTServer < FLServer
MNISTClient < FLClient
```

You can configure the federated learning you want by inheriting the class in FLlib and modifying the inherited function appropriately.

