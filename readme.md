# rclone-sync

simple hacky inotify-based driver loop for the `rclone` application to sync a 
directory to cloud services on change.

## Requirements

* docker
* `rclone` installed locally to round-trip authentication

## `ENV` Vars

* `RCLONE_SOURCE` 
  the source directory (in-container!) to copy to cloud storage
* `RCLONE_REMOTE` 
  the rclone remote config to be copied to (`remote-name:folder-name`, eg. `umtsync:upload-folder`)
* `SYNC_MINTIME` (default 1s) 
  the minimum amount of time to wait for events - if many events are detected within mintime, only one sync will occur.
* `SYNC_MAXTIME` (default 5m)
  the maximum amount of time to wait for events - if no events are detected within this time, sync anyway.

## Use

1. build the docker image (or pull from somewhere)
1. run the service, with env vars for control:

```
$ docker build .
...
...
...
Successfully built 3eeb70aa2e20

$ docker run -it --rm \
  -v ./uploads:/mnt/umtsync \             # mount the 'uploads' directory to /mnt/umtsync
  -eRCLONE_SOURCE=/mnt/umtsync \          # "local" to the container source for uploads (folder mounted above)
  -eRCLONE_REMOTE=umtsync:umt-sync \      # "remote-name:folder-name", where remote name is setup later
  -eSYNC_MINWAIT=1 \                      # minimum wait time (debouncing)
  -eSYNC_MAXWAIT=30 \                     # maximum wait time (scan for possible missed events)
  3eeb70aa2e20
```

1. leave that running; you'll get output explaining that the remote isn't configured.
1. in another terminal:
  - find the running image
  - exec in and configure `rclone`
    - use `umtsync` (or whatever you named your remote)
    - say `N` when being offered to launch a browser for auth, then follow instructions
  
```
$ docker ps
CONTAINER ID   IMAGE          COMMAND                  CREATED         STATUS         PORTS     NAMES
9671d9a478d2   3eeb70aa2e20   "python -u sync-driv…"   9 seconds ago   Up 8 seconds             cool_bell

# docker exec -it 9671d9a478d2 bash
$ rclone config
```
