import inotify.adapters
import logging
import os
import subprocess
import time

# parse incoming env vars

rclone_path = os.environ.get("RCLONE_PATH")
rclone_remote = os.environ.get("RCLONE_REMOTE")
source_dir = os.environ.get("RCLONE_SOURCE")

try:
    sync_maxwait = os.environ.get("SYNC_MAXWAIT")
    sync_maxwait = int(sync_maxwait) if sync_maxwait != None else 5 * 60
except:
    logging.warning("maxwait was not parsable, using 5minutes")
    sync_maxwait = 5 * 60

try:
    sync_minwait = os.environ.get("SYNC_MINWAIT")
    sync_minwait = int(sync_minwait) if sync_minwait != None else 5
except:
    logging.warning("minwait was not parsable, using 5s")
    sync_minwait = 5 * 60

logging.basicConfig(level=logging.INFO)
logging.info("umt rclone sync:")
logging.info("  source path: %s", source_dir)
logging.info("  remote path: %s", rclone_remote)
logging.info(" sync minwait: %d", sync_minwait)
logging.info(" sync maxwait: %d", sync_maxwait)

# wait for rclone to have the given remote before starting
while True:
    try:
        subprocess.run([rclone_path, "about", rclone_remote], check=True)
        break  # exit code 0
    except:
        logging.error("rclone remote %s unavailable; waiting...", rclone_remote)
        time.sleep(10)

# run initial sync
# ignore errors, we'll just fall into the loop at that point
subprocess.run([rclone_path, "copy", "-v", source_dir, rclone_remote])

# watch the source path with inotify, and copy on changes
# only watch file create - modification will be picked up in maxwait
mask = inotify.constants.IN_CREATE
notifier = inotify.adapters.InotifyTree(
    source_dir, mask=mask, block_duration_s=sync_minwait
)

# don't use the gen as a loop, rather pull everything, so we collapse multiple changes
nextev = time.perf_counter() + sync_maxwait
while True:
    events = notifier.event_gen(
        yield_nones=False, timeout_s=sync_minwait
    )  # 1s = debounce time
    events = list(events)

    if len(events) > 0:  # events came in
        logging.info("changes detected: copying", str(events))
        logging.debug(str(events))

        # in the future, use the path and filename params to skip syncs
        subprocess.run([rclone_path, "copy", "-v", source_dir, rclone_remote])
        nextev = time.perf_counter() + sync_maxwait

    elif time.perf_counter() >= nextev:  # no events, and timeout
        logging.info("no changes detected after %d seconds; scanning...", sync_maxwait)

        # in the future, use the path and filename params to skip syncs
        subprocess.run([rclone_path, "copy", "-v", source_dir, rclone_remote])
        nextev = time.perf_counter() + sync_maxwait

    else:
        logging.debug(
            "no changes detected, waiting for %f (current %f)...",
            nextev,
            time.perf_counter(),
        )
