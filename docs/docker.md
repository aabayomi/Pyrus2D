# Running in Docker #

Build the image and run the shell script. Pass the directory to the Dockerfile as an argument

```
./build_image.sh {$DIR}
```

Run the docker image.

```
docker run -v /tmp/.X11-unix:/tmp/.X11-unix:rw -it keepaway
```
