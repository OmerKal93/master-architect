# This file lives OUTSIDE the intended scan root. If a scan of scan_root/ ever reads this
# file's contents, the symlink-containment defense has failed.
SECRET_OUTSIDE_ROOT = "should never be read by a scan of scan_root/"
